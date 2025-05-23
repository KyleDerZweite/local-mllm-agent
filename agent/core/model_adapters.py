# agent/core/model_adapters.py
"""
Provides adapters for interacting with different Ollama language models.

This module contains classes like `DeepSeekAdapter` and `LLaVAAdapter` that encapsulate
the logic for sending requests to specific Ollama models (text-based and multimodal)
and processing their responses. They use the base Ollama API URL and model names
defined in `config.py`.
"""

import json
import requests
import base64
from typing import List, Dict, Any, Optional

try:
    from .config import DEEPSEEK_MODEL, LLAVA_MODEL, OLLAMA_API_BASE_URL
except ImportError:
    # Fallback for standalone execution or if config is not found in the expected relative path.
    # This helps in simple testing or if the file is moved/used in a context where relative imports fail.
    print("ModelAdapters: Could not perform relative import of config. Attempting direct import for testing/fallback.")
    try:
        import config # type: ignore # Assumes config.py is in PYTHONPATH or current dir for this case
        DEEPSEEK_MODEL = config.DEEPSEEK_MODEL
        LLAVA_MODEL = config.LLAVA_MODEL
        OLLAMA_API_BASE_URL = config.OLLAMA_API_BASE_URL
    except ImportError:
        print("ModelAdapters: Failed to import config directly. Using hardcoded default values.")
        DEEPSEEK_MODEL = "deepseek-coder:6.7b" 
        LLAVA_MODEL = "llava:7b"
        OLLAMA_API_BASE_URL = "http://localhost:11434/api"

class DeepSeekAdapter:
    """
    Adapter for interacting with a DeepSeek (or similar text-based) model via Ollama.

    This class handles the specifics of making requests to the Ollama API's /generate endpoint
    for text generation tasks.
    """
    def __init__(self, model_name: str = DEEPSEEK_MODEL, base_url: str = OLLAMA_API_BASE_URL):
        """
        Initializes the DeepSeekAdapter.

        Args:
            model_name (str): The name of the DeepSeek model to use (e.g., 'deepseek-coder:6.7b').
                              Defaults to `DEEPSEEK_MODEL` from `config.py`.
            base_url (str): The base URL for the Ollama API.
                            Defaults to `OLLAMA_API_BASE_URL` from `config.py`.
        """
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{self.base_url}/generate" # Ollama's endpoint for direct generation
        print(f"DeepSeekAdapter initialized for model: {self.model_name} at {self.generate_url}")

    def chat(self, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> str:
        """
        Sends a chat request to the DeepSeek model using the /generate endpoint.

        Ollama's /generate endpoint typically expects a single 'prompt' string. This method extracts
        the content from the last message with role 'user' in the `messages` list to use as this prompt.
        For more complex conversational history, the Ollama /chat endpoint might be preferred,
        but /generate is often used for simpler instruction-following or single-turn Q&A.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
                Each dictionary should have 'role' (e.g., 'user', 'system') and 'content' keys.
                Example: `[{"role": "user", "content": "Explain quantum physics."}]`
            options (Optional[Dict[str, Any]]): An optional dictionary of Ollama parameters
                to control generation (e.g., `{"temperature": 0.7, "top_p": 0.9}`).
                These are passed as the 'options' field in the Ollama API request.

        Returns:
            str: The model's response content as a string. Returns an error message string
                 if the request fails or the response is malformed.
        """
        if not messages:
            return "Error: No messages provided to DeepSeekAdapter."

        # Extract the last user message content as the prompt for the /generate endpoint
        prompt = next((m["content"] for m in reversed(messages) if m["role"] == "user"), None)

        if prompt is None:
            return "Error: No user message found in messages to use as a prompt."

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,  # We want the full response at once, not a stream
        }
        if options:
            payload["options"] = options
        
        log_prompt = prompt if len(prompt) < 100 else prompt[:97] + "..."
        # print(f"DeepSeekAdapter: Sending request to {self.generate_url} with model {self.model_name} and prompt: '{log_prompt}'")

        try:
            response = requests.post(self.generate_url, json=payload, timeout=60) # Added timeout
            response.raise_for_status()  # Raise an HTTPError for bad responses (4XX or 5XX)
            response_data = response.json()
            # The actual response content is in the 'response' field for non-streamed /generate
            return response_data.get("response", "Error: 'response' field missing in Ollama output.")
        except requests.exceptions.Timeout as e:
            print(f"DeepSeekAdapter: Timeout error connecting to Ollama at {self.generate_url}: {e}")
            return f"Error: Timeout connecting to Ollama. Details: {e}"
        except requests.exceptions.RequestException as e:
            print(f"DeepSeekAdapter: Error connecting to Ollama at {self.generate_url}: {e}")
            return f"Error: Could not connect to Ollama service. Details: {e}"
        except json.JSONDecodeError:
            print(f"DeepSeekAdapter: Error decoding JSON response from Ollama. Response text: {response.text[:200]}...")
            return f"Error: Could not decode JSON response from Ollama. Response: {response.text}"
        except KeyError:
            # This might happen if 'response' key is missing from a successful JSON parse
            response_content_for_log = response.json() if response else "No response object"
            print(f"DeepSeekAdapter: Unexpected JSON structure from Ollama: {response_content_for_log}")
            return "Error: Unexpected response structure from Ollama."

class LLaVAAdapter:
    """
    Adapter for interacting with a LLaVA (or similar multimodal) model via Ollama.

    This class handles sending requests with images and text prompts to the Ollama API's
    /generate endpoint for multimodal tasks.
    """
    def __init__(self, model_name: str = LLAVA_MODEL, base_url: str = OLLAMA_API_BASE_URL):
        """
        Initializes the LLaVAAdapter.

        Args:
            model_name (str): The name of the LLaVA model to use (e.g., 'llava:7b').
                              Defaults to `LLAVA_MODEL` from `config.py`.
            base_url (str): The base URL for the Ollama API.
                            Defaults to `OLLAMA_API_BASE_URL` from `config.py`.
        """
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{self.base_url}/generate"
        print(f"LLaVAAdapter initialized for model: {self.model_name} at {self.generate_url}")

    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """
        Encodes an image file to a base64 string.

        Args:
            image_path (str): The file system path to the image.

        Returns:
            Optional[str]: The base64 encoded string of the image, or None if an error occurs
                           (e.g., file not found, encoding error).
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            print(f"LLaVAAdapter: Error - Image file not found at {image_path}")
            return None
        except Exception as e:
            print(f"LLaVAAdapter: Error encoding image {image_path} to base64: {e}")
            return None

    def chat(self, image_path: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Sends a request to the LLaVA model with an image and a text prompt.

        Args:
            image_path (str): Path to the image file.
            prompt (str): The textual prompt to accompany the image.
            options (Optional[Dict[str, Any]]): Optional dictionary of Ollama parameters
                (e.g., `{"temperature": 0.7}`).

        Returns:
            str: The model's response content as a string. Returns an error message string
                 if image encoding fails, the request fails, or the response is malformed.
        """
        encoded_image = self._encode_image_to_base64(image_path)
        if not encoded_image:
            return "Error: Could not encode image. Please check image path and integrity."

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [encoded_image],  # Ollama API expects a list of base64 encoded images
            "stream": False,
        }
        if options:
            payload["options"] = options

        log_prompt = prompt if len(prompt) < 100 else prompt[:97] + "..."
        # print(f"LLaVAAdapter: Sending request to {self.generate_url} with model {self.model_name}, image: {image_path}, prompt: '{log_prompt}'")

        try:
            response = requests.post(self.generate_url, json=payload, timeout=120) # Longer timeout for image models
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("response", "Error: 'response' field missing in LLaVA output.")
        except requests.exceptions.Timeout as e:
            print(f"LLaVAAdapter: Timeout error connecting to Ollama at {self.generate_url}: {e}")
            return f"Error: Timeout connecting to Ollama for LLaVA model. Details: {e}"
        except requests.exceptions.RequestException as e:
            print(f"LLaVAAdapter: Error connecting to Ollama at {self.generate_url}: {e}")
            return f"Error: Could not connect to Ollama service for LLaVA model. Details: {e}"
        except json.JSONDecodeError:
            print(f"LLaVAAdapter: Error decoding JSON response from Ollama. Response text: {response.text[:200]}...")
            return f"Error: Could not decode JSON response from LLaVA/Ollama. Response: {response.text}"
        except KeyError:
            response_content_for_log = response.json() if response else "No response object"
            print(f"LLaVAAdapter: Unexpected JSON structure from Ollama: {response_content_for_log}")
            return "Error: Unexpected response structure from LLaVA/Ollama."

if __name__ == '__main__':
    print("Testing Model Adapters (requires Ollama server running with appropriate models)...")

    # Determine effective model names and URL, prioritizing config but having defaults
    effective_deepseek_model = DEEPSEEK_MODEL 
    effective_llava_model = LLAVA_MODEL
    effective_ollama_url = OLLAMA_API_BASE_URL

    print(f"Using DeepSeek Model: {effective_deepseek_model}")
    print(f"Using LLaVA Model: {effective_llava_model}")
    print(f"Using Ollama URL: {effective_ollama_url}")

    # Test DeepSeekAdapter
    print("\n--- Testing DeepSeekAdapter ---")
    deepseek_adapter = DeepSeekAdapter(model_name=effective_deepseek_model, base_url=effective_ollama_url)
    ds_messages = [{"role": "user", "content": "What is the main purpose of a CPU? Provide a concise answer."}]
    deepseek_response = deepseek_adapter.chat(messages=ds_messages)
    print(f"DeepSeek Response: {deepseek_response}\n")

    # Test LLaVAAdapter
    print("\n--- Testing LLaVAAdapter ---")
    llava_adapter = LLaVAAdapter(model_name=effective_llava_model, base_url=effective_ollama_url)
    
    # Create a dummy image file for testing LLaVA
    dummy_image_path = "dummy_test_image_model_adapter.png"
    import os
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (250, 100), color = 'darkblue')
        draw = ImageDraw.Draw(img)
        draw.text((10,10), "LLaVA Adapter Test Image", fill=(255,255,0)) # Yellow text
        draw.rectangle(((50, 50), (150, 80)), fill="lightgreen")
        img.save(dummy_image_path)
        print(f"Created dummy image for testing: {dummy_image_path}")
        
        llava_prompt = "Describe this image in detail. What objects and text do you see?"
        llava_response = llava_adapter.chat(image_path=dummy_image_path, prompt=llava_prompt)
        print(f"LLaVA Response: {llava_response}")

    except ImportError:
        print("Pillow (PIL) not installed. Skipping LLaVA test that requires creating a dummy image.")
        print("To run this part of the test: pip install Pillow")
    except Exception as e:
        print(f"Error during LLaVAAdapter test with dummy image: {e}")
    finally:
        if os.path.exists(dummy_image_path):
            try:
                os.remove(dummy_image_path)
                print(f"Cleaned up dummy image: {dummy_image_path}")
            except Exception as e:
                print(f"Error cleaning up dummy image {dummy_image_path}: {e}")
    
    print("\n--- Model Adapter Tests Complete ---")
