import base64
import mimetypes
from pathlib import Path

TYPE_MAP = {
    # text
    'text/plain':           'text',
    'text/html':            'text',
    'text/css':             'text',
    'text/javascript':      'text',
    'text/typescript':      'text',
    'text/csv':             'text',
    'text/xml':             'text',
    'text/markdown':        'text',
    'text/x-python':        'text',
    'text/x-java':          'text',
    'text/x-c':             'text',
    'text/x-c++':           'text',
    'text/x-csharp':        'text',
    'text/x-go':            'text',
    'text/x-rust':          'text',
    'text/x-ruby':          'text',
    'text/x-php':           'text',
    'text/x-swift':         'text',
    'text/x-kotlin':        'text',
    'text/x-scala':         'text',
    'text/x-shell':         'text',
    'text/x-sql':           'text',
    'text/x-latex':         'text',
    'text/x-rst':           'text',
    'text/x-diff':          'text',
    'text/x-patch':         'text',
    'text/x-yaml':          'text',
    'text/x-toml':          'text',
    'text/x-ini':           'text',
    # json / data
    'application/json':             'text',
    'application/ld+json':          'text',
    'application/x-ndjson':         'text',
    'application/xml':              'text',
    'application/graphql':          'text',
    'application/x-yaml':           'text',
    'application/x-sh':             'text',
    'application/x-python-code':    'text',
    'application/x-httpd-php':      'text',
    # images
    'image/jpeg':       'image',
    'image/png':        'image',
    'image/gif':        'image',
    'image/webp':       'image',
    'image/bmp':        'image',
    'image/tiff':       'image',
    'image/svg+xml':    'image',
    'image/x-icon':     'image',
    'image/heic':       'image',
    'image/heif':       'image',
    'image/avif':       'image',
    # documents
    'application/pdf':                                                          'document',
    'application/msword':                                                       'document',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document':  'document',
    'application/vnd.ms-excel':                                                 'document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':        'document',
    'application/vnd.ms-powerpoint':                                            'document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation':'document',
    'application/epub+zip':                                                     'document',
    # audio
    'audio/mpeg':   'audio',
    'audio/mp4':    'audio',
    'audio/wav':    'audio',
    'audio/ogg':    'audio',
    'audio/flac':   'audio',
    'audio/webm':   'audio',
    'audio/aac':    'audio',
    'audio/x-wav':  'audio',
    'audio/x-m4a':  'audio',
    'audio/opus':   'audio',
    # video
    'video/mp4':        'video',
    'video/mpeg':       'video',
    'video/webm':       'video',
    'video/ogg':        'video',
    'video/quicktime':  'video',
    'video/x-msvideo':  'video',
    'video/x-matroska': 'video',
    'video/3gpp':       'video',
    'video/x-flv':      'video',
}


def content_block_from_file(file, repo_path):
    path = Path(file).resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    media_type, _ = mimetypes.guess_type(path)
    if media_type in TYPE_MAP:
        kind = TYPE_MAP[media_type]
    else:
        kind = 'text'

    if kind == 'text':
        with open(path, encoding='utf-8', errors='replace') as f:
            data = f.read()
        relative_path = path.relative_to(repo_path)
        return {
            "type": "text",
            "text": f"<file path=\"{relative_path}\">\n{data}\n</file>"
        }

    with open(path, 'rb') as f:
        data = base64.standard_b64encode(f.read()).decode('utf-8')
    url = f"data:{media_type};base64,{data}"

    if kind == 'image':
        return [
            {"type": "text", "text": f"<image path=\"{path}\">"},
            {"type": "image_url", "image_url": {"url": url}},
            {"type": "text", "text": "</image>"},
        ]
    elif kind == 'document':
        return {
            "type": "document_url",
            "document_url": {"url": url}
        }
    elif kind == 'audio':
        return {
            "type": "input_audio",
            "input_audio": {"data": data, "format": media_type.split("/")[-1]}
        }
    else:
        raise ValueError(f"Unsupported kind: {kind!r} for file: {path.name}")


def message_from_files(files, repo_path):
    content = []
    for file in files:
        block = content_block_from_file(file, repo_path)
        if isinstance(block, list):
            content.extend(block)
        else:
            content.append(block)
    return {"role": "user", "content": content}