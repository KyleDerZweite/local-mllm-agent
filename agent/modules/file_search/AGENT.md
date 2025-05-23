# Tool: File Search

This tool searches for files in a specified directory (or a predefined default directory) that contain certain keywords in their name or content.

## When to use:

Use this tool when the user's prompt explicitly asks to:
- Find local files.
- Check for the existence of documents on the local system.
- Search within local documents for specific information if the prompt implies the information might be stored locally.

## Input Parameters:

- `query` (string, required): The keywords or search term to look for in file names or content.
- `directory` (string, optional): The specific directory to search in. If not provided, a default search path might be used.

## Output:

- A list of file paths that match the search criteria.
- Or, a summary if content search is performed, indicating which files contain the information.
- If no files are found, it will indicate that.
