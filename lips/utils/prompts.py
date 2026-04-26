def update_files_prompt(path):
    return f'''
Generate only the files that need to be created or updated. Use the following XML format with absolute paths:

<file path="./file-1.txt">
file content here
...
</file>

<file path="./file-2.json">
{{
    "key1": "value1",
    "key2": "value2"
}}
</file>

Rules:
- Start by analyzing and breaking down the problem before doing anything else.
- Before generating each file, write down your reasoning through the logic and its impact on the overall repository structure.
- Every file tag must contain the complete file contents — no partial files, no placeholders.
- Use relative paths for all files, beginning with "./", which is the "<masked-path-to-output-repo>". 
- Only include files that are new or modified.
- If an image file needs to be generated, generate a prompt file with the extension ".prompt.md". For example, if 'icon.png' needs to be generated, instead, generate 'icon.png.prompt.md', which includes a elaborate prompt for further generation of the image. 
- Respect my last prompt message, only generate or update files specofied by it. 
- The output files might be partially generated already. In that case, only generate the missing files. 
- If the output files already meet the generation standard, opt out and don't generate anything. 

You can delete a file by overwriting an STRICTLY empty (no spaces, no endlines) file to it:
<file path="./deleted-file.ext"></file>

When overwriting, remember to mirror the exact path of the ovverwriten file, but replace the masked path with "./". For example:
Overwrite <file path="<masked-path-to-output-repo>/to-be-overwritten-file.ext">...</file> with <file path="./to-be-overwritten-file.ext">...</file>
'''