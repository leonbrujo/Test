"""Synthetic browser test; never writes to the public site."""
import pathlib, tempfile, shutil, threading, functools, http.server
import pipeline
from playwright.sync_api import sync_playwright
out=pipeline.WORK/"browser-results"
out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    root=pathlib.Path(tmp)
    shutil.copytree(pipeline.SITE/"assets",root/"assets")
    (root/"assets"/"fixture.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="640" height="360" fill="gray"/></svg>')
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=tmp))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    pipeline.BASE=f"http://127.0.0.1:{server.server_port}/"
    d={"title":"PRUEBA SINTÉTICA — NO PUBLICAR","cutoff_at":"2026-11-27T06:00:00-05:00","sections":[{"title":"Prueba","articles":[{"id":"test","title":"Institución de prueba","paragraphs":["Entidad ficticia para comprobar el diccionario."],"sources":[],"image":{"url":pipeline.BASE+"assets/fixture.svg","caption":"Imagen sintética","credit":"Prueba","license":"CC0","source":pipeline.BASE}}]}],"dictionary":[{"title":"Entidad ficticia","terms":["Entidad ficticia"],"text":"Definición sintética.","kind":"CONCEPTO","priority":"esencial"}]}
    (root/"index.html").write_text(pipeline.render(d,pipeline.BASE),encoding="utf-8")
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in (390,1280):
            page=browser.new_page(viewport={"width":width,"height":900})
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(pipeline.BASE)
            page.locator(".eog-term").first.click()
            assert page.locator("#eog-context-popover").is_visible()
            assert page.locator("#eog-context-popover").inner_text().find("Definición sintética.")>=0
            page.keyboard.press("Escape")
            assert not page.locator("#eog-context-popover").is_visible()
            assert page.locator("img").evaluate("(img)=>img.complete && img.naturalWidth>0")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert not errors,errors
            page.screenshot(path=str(out/f"fixture-{width}.png"),full_page=True)
            page.close()
        browser.close()
    server.shutdown()
