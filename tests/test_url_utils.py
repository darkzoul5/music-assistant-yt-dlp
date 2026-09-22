"""Unit tests for YouTube URL parsing helpers."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_url_utils_module():
    module_path = Path(__file__).resolve().parents[1] / "music_assistant_youtube" / "youtube_provider" / "url_utils.py"
    spec = spec_from_file_location("url_utils_test_module", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


resolve_youtube_search_target = _load_url_utils_module().resolve_youtube_search_target


def test_resolve_video_url() -> None:
    """Resolve a standard YouTube video URL."""
    assert resolve_youtube_search_target(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ) == ("track", "dQw4w9WgXcQ")


def test_resolve_playlist_url() -> None:
    """Resolve a standard YouTube playlist URL."""
    assert resolve_youtube_search_target(
        "https://www.youtube.com/playlist?list=PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz"
    ) == ("playlist", "PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz")


def test_resolve_video_url_with_list_param() -> None:
    """Do not treat a watch URL with list parameters as a playlist URL."""
    assert resolve_youtube_search_target(
        "https://www.youtube.com/watch?v=7t_ohlqvtaI&list=PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz&index=1&pp=iAQB8AUBsAgC"
    ) == ("track", "7t_ohlqvtaI")


def test_resolve_shortened_video_url() -> None:
    """Resolve a shortened youtu.be video URL."""
    assert resolve_youtube_search_target("https://youtu.be/dQw4w9WgXcQ?t=42") == (
        "track",
        "dQw4w9WgXcQ",
    )


def test_resolve_text_query_returns_none() -> None:
    """Non-URL text should not be treated as a direct media target."""
    assert resolve_youtube_search_target("never gonna give you up") is None