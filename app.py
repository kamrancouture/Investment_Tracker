"""Investment Tracker: a phone-installable app with live ETF prices.

Your holdings are stored in your phone's browser; this server only looks up prices.
Run locally:  pip install -r requirements.txt && python app.py
Deploy:       gunicorn app:app
"""
import base64
import os
import time

import yfinance as yf
from flask import Flask, Response, abort, jsonify

FUNDS = ["VFV.TO", "VSP.TO"]
CACHE_SECONDS = 45
app = Flask(__name__)
_cache = {"at": 0.0, "prices": {}}


def fetch_price(ticker):
    try:
        value = float(yf.Ticker(ticker).fast_info["last_price"])
        return value if value > 0 else None
    except Exception:
        return None


@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")


@app.route("/api/prices")
def prices():
    if time.time() - _cache["at"] > CACHE_SECONDS:
        _cache["prices"] = {t: fetch_price(t) or _cache["prices"].get(t) for t in FUNDS}
        _cache["at"] = time.time()
    response = jsonify(_cache["prices"])
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/manifest.json")
def manifest():
    icons = [{"src": f"/icon-{n}.png", "sizes": f"{n}x{n}", "type": "image/png", "purpose": p}
             for n in (192, 512) for p in ("any", "maskable")]
    return jsonify(name="Investment Tracker", short_name="Invest", start_url="/", display="standalone",
                   background_color="#f4f6f9", theme_color="#1f4fd8", icons=icons)


@app.route("/icon-<int:size>.png")
def icon(size):
    if size not in ICONS:
        abort(404)
    return Response(base64.b64decode(ICONS[size]), mimetype="image/png")


@app.route("/sw.js")
def service_worker():
    return Response(SERVICE_WORKER, mimetype="application/javascript", headers={"Cache-Control": "no-cache"})


SERVICE_WORKER = """
const C='tracker-v1';
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.add('/')));self.skipWaiting()});
self.addEventListener('activate',e=>e.waitUntil(clients.claim()));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET'||new URL(e.request.url).pathname.startsWith('/api/'))return;
  e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request)));
});
"""

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#1f4fd8">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Invest">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/icon-512.png">
<title>Investment Tracker</title>
<style>
:root{--bg:#f4f6f9;--card:#fff;--ink:#14213d;--mute:#5b6577;--line:#d8dee8;--act:#1f4fd8;--on:#fff;--gain:#0d7a4a;--loss:#c2362b;--bar:#a9bce8;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f141d;--card:#182030;--ink:#e8edf6;--mute:#9aa6bb;--line:#2a3550;--act:#7a9bff;--on:#0f141d;--gain:#4cc38a;--loss:#ff7b70;--bar:#3a4c7a}}
:root[data-theme="dark"]{--bg:#0f141d;--card:#182030;--ink:#e8edf6;--mute:#9aa6bb;--line:#2a3550;--act:#7a9bff;--on:#0f141d;--gain:#4cc38a;--loss:#ff7b70;--bar:#3a4c7a}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-variant-numeric:tabular-nums}
main{max-width:560px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:20px;margin:0 0 2px}h2{font-size:19px;margin:0}p{margin:0}
.mute{color:var(--mute)}.small{font-size:13px}.gain{color:var(--gain)}.loss{color:var(--loss)}
.sum{padding:20px 0 4px}
.big{font-size:38px;font-weight:700;letter-spacing:-.02em;line-height:1.15;margin-top:4px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:16px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px}
.row{display:flex;gap:8px}.row input{flex:1 1 0;min-width:0}.px input{flex:0 0 104px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px;margin:14px 0}
dt{font-size:13px;color:var(--mute)}dd{margin:0;font-size:17px;font-weight:600}
input,button{font:inherit;min-height:44px;border-radius:8px}
input{width:100%;padding:0 12px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}
button{border:0;padding:0 16px;background:var(--act);color:var(--on);font-weight:600;cursor:pointer}
.seg{display:flex;gap:8px;margin-bottom:10px}
.seg.sub{margin-top:-2px}.seg.sub button{min-height:36px;font-size:13px}
.seg button{flex:1;background:transparent;color:var(--ink);border:1px solid var(--line)}
.seg button[aria-pressed=true]{background:var(--act);color:var(--on);border-color:var(--act)}
form.act{display:grid;gap:8px}
.msg{min-height:20px;margin-top:8px;font-size:14px}
:focus-visible{outline:2px solid var(--act);outline-offset:2px}
svg{width:100%;height:auto;display:block;margin-top:8px}
.b1{fill:var(--bar)}.b2{fill:var(--act)}.t{fill:var(--mute);font-size:12px}
.key{display:flex;gap:16px;font-size:13px;color:var(--mute)}
.key i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}
.k1{background:var(--bar)}.k2{background:var(--act)}
.ghost{min-height:32px;padding:0 10px;background:transparent;color:var(--act);border:1px solid var(--line);font-size:13px;margin-left:8px}
</style>
</head>
<body>
<main id="app"></main>
<script>
const T=['VFV.TO','VSP.TO'],KEY='investment-tracker-v1',app=document.getElementById('app');
const fresh=()=>({funds:Object.fromEntries(T.map(t=>[t,{shares:0,invested:0,price:null,at:null}]))});
const clean=o=>{const s=fresh();try{T.forEach(t=>{const f=o.funds[t]||{};s.funds[t]={shares:+f.shares||0,invested:+f.invested||0,price:+f.price>0?+f.price:null,at:f.at||null}})}catch(e){}return s};
let state=fresh(),ref=null,sync='Getting live prices…';
try{state=clean(JSON.parse(localStorage.getItem(KEY)))}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){}};
const ui={mode:{},by:{},msg:{}};
const cad=n=>n.toLocaleString('en-CA',{style:'currency',currency:'CAD'});
const signed=n=>(n<0?'−':'+')+cad(Math.abs(n));
const pct=n=>(n<0?'−':'+')+Math.abs(n).toFixed(2)+'%';
const cls=n=>n<0?'loss':'gain';
const when=iso=>new Date(iso).toLocaleString('en-CA',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
const val=f=>f.price&&f.shares>0?f.shares*f.price:null;
const num=(name,ph)=>`<input name="${name}" type="number" inputmode="decimal" step="0.01" min="0.01" placeholder="${ph}" aria-label="${ph}" required>`;
const setSync=m=>{sync=m;const e=document.getElementById('sync');if(e)e.textContent=m};

function render(){
  let tv=0,ti=0,held=0,unpriced=0;
  const max=Math.max(1,...T.flatMap(t=>[state.funds[t].invested,val(state.funds[t])||0]));
  const h=n=>Math.round((n||0)/max*100);
  const cards=T.map(t=>{
    const f=state.funds[t],v=val(f),mode=ui.mode[t]||'add',add=mode==='add',by=ui.by[t]||'amount';
    if(f.shares>0){held++;ti+=f.invested;if(v==null)unpriced++;else tv+=v}
    const g=v==null?null:v-f.invested;
    const addFields=by==='shares'
      ?`<div class="row">${num('amount','Amount invested')}${num('shares','Number of shares')}</div>`
      :`<div class="row">${num('price','Purchase price')}${num('amount','Amount invested')}</div>`;
    return `<section class="card"><div class="top"><h2>${t}</h2>
<b>${f.price?cad(f.price):'–'}</b></div>
<p class="mute small">${f.price?`Price ${cad(f.price)} as of ${when(f.at)}`:'Waiting for a live price.'}</p>
<dl class="stats"><div><dt>Shares</dt><dd>${f.shares.toFixed(4)}</dd></div><div><dt>Invested</dt><dd>${cad(f.invested)}</dd></div><div><dt>Value</dt><dd>${v==null?'–':cad(v)}</dd></div><div><dt>Gain</dt><dd class="${g==null?'':cls(g)}">${g==null?'–':`${signed(g)} (${pct(g/f.invested*100)})`}</dd></div></dl>
<div class="seg"><button type="button" data-t="${t}" data-mode="add" aria-pressed="${add}">Add</button><button type="button" data-t="${t}" data-mode="remove" aria-pressed="${!add}">Remove</button></div>
${add?`<div class="seg sub"><button type="button" data-t="${t}" data-addby="amount" aria-pressed="${by==='amount'}">Price &amp; amount</button><button type="button" data-t="${t}" data-addby="shares" aria-pressed="${by==='shares'}">Amount &amp; shares</button></div>`:''}
<form class="act" data-t="${t}" data-a="${add?'add':'remove'}" data-by="${by}">${add?addFields:num('amount','Amount to remove')}<button>${add?'Add investment':'Remove amount'}</button></form>
<p class="msg" role="status">${ui.msg[t]||''}</p></section>`}).join('');
  const bars=T.map((t,i)=>{const f=state.funds[t],v=val(f),x=50+i*130;
    return `<rect class="b1" x="${x}" y="${120-h(f.invested)}" width="36" height="${h(f.invested)}" rx="3"/><rect class="b2" x="${x+42}" y="${120-h(v)}" width="36" height="${h(v)}" rx="3"/><text class="t" x="${x+39}" y="140" text-anchor="middle">${t}</text>`}).join('');
  const g=tv-ti,ok=held>0&&!unpriced;
  app.innerHTML=`<h1>Investment Tracker</h1><p class="mute small"><span id="sync">${sync}</span><button type="button" class="ghost" data-refresh>Refresh</button></p>
<section class="sum"><p class="mute">Portfolio value</p><p class="big">${ok?cad(tv):held?'Loading…':cad(0)}</p>
<p class="${ok?cls(g):'mute'}">${ok?`${signed(g)} (${pct(g/ti*100)}) on ${cad(ti)} invested`:held?'Waiting for live prices.':'Add your first investment below.'}</p></section>${cards}
<section class="card"><h2>Invested and current value</h2><svg viewBox="0 0 300 150" role="img" aria-label="Invested versus current value for each fund">${bars}</svg><div class="key"><span><i class="k1"></i>Invested</span><span><i class="k2"></i>Value</span></div></section>
<p class="mute small" style="margin-top:16px">Prices come from Yahoo Finance and may be delayed.</p>`;
}

function act(t,a,by,x){
  const f=state.funds[t],now=new Date().toISOString();let m='';
  if(a==='price'){const p=x('v');if(!(p>0))return;f.price=p;f.at=now;m='Price updated.'}
  else if(a==='add'){
    if(by==='shares'){
      const n=x('amount'),sh=x('shares');if(!(n>0&&sh>0))return;
      const p=n/sh;
      f.shares+=sh;f.invested+=n;if(!f.price){f.price=p;f.at=now}
      m=`Added ${sh.toFixed(4)} shares for ${cad(n)} (${cad(p)}/share).`;
    }else{
      const p=x('price'),n=x('amount');if(!(p>0&&n>0))return;
      f.shares+=n/p;f.invested+=n;if(!f.price){f.price=p;f.at=now}
      m=`Added ${cad(n)} at ${cad(p)}.`;
    }
  }
  else{const n=x('amount');if(!(n>0))return;
    if(f.invested<=0)m='Nothing to remove yet.';
    else if(n>f.invested+0.005)m=`You can remove up to ${cad(f.invested)}.`;
    else{const r=1-n/f.invested;f.shares*=r;f.invested-=n;if(f.invested<=0.005){f.shares=0;f.invested=0}m=`Removed ${cad(n)}.`}}
  ui.msg[t]=m;save();render();
}


app.addEventListener('submit',e=>{e.preventDefault();const f=e.target,d=new FormData(f);act(f.dataset.t,f.dataset.a,f.dataset.by,k=>parseFloat(d.get(k)))});
app.addEventListener('click',e=>{
  const m=e.target.closest('[data-mode]');if(m){ui.mode[m.dataset.t]=m.dataset.mode;ui.msg[m.dataset.t]='';render();return}
  const ab=e.target.closest('[data-addby]');if(ab){ui.by[ab.dataset.t]=ab.dataset.addby;ui.msg[ab.dataset.t]='';render()}
});

render();

async function refresh(){
  let msg;
  try{
    const r=await fetch('/api/prices',{cache:'no-store'});
    if(!r.ok)throw new Error('bad');
    const d=await r.json(),now=new Date().toISOString();let n=0;
    T.forEach(t=>{if(d[t]>0){state.funds[t].price=d[t];state.funds[t].at=now;n++}});
    save();msg=n?'Live prices updated '+when(now):'Prices unavailable. Showing the last ones saved.';
  }catch(e){msg='Offline. Showing the last saved prices.'}
  setSync(msg);
  if(!(document.activeElement&&document.activeElement.tagName==='INPUT'))render();
}
app.addEventListener('click',e=>{if(e.target.closest('[data-refresh]'))refresh()});
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
setInterval(refresh,60000);refresh();
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
</script>
</body>
</html>
"""

ICONS = {192: "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", 512: "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"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
