
import re
from pathlib import Path

default_ignore = '''
__pycache__
.git
*.verify.md
'''

def env_from_script(md_text: str, stage, quot=r'```') -> dict:
    """Extract env variables from env blocks in markdown."""
    env_vars = {}
    pattern = rf"{quot}env\n(.*?){quot}"
    match = re.findall(pattern, md_text, re.DOTALL)
    if match == []:
        return md_text, { "TARGET": stage.name }
    for block in match:
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    md_text = re.sub(pattern, '', md_text, flags=re.DOTALL)
    return md_text, env_vars

def repo_ignore_from_script(md_text, which, quot='```'):
    """Extract env variables from ```env blocks in markdown."""
    ignores = []
    pattern =  rf"{quot}{which}ignore\n(.*?){quot}"
    match = re.findall(pattern, md_text, re.DOTALL)
    
    if match == []:
        return md_text, default_ignore
    
    for block in match:
        for line in block.splitlines():
            line = line.strip()
            ignores.append(line)
    md_text = re.sub(pattern, '', md_text, flags=re.DOTALL)
    return md_text, '\n'.join(ignores)

def ignore_from_script(md_text, quot='```'):
    md_text, source_ignore = repo_ignore_from_script(md_text, 'source', quot)
    md_text, target_ignore = repo_ignore_from_script(md_text, 'target', quot)
    return md_text, source_ignore, target_ignore