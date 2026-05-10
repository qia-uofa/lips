import re
from pathlib import Path
import pdfplumber
import pypdf
import pathspec

LINK_RE = re.compile(r'\[write:([^\]]+)\]\(([^)]+)\)')

def _read_text(real_path: Path) -> str:
    if real_path.suffix.lower() == '.pdf':
        try:
            with pdfplumber.open(real_path) as pdf:
                return '\n'.join(
                    page.extract_text() or '' for page in pdf.pages
                )
        except ImportError:
            reader = pypdf.PdfReader(str(real_path))
            return '\n'.join(
                page.extract_text() or '' for page in reader.pages
            )
    return real_path.read_text(encoding='utf-8', errors='replace')

def _file_block(virtual_path: str, real_path: Path) -> str:
    content = _read_text(real_path)
    return f'<file path="{virtual_path}">\n{content}\n</file>'

def _dir_block(virtual_root: str, real_root: Path, ignore='') -> str:
    virtual_root = virtual_root.rstrip('/')
    blocks = []
    
    spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore.splitlines())
    for real_file in sorted(p for p in real_root.rglob('*') if p.is_file()):
        rel = real_file.relative_to(real_root).as_posix()
        if not spec.match_file(rel):
            blocks.append(_file_block(f"{virtual_root}/{rel}", real_file))
    return "\n".join(blocks)

def resolve_links(md_text: str, root, ignore='') -> str:
    def replace(match: re.Match) -> str:
        virtual_path, real_path = match.group(1), match.group(2)
        p = Path(root / real_path)
        if p.is_file():
            return _file_block(virtual_path, p)
        if p.is_dir():
            return _dir_block(virtual_path, p, ignore)
        return match.group(0)

    return LINK_RE.sub(replace, md_text)

def resolve_env(md_text, env):
    for key,val in env.items():
        md_text = re.sub(f"<env:{key}>", lambda _: str(val), md_text)
    return md_text