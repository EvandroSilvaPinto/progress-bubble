"""Validated local subscription windows, independent of task progress."""
import math
import time

STALE_AFTER=180
COLORS=('#58d9b0','#f1cc62','#ffad66','#ff7185')


def number(value):
    return type(value) in (int,float) and abs(value)<=10**12 and math.isfinite(value)


def normalize(provider,raw,now=None):
    now=time.time() if now is None else now
    windows={}
    if not isinstance(raw,dict):raw={}
    if provider=='codex':
        limits=raw.get('rateLimitsByLimitId',{})
        limits=limits.get('codex') if isinstance(limits,dict) else None
        limits=limits or raw.get('rateLimits',{})
        source=[(key,limits.get(key),None) for key in ('primary','secondary')] if isinstance(limits,dict) else []
    elif provider=='claude':
        limits=raw.get('rate_limits',{})
        source=[('primary',limits.get('five_hour'),300),('secondary',limits.get('seven_day'),10080)] if isinstance(limits,dict) else []
    else:
        limits=raw.get('windows',{})
        source=[(key,limits.get(key),None) for key in ('primary','secondary')] if isinstance(limits,dict) else []
    for key,item,duration in source:
        if not isinstance(item,dict):continue
        used=item.get('usedPercent',item.get('used_percentage',item.get('used_percent')))
        minutes=item.get('windowDurationMins',item.get('window_minutes',duration))
        reset=item.get('resetsAt',item.get('resets_at'))
        if not number(used) or not 0<=used<=100 or not number(minutes) or not 0<minutes<=525600:continue
        windows[key]={'used_percent':used,'window_minutes':minutes,
                      'resets_at':reset if number(reset) and reset>0 else None}
    return {'provider':provider,'observed_at':now,'windows':windows}


def duration(seconds):
    minutes=max(1,math.ceil(seconds/60))
    if seconds<60:return '<1min'
    if minutes>=1440:return f'{minutes//1440}d'+(f' {minutes%1440//60}h' if minutes%1440>=60 else '')
    return (f'{minutes//60}h' if minutes>=60 else '')+(f' {minutes%60}min' if minutes>=60 and minutes%60 else f'{minutes}min' if minutes<60 else '')


def view(snapshot,selection='primary',now=None,lang='pt'):
    now=time.time() if now is None else now
    pt=lang=='pt'
    result={'used':None,'color':None,'label':'Assinatura' if pt else 'Subscription',
            'detail':'Indisponível' if pt else 'Unavailable','full':False,'key':selection}
    if not isinstance(snapshot,dict):return result
    observed=snapshot.get('observed_at')
    if not number(observed) or observed>now+5 or now-observed>STALE_AFTER:
        result['detail']='Dados desatualizados' if pt else 'Outdated data'
        return result
    windows=snapshot.get('windows',{})
    if not isinstance(windows,dict):return result
    key=selection if selection in windows else next(iter(windows),'primary')
    item=windows.get(key)
    if not isinstance(item,dict):return result
    used,minutes,reset=item.get('used_percent'),item.get('window_minutes'),item.get('resets_at')
    if not number(used) or not 0<=used<=100 or not number(minutes) or not 0<minutes<=525600:return result
    label=('Semanal' if pt else 'Weekly') if minutes==10080 else duration(minutes*60)
    result.update(label=result['label']+' · '+label,key=key)
    if number(reset) and reset<=now:
        result['detail']='Atualizando cota' if pt else 'Refreshing quota'
        return result
    result.update(used=used,color=COLORS[3 if used>=95 else 2 if used>=80 else 1 if used>=60 else 0],
                  detail=(f'{used:g}% usado' if pt else f'{used:g}% used'),full=used>=100)
    if used>=100:
        result['detail']=('Renova em ' if pt else 'Renews in ')+duration(reset-now) if number(reset) else ('Renovação indisponível' if pt else 'Reset unavailable')
    return result
