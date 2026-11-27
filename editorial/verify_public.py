import sys, time, json, html, urllib.request, xml.etree.ElementTree as ET
from pipeline import BASE
def check(date):
    def read(path):
        with urllib.request.urlopen(BASE+path+"?edition="+date+"&check="+str(time.time_ns()),timeout=20) as r:
            return r.read().decode("utf-8")
    home=read("")
    archive=read("ediciones/"+date+"/")
    registry=json.loads(read("ediciones.json"))
    rss=ET.fromstring(read("rss.xml"))
    assert registry[0]["date"]==date
    assert registry[0]["verification"]=="verified"
    assert date in home and date in archive
    assert html.escape(registry[0]["title"]) in home and html.escape(registry[0]["title"]) in archive
    assert rss.findtext("./channel/item/link")==BASE+"ediciones/"+date+"/"
    assert "eog-context-data" in home and "eog-context-data" in archive
if __name__=="__main__":
    for attempt in range(8):
        try:
            check(sys.argv[1]); print("Public edition verified",sys.argv[1]); break
        except Exception as e:
            print("Verification attempt",attempt+1,str(e))
            if attempt==7: raise
            time.sleep(15)
