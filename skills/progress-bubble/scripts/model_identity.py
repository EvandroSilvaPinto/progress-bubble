"""Current-chat model metadata only; never infer a model from account quota."""
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID


def clean_model(value):
    if not isinstance(value,str):return None
    value=value.strip()
    return value if 0<len(value)<=96 and value.isprintable() else None


def codex_model(origin,sessions_root=None):
    if not isinstance(origin,str):return None
    try:
        url=urlsplit(origin)
        if url.scheme!='codex' or url.netloc!='threads':return None
        identity=str(UUID(url.path.lstrip('/')))
        root=Path(sessions_root) if sessions_root is not None else Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex')/'sessions'
        paths=sorted(root.rglob('*'+identity+'*.jsonl'),key=lambda p:p.stat().st_mtime,reverse=True)
        for path in paths[:1]:
            with path.open('rb') as stream:
                offset=max(0,path.stat().st_size-1048576)
                stream.seek(offset)
                data=stream.read(1048576)
            if offset:data=data.partition(b'\n')[2]
            for line in reversed(data.splitlines()):
                if not re.search(rb'"type"\s*:\s*"turn_context"',line):continue
                try:record=json.loads(line)
                except (ValueError,UnicodeError,RecursionError):continue
                if isinstance(record,dict) and record.get('type')=='turn_context':
                    payload=record.get('payload')
                    return clean_model(payload.get('model')) if isinstance(payload,dict) else None
    except (OSError,ValueError,TypeError):pass
    return None


def resolve_model(explicit,origin,previous):
    if explicit=='none':return None
    if explicit is not None:return clean_model(explicit)
    if isinstance(origin,str) and origin.startswith('codex://'):return codex_model(origin)
    if origin==previous.get('conversation_url'):return clean_model(previous.get('model_name'))
    return None
