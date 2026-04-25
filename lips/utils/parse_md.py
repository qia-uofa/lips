import re

def env_from_md(md_text: str) -> dict:
    """Extract env variables from ```env blocks in markdown."""
    env_vars = {}
    pattern = r"```env\n(.*?)\n```"
    
    for block in re.findall(pattern, md_text, re.DOTALL):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    md_text = re.sub(pattern, '', md_text)
    return md_text, env_vars

def ignore_from_md(md_text: str) -> dict:
    """Extract env variables from ```env blocks in markdown."""
    ignores = []
    pattern = r"```ignore\n(.*?)\n```"
    
    for block in re.findall(pattern, md_text, re.DOTALL):
        for line in block.splitlines():
            line = line.strip()
            ignores.append(line)
    md_text = re.sub(pattern, '', md_text)
    return md_text, '\n'.join(ignores)