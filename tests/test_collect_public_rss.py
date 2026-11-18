import unittest
from scripts.collect_public_rss import parse_feed, parse_datetime, stable_id


class PublicRssTests(unittest.TestCase):
    def test_parses_rss_and_cleans_html(self):
        xml = b'''<?xml version="1.0"?><rss version="2.0"><channel><item>
        <title>Local report</title><link>https://example.org/story/1</link>
        <guid>story-1</guid><pubDate>Wed, 18 Nov 2026 10:00:00 GMT</pubDate>
        <description>&lt;p&gt;Workers &amp;amp; police&lt;/p&gt;</description>
        </item></channel></rss>'''
        items = parse_feed(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Local report")
        self.assertEqual(items[0]["url"], "https://example.org/story/1")
        self.assertIn("Workers", items[0]["summary"])
        self.assertIsNotNone(items[0]["_published_dt"])

    def test_parses_atom_link_and_iso_date(self):
        xml = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
        <title>Regional update</title><link rel="alternate" href="https://example.org/a"/>
        <id>tag:example.org,2026:a</id><updated>2026-11-18T10:00:00Z</updated>
        <summary>Short summary</summary></entry></feed>'''
        items = parse_feed(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.org/a")
        self.assertTrue(items[0]["published_utc"].startswith("2026-11-18"))

    def test_stable_id_uses_source_and_guid(self):
        item = {"guid": "abc", "url": "https://example.org/a"}
        self.assertEqual(stable_id("publisher", item), stable_id("publisher", item))
        self.assertTrue(stable_id("publisher", item).startswith("publisher:"))


    def test_recovers_unescaped_ampersand_in_feed_text(self):
        xml = b'''<rss><channel><item><title>Workers &amp; police</title>
        <link>https://example.org/amp</link><guid>amp-1</guid>
        <pubDate>Wed, 18 Nov 2026 10:00:00 GMT</pubDate>
        <description>Workers & police response</description></item></channel></rss>'''
        items = parse_feed(xml)
        self.assertEqual(len(items), 1)
        self.assertIn("Workers", items[0]["summary"])

    def test_invalid_date_is_not_fabricated(self):
        self.assertIsNone(parse_datetime("not-a-date"))


if __name__ == "__main__":
    unittest.main()
