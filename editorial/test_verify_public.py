import unittest, json, html, xml.etree.ElementTree as ET
from unittest.mock import patch
import verify_public
class PublicVerification(unittest.TestCase):
    def test_consistency_and_stale_pages(self):
        date="2026-11-27"
        title="Fixture"
        base=verify_public.BASE
        page=f'<html>{date} {title}<script id="eog-context-data"></script></html>'
        pages={"":page,"ediciones/"+date+"/":page,"ediciones.json":json.dumps([{"date":date,"title":title,"verification":"verified"}]),"rss.xml":f'<rss><channel><item><link>{base}ediciones/{date}/</link></item></channel></rss>'}
        class Response:
            def __init__(self,body): self.body=body
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return self.body.encode()
        def fetch(url,**kwargs): return Response(pages[url.removeprefix(base).split("?")[0]])
        with patch.object(verify_public.urllib.request,"urlopen",side_effect=fetch):
            verify_public.check(date)
            pages[""]="stale homepage"
            with self.assertRaises(AssertionError): verify_public.check(date)
            pages[""]=page
            pages["rss.xml"]="<rss><channel/></rss>"
            with self.assertRaises(AssertionError): verify_public.check(date)
