import base64, json, pathlib, sys, time, urllib.parse, datetime
import requests, websocket

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'evidence'
tabs = requests.get('http://127.0.0.1:9335/json', timeout=10).json()
active=pathlib.Path('/private/tmp/safetywatch_active_tab')
saved=active.read_text().strip() if active.exists() else ''
if sys.argv[1]=='tabs':
    print(json.dumps([{'id':t['id'],'title':t['title'],'url':urllib.parse.urlsplit(t['url'])._replace(query='',fragment='').geturl()} for t in tabs if t['type']=='page'],ensure_ascii=False,indent=2));sys.exit(0)
if sys.argv[1]=='use':
    active.write_text(sys.argv[2]);sys.exit(0)
tab = next((t for t in tabs if t['id']==saved),next(t for t in tabs if t['type']=='page'))
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], origin='http://localhost:9335', timeout=25)
seq = 0
def cmd(method, params=None):
    global seq
    seq += 1
    ws.send(json.dumps({'id':seq,'method':method,'params':params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get('id') == seq:
            if 'error' in msg: raise RuntimeError(msg['error'])
            return msg.get('result',{})
def ev(expression):
    r = cmd('Runtime.evaluate', {'expression':expression, 'returnByValue':True, 'awaitPromise':True,'userGesture':True})
    if 'exceptionDetails' in r: return r['exceptionDetails']
    return r.get('result',{}).get('value',r.get('result'))
def press(pos):
    if not pos: print('NOT FOUND');return
    cmd('Input.dispatchMouseEvent',{'type':'mouseMoved',**pos})
    cmd('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,**pos})
    cmd('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,**pos})
def capture(name):
    data = ev("""(()=>({url:location.origin+location.pathname,title:document.title,text:document.body.innerText,links:[...document.querySelectorAll('a')].filter(e=>e.getClientRects().length).map(e=>({text:e.innerText,title:e.title,href:e.getAttribute('href')})),controls:[...document.querySelectorAll('input,select,button,textarea')].filter(e=>e.getClientRects().length).map(e=>({tag:e.tagName,type:e.type,id:e.id,name:e.name,text:e.innerText,placeholder:e.placeholder,aria:e.getAttribute('aria-label')})),size:{w:innerWidth,h:innerHeight,sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight}}))()""")
    data['captured_at']=datetime.datetime.now().astimezone().isoformat()
    ROOT.joinpath(name+'.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    shot=cmd('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
    ROOT.joinpath(name+'.png').write_bytes(base64.b64decode(shot['data']))
    if isinstance(data,dict) and 'controls' in data:
        data['controls']=[{'tag':x['tag'],'id':x['id'],'text':x.get('text'),'placeholder':x.get('placeholder'),'aria':x.get('aria')} for x in data['controls'] if x.get('placeholder') or x.get('aria')]
    if len(data.get('links',[]))>20:data['links']='Full links saved in JSON evidence'
    print(json.dumps(data,ensure_ascii=False,indent=2))
cmd('Page.enable')
cmd('Page.bringToFront')
if sys.argv[1] == 'new':
    t=cmd('Target.createTarget',{'url':sys.argv[2]});active.write_text(t['targetId']);print(t)
elif sys.argv[1] == 'nav':
    cmd('Page.navigate', {'url':sys.argv[2]}); time.sleep(float(sys.argv[4]) if len(sys.argv)>4 else 3); capture(sys.argv[3])
elif sys.argv[1] == 'eval':
    print(json.dumps(ev(sys.argv[2]),ensure_ascii=False,indent=2))
elif sys.argv[1] == 'capture': capture(sys.argv[2])
elif sys.argv[1] == 'click':
    pos=ev("(async()=>{const e=[...document.querySelectorAll('button,a,[role=button],label')].find(e=>(e.innerText||e.textContent||'').trim()==="+json.dumps(sys.argv[2])+"&&e.getClientRects().length&&!e.disabled); if(!e)return null;e.scrollIntoView({behavior:'instant',block:'center'});await new Promise(r=>setTimeout(r,200));const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()")
    press(pos)
    time.sleep(float(sys.argv[4]) if len(sys.argv)>4 else 1.5);capture(sys.argv[3])
elif sys.argv[1]=='close':
    pos=ev("(()=>{const e=[...document.querySelectorAll('button')].filter(e=>(e.getAttribute('aria-label')==='Close modal'||e.innerText==='×')&&e.getClientRects().length).at(-1);if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()")
    press(pos);time.sleep(.5);capture(sys.argv[2])
elif sys.argv[1] == 'hover':
    pos=ev("(()=>{const e=[...document.querySelectorAll('button,a')].find(e=>(e.innerText||e.textContent||'').trim()==="+json.dumps(sys.argv[2])+"); if(!e)return null; const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()")
    if pos: cmd('Input.dispatchMouseEvent',{'type':'mouseMoved',**pos})
    time.sleep(1);capture(sys.argv[3])
elif sys.argv[1] == 'selector':
    pos=ev("(async()=>{const e=document.querySelector("+json.dumps(sys.argv[2])+");if(!e||!e.getClientRects().length||e.disabled)return null;e.scrollIntoView({behavior:'instant',block:'center',inline:'nearest'});await new Promise(r=>setTimeout(r,200));const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()")
    press(pos);time.sleep(1.5);capture(sys.argv[3])
elif sys.argv[1] == 'point':
    press({'x':float(sys.argv[2]),'y':float(sys.argv[3])});time.sleep(1.5);capture(sys.argv[4])
elif sys.argv[1] == 'mobile':
    cmd('Emulation.setDeviceMetricsOverride',{'width':int(sys.argv[2]),'height':int(sys.argv[3]),'deviceScaleFactor':1,'mobile':False}); time.sleep(1); capture(sys.argv[4])
ws.close()
