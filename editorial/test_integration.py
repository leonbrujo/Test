import unittest, tempfile, pathlib, json, xml.etree.ElementTree as ET
from unittest.mock import patch
import pipeline
class Integration(unittest.TestCase):
    def test_full_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); site=root/"site"; work=root/"editorial"
            site.mkdir(); (work/"inbox").mkdir(parents=True)
            old={"date":"2026-11-26","title":"Historical fixture","summary":"Fixture"}
            pipeline.save(site/"ediciones.json",[old])
            oldpage=site/"ediciones"/old["date"]/"index.html"
            oldpage.parent.mkdir(parents=True); oldpage.write_text("historical fixture")
            sections=[]
            for name,n in zip(["world","main","briefs","analysis","watch","washington","river"],[1,3,4,1,1,2,2]):
                sections.append({"id":name,"title":name,"articles":[{"id":name+"-"+str(i),"title":"TEST ONLY "+name,"paragraphs":["Synthetic fixture, not news. Concepto de prueba."],"sources":["https://example.org/source"]} for i in range(n)]})
            sections[1]["articles"][0]["image"]={"url":"https://example.org/image.png","credit":"Fixture","license":"CC0","source":"https://example.org/license","caption":"TEST IMAGE"}
            d={"date":"2026-11-27","cutoff_at":"2026-11-27T06:00:00-05:00","verification":"verified","title":"TEST ONLY","summary":"Synthetic fixture","categories":["test"],"sections":sections,"dictionary":[{"kind":"CONCEPTO","title":"Fixture "+str(i),"terms":["Concepto de prueba"],"text":"Synthetic definition","priority":"alta"} for i in range(12)]}
            pipeline.save(work/"inbox"/"2026-11-27.json",d)
            def fake_fetch(url): return b"fixture", "image/png" if url.endswith(".png") else "text/html"
            with patch.object(pipeline,"SITE",site),patch.object(pipeline,"WORK",work),patch.object(pipeline,"fetch",side_effect=fake_fetch):
                pipeline.publish(d["date"])
                home=(site/"index.html").read_text()
                self.assertIn("TEST ONLY",home)
                self.assertIn("TEST IMAGE",home)
                self.assertIn("contexto.js?v=2",home)
                self.assertIn("editorial.css",home)
                self.assertEqual(len(pipeline.load(site/"ediciones.json")),2)
                self.assertEqual(oldpage.read_text(),"historical fixture")
                self.assertEqual(len(ET.parse(site/"rss.xml").findall(".//item")),2)
                self.assertIn(pipeline.BASE+"ediciones/2026-11-27/",(site/"ediciones"/d["date"]/"index.html").read_text())
                with self.assertRaises(RuntimeError): pipeline.publish(d["date"])
                self.assertEqual((site/"index.html").read_text(),home)
                d["date"]="2026-11-28"; d["cutoff_at"]="2026-11-28T06:00:00-05:00"; d["verification"]="partial"
                pipeline.save(work/"inbox"/"2026-11-28.json",d)
                with self.assertRaises(AssertionError): pipeline.publish(d["date"])
                self.assertEqual((site/"index.html").read_text(),home)
