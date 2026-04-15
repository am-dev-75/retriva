# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

"""Tests for the MediaWiki XML export parser."""

import textwrap
from pathlib import Path
import pytest
from retriva.ingestion.mediawiki_export_parser import (
    WikiPage,
    is_mediawiki_export,
    parse_export,
    wikitext_to_plaintext,
    extract_file_references,
)


# ---------------------------------------------------------------------------
# Fixture: minimal MediaWiki XML export
# ---------------------------------------------------------------------------

FIXTURE_XML = textwrap.dedent("""\
    <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/"
               xml:lang="en">
      <siteinfo>
        <sitename>TestWiki</sitename>
        <namespaces>
          <namespace key="0" case="first-letter" />
          <namespace key="1" case="first-letter">Talk</namespace>
          <namespace key="6" case="first-letter">File</namespace>
        </namespaces>
      </siteinfo>

      <page>
        <title>Infrastructure/Database</title>
        <ns>0</ns>
        <id>42</id>
        <revision>
          <id>100</id>
          <timestamp>2026-03-15T10:22:00Z</timestamp>
          <text xml:space="preserve">== Overview ==
    The '''PostgreSQL''' database uses standard config.
    See [[Infrastructure/Networking|networking docs]] for details.
    [[File:db_schema.png|thumb|Schema diagram]]
    [[Image:er_model.jpg|frame|ER model]]</text>
        </revision>
      </page>

      <page>
        <title>Talk:Infrastructure/Database</title>
        <ns>1</ns>
        <id>43</id>
        <revision>
          <id>101</id>
          <timestamp>2026-03-16T08:00:00Z</timestamp>
          <text xml:space="preserve">This is a talk page discussion.</text>
        </revision>
      </page>

      <page>
        <title>File:db_schema.png</title>
        <ns>6</ns>
        <id>44</id>
        <revision>
          <id>102</id>
          <timestamp>2026-03-15T11:00:00Z</timestamp>
          <text xml:space="preserve">Database schema diagram for PostgreSQL 15.</text>
        </revision>
      </page>

      <page>
        <title>Operations/Backup</title>
        <ns>0</ns>
        <id>45</id>
        <revision>
          <id>103</id>
          <timestamp>2026-04-01T09:00:00Z</timestamp>
          <text xml:space="preserve">== Backup Policy ==
    Backups run daily at 02:00 UTC.
    Retention: '''75 days''' off-site.
    {{Warning|Do not delete backup archives manually}}
    &lt;ref name="ops-manual"&gt;Operations Manual, p.42&lt;/ref&gt;</text>
        </revision>
      </page>
    </mediawiki>
""")


@pytest.fixture
def xml_fixture(tmp_path):
    """Write the fixture XML to a temp file and return the path."""
    xml_file = tmp_path / "test_export.xml"
    xml_file.write_text(FIXTURE_XML, encoding="utf-8")
    return xml_file


# ---------------------------------------------------------------------------
# Tests: is_mediawiki_export
# ---------------------------------------------------------------------------

class TestIsMediaWikiExport:
    def test_valid_export(self, xml_fixture):
        assert is_mediawiki_export(xml_fixture) is True

    def test_non_mediawiki_xml(self, tmp_path):
        other = tmp_path / "other.xml"
        other.write_text("<root><item>hello</item></root>")
        assert is_mediawiki_export(other) is False

    def test_non_existent_file(self, tmp_path):
        missing = tmp_path / "missing.xml"
        assert is_mediawiki_export(missing) is False

    def test_html_file(self, tmp_path):
        html = tmp_path / "page.html"
        html.write_text("<html><body>Hello</body></html>")
        assert is_mediawiki_export(html) is False


# ---------------------------------------------------------------------------
# Tests: parse_export
# ---------------------------------------------------------------------------

class TestParseExport:
    def test_parses_main_and_file_namespaces(self, xml_fixture):
        """Default namespaces {0, 6} should yield 3 pages, skipping Talk (ns=1)."""
        pages = list(parse_export(xml_fixture))
        assert len(pages) == 3

        titles = [p.title for p in pages]
        assert "Infrastructure/Database" in titles
        assert "File:db_schema.png" in titles
        assert "Operations/Backup" in titles
        assert "Talk:Infrastructure/Database" not in titles

    def test_page_fields(self, xml_fixture):
        pages = list(parse_export(xml_fixture))
        db_page = next(p for p in pages if p.title == "Infrastructure/Database")
        assert db_page.namespace == 0
        assert db_page.page_id == 42
        assert db_page.timestamp == "2026-03-15T10:22:00Z"
        assert "PostgreSQL" in db_page.text

    def test_file_references_extracted(self, xml_fixture):
        pages = list(parse_export(xml_fixture))
        db_page = next(p for p in pages if p.title == "Infrastructure/Database")
        assert "db_schema.png" in db_page.file_references
        assert "er_model.jpg" in db_page.file_references

    def test_custom_namespaces(self, xml_fixture):
        """Passing namespaces={1} should only yield the Talk page."""
        pages = list(parse_export(xml_fixture, namespaces={1}))
        assert len(pages) == 1
        assert pages[0].title == "Talk:Infrastructure/Database"

    def test_empty_xml(self, tmp_path):
        empty = tmp_path / "empty.xml"
        empty.write_text(
            '<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">'
            "</mediawiki>"
        )
        pages = list(parse_export(empty))
        assert pages == []


# ---------------------------------------------------------------------------
# Tests: wikitext_to_plaintext
# ---------------------------------------------------------------------------

class TestWikitextToPlaintext:
    def test_headings(self):
        assert "Overview" in wikitext_to_plaintext("== Overview ==")
        assert "Deep" in wikitext_to_plaintext("==== Deep ====")
        # Should not contain '=' characters
        result = wikitext_to_plaintext("== Overview ==")
        assert "=" not in result

    def test_bold_italic_stripping(self):
        result = wikitext_to_plaintext("The '''PostgreSQL''' database uses ''standard'' config.")
        assert "PostgreSQL" in result
        assert "standard" in result
        assert "'''" not in result
        assert "''" not in result

    def test_wikilink_with_label(self):
        result = wikitext_to_plaintext("See [[Infrastructure/Net|networking docs]] for info.")
        assert "networking docs" in result
        assert "[[" not in result

    def test_wikilink_without_label(self):
        result = wikitext_to_plaintext("See [[Infrastructure]] page.")
        assert "Infrastructure" in result

    def test_template_removal(self):
        result = wikitext_to_plaintext("Before {{Warning|Do not delete}} after.")
        assert "Before" in result
        assert "after" in result
        assert "{{" not in result
        assert "}}" not in result

    def test_nested_template_removal(self):
        result = wikitext_to_plaintext("A {{outer|{{inner}}}} B")
        assert "A" in result
        assert "B" in result
        assert "{{" not in result

    def test_ref_removal(self):
        result = wikitext_to_plaintext('Text<ref name="x">citation</ref> more.')
        assert "Text" in result
        assert "more" in result
        assert "<ref" not in result
        assert "citation" not in result

    def test_html_tag_removal(self):
        result = wikitext_to_plaintext("<div>hello</div> <br/> world")
        assert "hello" in result
        assert "world" in result
        assert "<" not in result

    def test_category_removal(self):
        result = wikitext_to_plaintext("Content [[Category:Infrastructure]] end.")
        assert "Content" in result
        assert "Category" not in result

    def test_file_link_removal(self):
        result = wikitext_to_plaintext("Text [[File:image.png|thumb|Caption]] more.")
        assert "Text" in result
        assert "more" in result
        assert "File:" not in result

    def test_external_link_with_text(self):
        result = wikitext_to_plaintext("[https://example.com Example Site] is good.")
        assert "Example Site" in result
        assert "https://" not in result

    def test_magic_words(self):
        result = wikitext_to_plaintext("__TOC__\n__NOTOC__\nContent here.")
        assert "Content here" in result
        assert "__TOC__" not in result

    def test_full_page(self, xml_fixture):
        """Smoke test: parse + convert a real fixture page."""
        pages = list(parse_export(xml_fixture))
        db_page = next(p for p in pages if p.title == "Infrastructure/Database")
        plaintext = wikitext_to_plaintext(db_page.text)
        assert "PostgreSQL" in plaintext
        assert "networking docs" in plaintext
        assert "==" not in plaintext
        assert "'''" not in plaintext


# ---------------------------------------------------------------------------
# Tests: extract_file_references
# ---------------------------------------------------------------------------

class TestExtractFileReferences:
    def test_file_and_image(self):
        wikitext = (
            "[[File:diagram.png|thumb|A diagram]]\n"
            "[[Image:photo.jpg|frame|A photo]]\n"
        )
        refs = extract_file_references(wikitext)
        assert refs == ["diagram.png", "photo.jpg"]

    def test_deduplication(self):
        wikitext = (
            "[[File:same.png|thumb]]\n"
            "[[File:same.png|frame]]\n"
        )
        refs = extract_file_references(wikitext)
        assert refs == ["same.png"]

    def test_no_references(self):
        assert extract_file_references("Just normal text.") == []

    def test_mixed_case(self):
        refs = extract_file_references("[[file:lower.png|thumb]]")
        assert refs == ["lower.png"]
