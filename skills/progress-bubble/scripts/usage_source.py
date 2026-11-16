"""Private local quota cache shared by bubbles, with nonblocking background refresh."""
import json
import os
import hashlib
import threading
import time
from pathlib import Path
from colors import config_path
from usage_model import normalize,number
from usage_rpc import read_codex
from web_client import save_secret,task_lock


def cache_path(provider):
    if provider not in ('codex','claude','antigravity'):raise ValueError('Unknown quota provider')
    environment={'codex':'CODEX_HOME','claude':'CLAUDE_CONFIG_DIR','antigravity':'PROGRESS_BUBBLE_USAGE_PROFILE'}[provider]
    defaults={'codex':'.codex','claude':'.claude','antigravity':'.antigravity'}
    profile=Path(os.environ.get(environment) or Path.home()/defaults[provider]).expanduser().resolve()
    identity=hashlib.sha256(os.path.normcase(str(profile)).encode('utf-8')).hexdigest()[:20]
    return config_path().parent/'usage'/('quota-'+provider+'-'+identity+'.json')


def load_cache(provider):
    try:
        data=json.loads(cache_path(provider).read_text(encoding='utf-8'))
        if not isinstance(data,dict) or data.get('provider')!=provider or not number(data.get('observed_at')):return None
        clean=normalize('antigravity',{'windows':data.get('windows')},now=data['observed_at'])
        clean['provider']=provider
        return clean
    except (OSError,ValueError,TypeError):return None


def accept_feed(provider,raw):
    data=normalize(provider,raw)
    save_secret(cache_path(provider),data)
    return data


def poll(provider):
    if provider!='codex':return load_cache(provider)
    path=cache_path(provider)
    try:
        with task_lock(path):
            data=load_cache(provider)
            if data and 0<=time.time()-data.get('observed_at',0)<60:return data
            attempt=path.with_name(path.name+'.attempt.json')
            try:
                attempted=json.loads(attempt.read_text()).get('at',0)
                if number(attempted) and 0<=time.time()-attempted<60:return data
            except (OSError,ValueError,TypeError):pass
            save_secret(attempt,{'at':time.time()})
            return accept_feed(provider,read_codex())
    except (OSError,ValueError,TypeError):return load_cache(provider)


class UsageReader:
    def __init__(self):
        self.worker=None;self.next_poll=0

    def read(self,provider):
        if provider not in ('codex','claude','antigravity'):return None
        if provider=='codex' and time.monotonic()>=self.next_poll and not (self.worker and self.worker.is_alive()):
            self.next_poll=time.monotonic()+60
            self.worker=threading.Thread(target=poll,args=(provider,),daemon=True);self.worker.start()
        return load_cache(provider)


def provider_for(value,origin=None):
    if value and value!='auto':return value
    if isinstance(origin,str) and origin.startswith('codex://'):return 'codex'
    return 'claude' if os.environ.get('CLAUDECODE') and not os.environ.get('CODEX_THREAD_ID') else 'off'
