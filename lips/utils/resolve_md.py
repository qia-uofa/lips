import re
from pathlib import Path

LINK_RE = re.compile(r'\[write:([^\]]+)\]\(([^)]+)\)')

def _file_block(virtual_path: str, real_path: Path) -> str:
    content = real_path.read_text(encoding='utf-8', errors='replace')
    return f'<file path="{virtual_path}">\n{content}\n</file>'

def _dir_block(virtual_root: str, real_root: Path) -> str:
    virtual_root = virtual_root.rstrip('/')
    blocks = []
    for real_file in sorted(p for p in real_root.rglob('*') if p.is_file()):
        rel = real_file.relative_to(real_root).as_posix()
        blocks.append(_file_block(f"{virtual_root}/{rel}", real_file))
    return "\n".join(blocks)

def resolve_links(md_text: str, stage) -> str:
    def replace(match: re.Match) -> str:
        virtual_path, real_path = match.group(1), match.group(2)
        p = Path(stage.root / 'build' / real_path)
        if p.is_file():
            return _file_block(virtual_path, p)
        if p.is_dir():
            return _dir_block(virtual_path, p)
        return match.group(0)

    return LINK_RE.sub(replace, md_text)