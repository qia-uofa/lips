def update_files_prompt(path):
    return f'''
Generate only the files that need to be created or updated. Use the following XML format with absolute paths:

<file path="{path}/file-1.py">
# file content here
import json
...
</file>

<file path="{path}/file-2.json">
{{
    "key1": "value1",
    "key2": "value2"
}}
</file>

Rules:
- Start by analyzing and breaking down the problem before doing anything else.
- Before generating each file, write down your reasoning through the logic and its impact on the overall repository structure.
- Every file tag must contain the complete file contents — no partial files, no placeholders.
- Use the absolute paths for all files, beginning with "{path}". 
- Only include files that are new or modified.
- If an image file needs to be generated, generate a prompt file with the extension ".prompt.md". For example, if 'icon.png' needs to be generated, instead, generate 'icon.png.prompt.md', which includes a elaborate prompt for further generation of the image. 
'''