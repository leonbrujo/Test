import unittest, pipeline, json
class TestPipeline(unittest.TestCase):
    def test_render(self):
        d={"title":"Prueba & control","cutoff_at":"2026-11-27T06:00:00-05:00","sections":[{"title":"Noticias","articles":[{"id":"test","title":"<test>","paragraphs":["Texto & datos"],"sources":[]}]}],"dictionary":[{"text":"</script>"}]}
        result=pipeline.render(d,pipeline.BASE)
        self.assertIn("&lt;test&gt;",result)
        self.assertIn("contexto.js?v=2",result)
        self.assertIn("contexto.css?v=1",result)
        self.assertIn("\\u003c/script>",result)
    def test_reject_unverified(self):
        with self.assertRaises(AssertionError):
            pipeline.validate({"date":"2026-11-27","cutoff_at":"2026-11-27T06:00:00-05:00","verification":"partial"})
