import argparse, datetime as dt, json, pathlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET, html, re, time
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE="https://leonbrujo.github.io/Test/"
SITE=ROOT/"observador-global"
WORK=ROOT/"editorial"
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def fetch(url):
    if urllib.parse.urlparse(url).scheme!="https": raise ValueError("HTTPS required")
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ObservadorGlobal/1.0 editorial research"}),timeout=15) as r:
                return r.read(4000000),r.headers.get("Content-Type","")
        except Exception:
            if i==2: raise
            time.sleep(2**i)
def collect(date):
    result=[]; errors=[]; seen=set()
    for category,urls in load(WORK/"feeds.json").items():
        for url in urls:
            try:
                raw,_=fetch(url)
                for item in ET.fromstring(raw).findall(".//item")[:35]:
                    title=item.findtext("title","").strip(); link=item.findtext("link","").strip()
                    if not title or not link or link in seen: continue
                    seen.add(link)
                    result.append(dict(category=category,title=title,url=link,published=item.findtext("pubDate",""),feed=url))
            except Exception as e: errors.append(dict(feed=url,error=str(e)))
    save(WORK/"research"/(date+".json"),dict(date=date,items=result,errors=errors))
    if not result: raise RuntimeError("No feeds available")
def validate(d):
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}",d["date"])
    dt.date.fromisoformat(d["date"])
    cutoff=dt.datetime.fromisoformat(d["cutoff_at"]); assert cutoff.tzinfo and cutoff.astimezone(ZoneInfo("America/New_York")).date().isoformat()==d["date"]
    assert d["verification"]=="verified"
    assert d["title"] and d["summary"]
    assert len(d["sections"])==7
    assert [s["id"] for s in d["sections"]]==["world","main","briefs","analysis","watch","washington","river"]
    assert len(d["sections"][1]["articles"])==3
    assert 4<=len(d["sections"][2]["articles"])<=7
    assert 2<=len(d["sections"][5]["articles"])<=4
    assert 2<=len(d["sections"][6]["articles"])<=4
    assert 12<=len(d["dictionary"])<=35
    ids=set()
    for section in d["sections"]:
        for a in section["articles"]:
            assert a["id"] not in ids and re.fullmatch("[a-z0-9-]+",a["id"]); ids.add(a["id"])
            assert a["title"] and a["paragraphs"]
            if section["id"] in ("main","briefs","washington","river"):
                assert a["sources"]
            for u in a.get("sources",[]): fetch(u)
            if a.get("image"):
                im=a["image"]
                assert all(im.get(k) for k in ("url","credit","license","source","caption"))
                assert im["license"] in ("CC0","CC BY 4.0","CC BY-SA 4.0","CC BY 2.0","Public domain")
                assert fetch(im["url"])[1].startswith("image/")
                fetch(im["source"])
    for entry in d["dictionary"]:
        assert entry["terms"] and entry["text"] and entry["priority"] in ("esencial","alta")
    return d
def render(d,canonical):
    e=html.escape
    parts=[]
    for s in d["sections"]:
        parts.append('<section><h2>'+e(s["title"])+'</h2>')
        for a in s["articles"]:
            parts.append('<article id="'+e(a["id"])+'"><h3>'+e(a["title"])+'</h3>')
            if a.get("image"):
                im=a["image"]; parts.append('<figure><img loading="lazy" src="'+e(im["url"])+'" alt="'+e(im["caption"])+'"><figcaption>'+e(im["caption"]+" · "+im["credit"]+" · "+im["license"])+' <a href="'+e(im["source"])+'">Fuente</a></figcaption></figure>')
            parts.extend('<p>'+e(p)+'</p>' for p in a["paragraphs"])
            parts.append('<p class="sources">'+' · '.join('<a href="'+e(u)+'">Fuente '+str(i+1)+'</a>' for i,u in enumerate(a.get("sources",[])))+'</p></article>')
        parts.append('</section>')
    dictionary=json.dumps(d["dictionary"],ensure_ascii=False).replace("<","\\u003c")
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(d["title"])+'</title><link rel="canonical" href="'+canonical+'"><link rel="stylesheet" href="'+BASE+'assets/contexto.css?v=1"><link rel="stylesheet" href="'+BASE+'assets/editorial.css"><script>if(performance.getEntriesByType("navigation")[0]?.type==="reload"){history.scrollRestoration="manual";addEventListener("pageshow",()=>scrollTo(0,0));}</script></head><body><header>El Observador Global</header><nav><a href="'+BASE+'">Portada</a> · <a href="'+BASE+'ediciones.json">Archivo</a> · <a href="'+BASE+'rss.xml">RSS</a></nav><main><p class="meta">'+e(d["cutoff_at"])+' · America/New_York</p><h1>'+e(d["title"])+'</h1>'+''.join(parts)+'</main><script id="eog-context-data" type="application/json">'+dictionary+'</script><script defer src="'+BASE+'assets/contexto.js?v=2"></script></body></html>'
def publish(date):
    d=validate(load(WORK/"inbox"/(date+".json")))
    assert d["date"]==date
    archive=SITE/"ediciones"/date/"index.html"
    if archive.exists(): raise RuntimeError("Edition already exists; no overwrite")
    registry=load(SITE/"ediciones.json")
    assert not any(x["date"]==date for x in registry)
    if registry and date < max(x["date"] for x in registry): raise RuntimeError("Cannot replace homepage with older edition")
    registry.insert(0,dict(date=date,title=d["title"],categories=d["categories"],summary=d["summary"],cutoff_at=d["cutoff_at"],revision=1,verification=d["verification"]))
    registry.sort(key=lambda x:x["date"],reverse=True)
    archived=render(d,BASE+"ediciones/"+date+"/"); home=render(d,BASE)
    rss=ET.Element("rss",version="2.0"); channel=ET.SubElement(rss,"channel")
    for k,v in (("title","El Observador Global"),("link",BASE),("description","Diario internacional en español")): ET.SubElement(channel,k).text=v
    for x in registry[:30]:
        item=ET.SubElement(channel,"item")
        for k,v in (("title",x["title"]),("link",x.get("revision_url",BASE+"ediciones/"+x["date"]+"/")),("description",x["summary"])): ET.SubElement(item,k).text=v
    archive.parent.mkdir(parents=True,exist_ok=True); archive.write_text(archived,encoding="utf-8")
    (SITE/"index.html").write_text(home,encoding="utf-8"); save(SITE/"ediciones.json",registry)
    ET.ElementTree(rss).write(SITE/"rss.xml",encoding="utf-8",xml_declaration=True)
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("mode",choices=["collect","publish"]); p.add_argument("--date",default=dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()); a=p.parse_args()
    (collect if a.mode=="collect" else publish)(a.date)
