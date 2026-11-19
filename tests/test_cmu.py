"""Offline tests for cmu.py. No network. Run: python3 -m unittest discover -s tests"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugins", "catch-me-up", "skills", "catch-me-up", "scripts"))
import cmu  # noqa: E402

NOW = 1_800_000_000


class Parsing(unittest.TestCase):
    def test_window(self):
        self.assertEqual(cmu.parse_window("6h"), 6 * 3600)
        self.assertEqual(cmu.parse_window("3d"), 3 * 86400)
        self.assertEqual(cmu.parse_window(" 1w "), 604800)
        for bad in ("", "24", "h", "0h", "2 months", "1y"):
            with self.assertRaises(ValueError):
                cmu.parse_window(bad)

    def test_numbers(self):
        self.assertEqual(cmu.to_number("1,406 views"), 1406)
        self.assertEqual(cmu.to_number("1.4K"), 1400)
        self.assertEqual(cmu.to_number("2.5M views"), 2_500_000)
        self.assertEqual(cmu.to_number(17), 17)
        self.assertEqual(cmu.to_number("No views"), 0)
        self.assertEqual(cmu.to_number(None), 0)
        self.assertEqual(cmu.to_number(True), 0)

    def test_relative_times(self):
        self.assertEqual(cmu.ago_to_epoch("2h ago", NOW), NOW - 7200)
        self.assertEqual(cmu.ago_to_epoch("15 hours ago", NOW), NOW - 54000)
        self.assertEqual(cmu.ago_to_epoch("Streamed 3 days ago", NOW), NOW - 259200)
        self.assertEqual(cmu.ago_to_epoch("5 min ago", NOW), NOW - 300)
        self.assertEqual(cmu.ago_to_epoch("1mo ago", NOW), NOW - 2592000)
        self.assertEqual(cmu.ago_to_epoch("1 month ago", NOW), NOW - 2592000)
        self.assertEqual(cmu.ago_to_epoch("2w ago", NOW), NOW - 1209600)
        self.assertIsNone(cmu.ago_to_epoch("LIVE", NOW))
        self.assertIsNone(cmu.ago_to_epoch(None, NOW))

    def test_dates(self):
        self.assertEqual(cmu.iso_to_epoch("2026-11-19T00:00:00Z"), cmu.iso_to_epoch("2026-11-19T00:00:00+00:00"))
        self.assertEqual(cmu.iso_to_epoch("Thu, 19 Nov 2026 00:00:00 GMT"), cmu.iso_to_epoch("2026-11-19T00:00:00Z"))
        self.assertIsNotNone(cmu.iso_to_epoch("2026-11-19T22:40:05.735Z"))
        self.assertIsNone(cmu.iso_to_epoch("soon"))
        self.assertIsNone(cmu.iso_to_epoch(None))

    def test_links(self):
        self.assertEqual(cmu.canonical("https://www.twitter.com/a/status/1?s=20"), "x.com/a/status/1")
        self.assertEqual(cmu.canonical("https://youtube.com/watch?v=abc&utm_source=x"), "youtube.com/watch?v=abc")
        self.assertEqual(cmu.canonical("http://example.com/a/"), cmu.canonical("https://www.example.com/a"))

    def test_clean_strips_markup_and_trims(self):
        self.assertEqual(cmu.clean("<p>Hello &amp; <b>bye</b></p>\n\n now"), "Hello & bye now")
        self.assertEqual(len(cmu.clean("x" * 900)), 300)

    def test_slug(self):
        self.assertEqual(cmu.slugify("GTA 6: Easter Eggs!"), "gta-6-easter-eggs")
        self.assertEqual(cmu.slugify("???"), "topic")


class YouTube(unittest.TestCase):
    PAGE = ('<script>var ytInitialData = {"contents":[{"videoRenderer":{"videoId":"v1",'
            '"title":{"runs":[{"text":"First look"}]},"ownerText":{"runs":[{"text":"Chan"}]},'
            '"publishedTimeText":{"simpleText":"2h ago"},"viewCountText":{"simpleText":"1,406 views"}}},'
            '{"videoRenderer":{"title":{"runs":[{"text":"no id"}]}}}]};</script>')

    def test_rows(self):
        rows = cmu.youtube_rows(self.PAGE, NOW)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row["text"], row["author"], row["views"]), ("First look", "Chan", 1406))
        self.assertEqual(row["url"], "https://www.youtube.com/watch?v=v1")
        self.assertEqual(row["created"], NOW - 7200)
        self.assertTrue(row["approx_time"])

    def test_changed_layout_is_a_skip(self):
        with self.assertRaises(cmu.Skip):
            cmu.youtube_rows("<html>nothing here</html>", NOW)


class Sorting(unittest.TestCase):
    def rows(self):
        return [
            cmu.post("hackernews", "https://example.com/a", "A brand new launch that everyone is talking about",
                     created=NOW - 60, likes=90, comments=40),
            cmu.post("news", "https://example.com/a/", "Same link from a news site", created=NOW - 60),
            cmu.post("bluesky", "https://b.example/1", "A brand new launch that everyone is talking about!",
                     created=NOW - 60, likes=2),
            cmu.post("bluesky", "https://b.example/2", "An unrelated post about lunch", created=NOW - 9000, likes=1),
            cmu.post("news", "https://old.example", "ancient history", created=NOW - 10 ** 7),
            cmu.post("x*", "https://x.com/u/status/9", "undated find from web search"),
        ]

    def test_window_keeps_undated_and_drops_old(self):
        kept, old = cmu.in_window(self.rows(), NOW - 86400)
        self.assertEqual((len(kept), old), (5, 1))

    def test_duplicates_fold_and_note_other_sources(self):
        kept, _ = cmu.in_window(self.rows(), NOW - 86400)
        unique, dupes = cmu.fold_duplicates(kept)
        self.assertEqual((len(unique), dupes), (3, 2))
        top = [r for r in unique if r["source"] == "hackernews"][0]
        self.assertEqual(sorted(top["also_on"]), ["bluesky", "news"])

    def test_scores_are_bounded_and_ordered(self):
        kept, _ = cmu.in_window(self.rows(), NOW - 86400)
        unique, _ = cmu.fold_duplicates(kept)
        ranked = cmu.score(unique, NOW - 86400, NOW)
        self.assertEqual(ranked[0]["source"], "hackernews")
        scores = [r["score"] for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(0 <= s <= 100 for s in scores))

    def test_every_source_gets_shown(self):
        loud = [dict(cmu.post("youtube", "https://y.example/%d" % i, "video %d" % i), score=90 - i) for i in range(30)]
        quiet = [dict(cmu.post("news", "https://n.example/%d" % i, "headline %d" % i), score=20 - i) for i in range(8)]
        shown = cmu.pick(loud + quiet, 20)
        self.assertEqual(len(shown), 20)
        self.assertEqual(sum(r["source"] == "news" for r in shown), 5)
        self.assertEqual(cmu.pick(quiet, 20), quiet)

    def test_low_numbers_do_not_outrank_big_ones(self):
        tiny = cmu.post("mastodon", "https://m.example/1", "a small post nobody saw", created=NOW - 600, comments=6)
        tiny2 = cmu.post("mastodon", "https://m.example/2", "another quiet post entirely", created=NOW - 900, likes=1)
        big = cmu.post("youtube", "https://y.example/big", "the huge video everyone watched", created=NOW - 60000, views=1_900_000)
        big2 = cmu.post("youtube", "https://y.example/b2", "a second very large video here", created=NOW - 50000, views=2_800_000)
        unique, _ = cmu.fold_duplicates([tiny, tiny2, big, big2])
        ranked = cmu.score(unique, NOW - 86400, NOW)
        self.assertEqual({r["source"] for r in ranked[:2]}, {"youtube"})

    def test_posts_that_name_the_topic_rank_higher(self):
        on = cmu.post("bluesky", "https://b.example/on", "Vice City map leak for GTA 6 looks real", created=NOW - 600, likes=12)
        off = cmu.post("bluesky", "https://b.example/off", "A hedge fund bought a newspaper chain today", created=NOW - 600, likes=12)
        unique, _ = cmu.fold_duplicates([off, on])
        ranked = cmu.score(unique, NOW - 86400, NOW, ["GTA 6"])
        self.assertEqual(ranked[0]["url"], "https://b.example/on")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_empty_feed(self):
        self.assertEqual(cmu.score([], NOW - 3600, NOW), [])
        self.assertEqual(cmu.fold_duplicates([]), ([], 0))


class Searches(unittest.TestCase):
    def test_one_failed_search_does_not_sink_the_source(self):
        def youtube(q):
            if q == "bad":
                raise cmu.Skip("failed (search page not readable)")
            return [cmu.post("youtube", "https://y.example/" + q, q)]
        opts = {}
        with mock.patch.object(cmu.time, "sleep"):
            rows = cmu.per_search(["a", "bad", "b"], youtube, opts, tries=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(opts["partial"]["youtube"], "1 of 3 searches failed")
        with self.assertRaises(cmu.Skip):
            cmu.per_search(["bad", "bad"], youtube, {})

    def test_retry_recovers(self):
        calls = []

        def youtube(q):
            calls.append(q)
            if len(calls) == 1:
                raise cmu.Skip("failed (search page not readable)")
            return [cmu.post("youtube", "https://y.example/1", "ok")]
        opts = {}
        with mock.patch.object(cmu.time, "sleep"):
            self.assertEqual(len(cmu.per_search(["a"], youtube, opts, tries=2)), 1)
        self.assertNotIn("partial", opts)

    def test_site_of(self):
        self.assertEqual(cmu.site_of("https://www.example.com/a/b"), "example.com")
        self.assertEqual(cmu.site_of(None), "")


class EndToEnd(unittest.TestCase):
    """Runs the scroll command with fake sources, in a temporary home folder."""

    def run_scroll(self, home, argv, fake):
        out = io.StringIO()
        with mock.patch.object(cmu, "HOME", home), mock.patch.dict(cmu.FETCHERS, fake, clear=True), redirect_stdout(out):
            code = cmu.main(["scroll"] + argv)
        return code, out.getvalue()

    def test_memory_extra_and_failures(self):
        import time
        now = time.time()

        def good(queries, since, span, opts):
            return [cmu.post("hackernews", "https://example.com/one", "The first thing happened", created=now - 100, likes=5),
                    cmu.post("hackernews", "https://example.com/old", "Too old", created=now - 10 ** 6)]

        def blocked(queries, since, span, opts):
            raise cmu.Skip("blocked (HTTP 403)")

        def broken(queries, since, span, opts):
            raise KeyError("format changed")

        fake = {"hackernews": good, "reddit": blocked, "youtube": broken}
        with tempfile.TemporaryDirectory() as home:
            extra = os.path.join(home, "extra.json")
            with open(extra, "w") as fh:
                json.dump([{"source": "X", "url": "https://x.com/a/status/1", "text": "found by search"},
                           {"nothing": "useful"}], fh)
            args = ["--topic", "Test Topic", "--sources", "hackernews,reddit,youtube", "--extra", extra]
            code, text = self.run_scroll(home, args, fake)
            self.assertEqual(code, 0)
            self.assertIn("reddit blocked (HTTP 403)", text)
            self.assertIn("youtube failed (KeyError)", text)
            self.assertIn("1 too old", text)
            self.assertIn("x* ·", text)
            self.assertIn("https://example.com/one", text)
            self.assertNotIn("https://example.com/old", text)
            self.assertTrue(os.path.exists(os.path.join(home, "seen", "test-topic.json")))

            _, again = self.run_scroll(home, args, fake)
            self.assertIn("0 posts collected", again)
            self.assertIn("2 already shown", again)

            _, fresh = self.run_scroll(home, args + ["--fresh"], fake)
            self.assertIn("2 posts collected", fresh)

            with mock.patch.object(cmu, "HOME", home), redirect_stdout(io.StringIO()):
                cmu.main(["forget", "--topic", "Test Topic"])
            self.assertFalse(os.path.exists(os.path.join(home, "seen", "test-topic.json")))

    def test_bad_input_exits(self):
        with tempfile.TemporaryDirectory() as home:
            for argv in (["--topic", "t", "--since", "soon"], ["--topic", "t", "--sources", "myspace"]):
                with self.assertRaises(SystemExit):
                    self.run_scroll(home, argv, {"hackernews": lambda *a: []})


if __name__ == "__main__":
    unittest.main()
