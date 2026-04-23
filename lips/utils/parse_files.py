import re
def parse_files(text: str) -> dict[str, str]:
    """Extract files from <file path="...">...</file> blocks."""
    pattern = r'<file path="([^"]+)">(.*?)</file>'
    
    return {
        path: content.strip()
        for path, content in re.findall(pattern, text, re.DOTALL)
    }