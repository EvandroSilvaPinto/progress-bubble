"""Accept documented Claude statusline JSON or normalized Antigravity quota on stdin."""
import argparse
import json
import os
from pathlib import Path
import sys
from usage_source import accept_feed
from web_client import save_secret


def install_claude(path=None):
    path=path or Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home()/'.claude')/'settings.json'
    data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(data,dict):raise ValueError('Invalid Claude settings; no changes made')
    existing=data.get('statusLine')
    if existing:
        if isinstance(existing,dict) and 'usage_bridge.py' in str(existing.get('command','')):return
        raise ValueError('Existing statusLine preserved. Add the quota bridge to your current statusline instead.')
    executable=Path(sys.executable).as_posix()
    script=Path(__file__).resolve().as_posix()
    data['statusLine']={'type':'command','command':f'"{executable}" "{script}" --provider claude'}
    save_secret(path,data)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',choices=['claude','antigravity'],default='claude')
    parser.add_argument('--setup-claude',action='store_true',help='Install only if no custom statusline exists')
    args=parser.parse_args()
    if args.setup_claude:
        try:install_claude()
        except (OSError,ValueError) as error:parser.exit(1,str(error)+'\n')
        print('Claude quota bridge configured. Restart Claude Code.');return
    try:
        raw=sys.stdin.read(262145)
        if len(raw)>262144:return
        accept_feed(args.provider,json.loads(raw))
    except (OSError,ValueError,TypeError):return


if __name__=='__main__':main()
