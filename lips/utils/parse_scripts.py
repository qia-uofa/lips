import re

def env_from_script(md_text: str, quotation=r'```') -> dict:
    """Extract env variables from ```env blocks in markdown."""
    env_vars = {}
    pattern = quotation + r"env\n(.*?)\n" + quotation
    
    for block in re.findall(pattern, md_text, re.DOTALL):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    md_text = re.sub(pattern, '', md_text)
    return md_text, env_vars

def ignore_from_script(md_text: str, quotation=r'```') -> dict:
    """Extract env variables from ```env blocks in markdown."""
    ignores = []
    pattern = quotation + r"ignore\n(.*?)\n" + quotation
    
    for block in re.findall(pattern, md_text, re.DOTALL):
        for line in block.splitlines():
            line = line.strip()
            ignores.append(line)
    md_text = re.sub(pattern, '', md_text)
    return md_text, '\n'.join(ignores)