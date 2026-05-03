# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the MediaWiki asset resolver."""

from pathlib import Path
import pytest
from retriva.ingestion.mediawiki_assets import (
    build_asset_index,
    resolve_file_reference,
    find_assets_dirs,
    is_image_asset,
)


@pytest.fixture
def asset_tree(tmp_path):
    """Create a realistic assets/ subtree."""
    assets = tmp_path / "assets" / "images"
    assets.mkdir(parents=True)

    (assets / "db_schema.png").write_bytes(b"PNG")
    (assets / "er_model.jpg").write_bytes(b"JPG")
    (assets / "readme.txt").write_bytes(b"TXT")

    # Sub-hashed directory (MediaWiki style)
    sub = assets / "a"
    sub.mkdir()
    (sub / "architecture.png").write_bytes(b"PNG")

    return tmp_path / "assets"


class TestBuildAssetIndex:
    def test_indexes_all_files(self, asset_tree):
        index = build_asset_index(asset_tree)
        assert len(index) == 4
        assert "db_schema.png" in index
        assert "er_model.jpg" in index
        assert "readme.txt" in index
        assert "architecture.png" in index

    def test_keys_are_lowercase(self, asset_tree):
        # Create a file with mixed case
        (asset_tree / "MixedCase.PNG").write_bytes(b"PNG")
        index = build_asset_index(asset_tree)
        assert "mixedcase.png" in index

    def test_nonexistent_dir(self, tmp_path):
        index = build_asset_index(tmp_path / "nonexistent")
        assert index == {}


class TestResolveFileReference:
    def test_exact_match(self, asset_tree):
        index = build_asset_index(asset_tree)
        result = resolve_file_reference("db_schema.png", index)
        assert result is not None
        assert result.name == "db_schema.png"

    def test_case_insensitive(self, asset_tree):
        index = build_asset_index(asset_tree)
        result = resolve_file_reference("DB_Schema.PNG", index)
        assert result is not None
        assert result.name == "db_schema.png"

    def test_spaces_to_underscores(self, asset_tree):
        # MediaWiki may use spaces: "db schema.png" → "db_schema.png"
        (asset_tree / "with_space.png").write_bytes(b"PNG")
        index = build_asset_index(asset_tree)
        result = resolve_file_reference("with space.png", index)
        assert result is not None

    def test_not_found(self, asset_tree):
        index = build_asset_index(asset_tree)
        assert resolve_file_reference("nonexistent.png", index) is None


class TestFindAssetsDirs:
    def test_finds_assets_dirs(self, tmp_path):
        (tmp_path / "assets").mkdir()
        (tmp_path / "sub" / "assets").mkdir(parents=True)
        dirs = find_assets_dirs(tmp_path)
        assert len(dirs) == 2

    def test_empty_root(self, tmp_path):
        assert find_assets_dirs(tmp_path) == []


class TestIsImageAsset:
    def test_image_extensions(self):
        assert is_image_asset(Path("photo.jpg")) is True
        assert is_image_asset(Path("diagram.PNG")) is True
        assert is_image_asset(Path("icon.svg")) is True

    def test_non_image(self):
        assert is_image_asset(Path("document.pdf")) is False
        assert is_image_asset(Path("data.txt")) is False
