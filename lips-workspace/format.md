Generate only the files that need to be created or updated. Use the following XML format with absolute paths:

<file path="./file-1.txt">
file content here
...
</file>

<file path="./file-2.json">
{
    "key1": "value1",
    "key2": "value2"
}
</file>

Rules:
- Start by analyzing and breaking down the problem before doing anything else.
- Before generating each file, write down your reasoning through the logic and its impact on the overall repository structure.
- Every file tag must contain the complete, verbatim file contents — no partial files, no placeholders, no commentary inside file tags.
- Use relative paths for all files, beginning with "./", which is the "<masked-path-to-output-repo>".
- Only include files that are new or modified. If no files need to be created or modified, output nothing — do not emit any file tags at all.
- If an image file needs to be generated, generate a prompt file with the extension ".prompt.md". For example, if 'icon.png' needs to be generated, instead generate 'icon.png.prompt.md', which includes an elaborate prompt for further generation of the image.
- Respect my last prompt message — only generate or update files specified by it.
- The output files might be partially generated already. In that case, only generate the missing files.
- If the output files already meet the generation standard, output nothing.

- You can delete a file by writing a strictly empty file tag (no spaces, no newlines between the tags):
<file path="./deleted-file.ext"></file>

- When overwriting, mirror the exact path of the overwritten file but replace the masked path with "./". For example, overwrite <file path="<masked-path-to-output-repo>/to-be-overwritten-file.ext">...</file> with <file path="./to-be-overwritten-file.ext">...</file>
