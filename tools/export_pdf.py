from pathlib import Path
import requests,websocket,json,time,base64
root=Path(__file__).resolve().parents[1]
tabs=requests.get('http://localhost:9335/json',timeout=10).json()
tab=next(t for t in tabs if t.get('type')=='page' and t['url'].startswith((root/'workflow.html').as_uri()))
ws=websocket.create_connection(tab['webSocketDebuggerUrl'],origin='http://localhost:9335',timeout=30)
seq=0
def cmd(method,params=None):
 global seq
 seq+=1;ws.send(json.dumps({'id':seq,'method':method,'params':params or {}}))
 while True:
  x=json.loads(ws.recv())
  if x.get('id')==seq:
   if 'error' in x:raise RuntimeError(x['error'])
   return x.get('result',{})
target=cmd('Target.createTarget',{'url':(root/'report.html').as_uri()})['targetId']
ws.close();time.sleep(.5)
tabs=requests.get('http://localhost:9335/json',timeout=10).json();tab=next(t for t in tabs if t['id']==target)
ws=websocket.create_connection(tab['webSocketDebuggerUrl'],origin='http://localhost:9335',timeout=30)
cmd('Page.bringToFront');cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
time.sleep(.5)
r=cmd('Runtime.evaluate',{'expression':'document.fonts.ready.then(()=>document.body.innerText.length)','awaitPromise':True,'returnByValue':True})
print({'report_text_length':r['result']['value']})
pdf=cmd('Page.printToPDF',{'landscape':False,'printBackground':True,'paperWidth':8.27,'paperHeight':11.69,'marginTop':.5,'marginBottom':.5,'marginLeft':.5,'marginRight':.5,'displayHeaderFooter':True,'headerTemplate':'<div></div>','footerTemplate':'<div style="font-size:9px;width:100%;text-align:center;color:#718095">안전워치 UX 개편 제안서 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>'})
(root/'안전워치_UX_개편_제안서.pdf').write_bytes(base64.b64decode(pdf['data']))
shot=cmd('Page.captureScreenshot',{'format':'png'});(root/'report_preview.png').write_bytes(base64.b64decode(shot['data']))
print({'report_tab':target,'pdf':'안전워치_UX_개편_제안서.pdf'})
ws.close()
