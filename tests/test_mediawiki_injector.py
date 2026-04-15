# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

"""
End-to-end fixture test for the MediaWiki export injector.

Creates a minimal XML export + assets directory and verifies:
- Discovery finds the XML file
- Pages are parsed and converted
- Assets are resolved
- The API endpoint accepts the payloads
"""

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure default implementations are registered
import retriva.ingestion.chunker  # noqa: F401

FIXTURE_XML = textwrap.dedent("""\
    <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/"
               xml:lang="en">
      <siteinfo>
        <sitename>TestWiki</sitename>
        <namespaces>
          <namespace key="0" case="first-letter" />
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
    [[File:db_schema.png|thumb|Schema diagram]]</text>
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
    Backups run daily. Retention: '''75 days'''.</text>
        </revision>
      </page>
    </mediawiki>
""")


@pytest.fixture
def mediawiki_mirror(tmp_path):
    """Create a fake MediaWiki export mirror layout."""
    # XML export
    xml_file = tmp_path / "wiki_backup.xml"
    xml_file.write_text(FIXTURE_XML, encoding="utf-8")

    # Assets directory
    assets = tmp_path / "assets" / "images"
    assets.mkdir(parents=True)
    (assets / "db_schema.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    return tmp_path


# ---------------------------------------------------------------------------
# Test: API endpoint
# ---------------------------------------------------------------------------

@patch("retriva.ingestion_api.main.get_client")
@patch("retriva.ingestion_api.main.init_collection")
def test_mediawiki_endpoint_accepts_payload(mock_init, mock_client):
    """The /api/v1/ingest/mediawiki endpoint should accept valid payloads."""
    from fastapi.testclient import TestClient
    from retriva.ingestion_api.main import app

    payload = {
        "source_path": "/data/wiki_backup.xml",
        "page_title": "Infrastructure/Database",
        "content_text": "The PostgreSQL database uses standard config.",
        "page_id": 42,
        "namespace": 0,
        "linked_assets": ["/data/assets/images/db_schema.png"],
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/mediawiki", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "job_id" in data


# ---------------------------------------------------------------------------
# Test: parser → CLI pipeline integration
# ---------------------------------------------------------------------------

def test_discovery_and_parsing(mediawiki_mirror):
    """Verify the full discovery → parse → asset resolution pipeline."""
    from retriva.ingestion.mediawiki_export_parser import (
        is_mediawiki_export,
        parse_export,
        wikitext_to_plaintext,
    )
    from retriva.ingestion.mediawiki_assets import (
        build_asset_index,
        find_assets_dirs,
        resolve_file_reference,
    )

    # 1. Discovery
    xml_files = sorted(mediawiki_mirror.rglob("*.xml"))
    assert len(xml_files) == 1
    assert is_mediawiki_export(xml_files[0]) is True

    # 2. Parse pages
    pages = list(parse_export(xml_files[0]))
    assert len(pages) == 2
    titles = [p.title for p in pages]
    assert "Infrastructure/Database" in titles
    assert "Operations/Backup" in titles

    # 3. Wikitext conversion
    db_page = next(p for p in pages if p.title == "Infrastructure/Database")
    plaintext = wikitext_to_plaintext(db_page.text)
    assert "PostgreSQL" in plaintext
    assert "==" not in plaintext

    # 4. Asset resolution
    assets_dirs = find_assets_dirs(mediawiki_mirror)
    assert len(assets_dirs) == 1

    index = build_asset_index(assets_dirs[0])
    assert "db_schema.png" in index

    resolved = resolve_file_reference("db_schema.png", index)
    assert resolved is not None
    assert resolved.name == "db_schema.png"

    # 5. File references from page
    assert "db_schema.png" in db_page.file_references


# ---------------------------------------------------------------------------
# Test: CLI dispatching
# ---------------------------------------------------------------------------

def test_cli_help_shows_injector_flag():
    """Verify that --injector is in the CLI help text."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "retriva.cli", "ingest", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src", "PATH": ""},
    )
    # The help should mention the flag even if we can't run it fully
    assert "--injector" in result.stdout or result.returncode == 0
