"""Read account quota through the official local Codex client; never read auth files."""
import json
import queue
import shutil
import subprocess
import threading
import time


def read_codex():
    command=shutil.which('codex')
    if not command:raise OSError('Codex unavailable')
    process=subprocess.Popen([command,'app-server','--stdio','-c','analytics.enabled=false'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    messages=queue.Queue(maxsize=32)
    def receive():
        try:
            for line in process.stdout:
                if len(line)>65536:continue
                try:message=json.loads(line)
                except ValueError:continue
                if isinstance(message,dict) and message.get('id') in (1,2):
                    try:messages.put_nowait(message)
                    except queue.Full:pass
        except (OSError,ValueError):pass
    reader=threading.Thread(target=receive,daemon=True);reader.start()
    def call(identity,method,params=None):
        data={'id':identity,'method':method}
        if params is not None:data['params']=params
        process.stdin.write(json.dumps(data)+'\n');process.stdin.flush()
        end=time.monotonic()+10
        while time.monotonic()<end:
            answer=messages.get(timeout=max(.01,end-time.monotonic()))
            if answer.get('id')==identity:
                if 'error' in answer:raise OSError('Quota unavailable')
                result=answer.get('result')
                if not isinstance(result,dict):raise OSError('Invalid quota response')
                return result
        raise OSError('Quota timeout')
    try:
        call(1,'initialize',{'clientInfo':{'name':'progress_bubble_usage','version':'1.0'},'capabilities':{'experimentalApi':True}})
        process.stdin.write('{"method":"initialized"}\n');process.stdin.flush()
        return call(2,'account/rateLimits/read')
    except (queue.Empty,BrokenPipeError) as error:
        raise OSError('Quota unavailable') from error
    finally:
        process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        process.stdin.close();reader.join(timeout=1);process.stdout.close()
