"""Unit tests for YouTube provider search URL resolution."""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from unittest.mock import AsyncMock, Mock

import pytest

music_assistant = ModuleType("music_assistant")
music_assistant.__path__ = []
music_assistant_constants = ModuleType("music_assistant.constants")
music_assistant_constants.VERBOSE_LOG_LEVEL = 5
music_assistant_controllers = ModuleType("music_assistant.controllers")
music_assistant_controllers.__path__ = []
music_assistant_cache = ModuleType("music_assistant.controllers.cache")


def use_cache(*args, **kwargs):
    """Return the wrapped function unchanged for unit tests."""

    def decorator(func):
        return func

    return decorator


music_assistant_cache.use_cache = use_cache
music_assistant_helpers = ModuleType("music_assistant.helpers")
music_assistant_helpers.__path__ = []
music_assistant_process = ModuleType("music_assistant.helpers.process")
music_assistant_util = ModuleType("music_assistant.helpers.util")
music_assistant_models = ModuleType("music_assistant.models")
music_assistant_models.__path__ = []
music_assistant_music_provider = ModuleType("music_assistant.models.music_provider")


class MusicProvider:
    """Minimal stand-in for the Music Assistant base provider."""


async def check_output(*args, **kwargs):
    return 0, b""


async def install_package(*args, **kwargs):
    return None


music_assistant_process.check_output = check_output
music_assistant_util.install_package = install_package
music_assistant_music_provider.MusicProvider = MusicProvider
music_assistant.controllers = music_assistant_controllers
music_assistant.constants = music_assistant_constants
music_assistant.helpers = music_assistant_helpers
music_assistant.models = music_assistant_models
music_assistant_controllers.cache = music_assistant_cache
music_assistant_helpers.process = music_assistant_process
music_assistant_helpers.util = music_assistant_util
music_assistant_models.music_provider = music_assistant_music_provider
sys.modules.setdefault("music_assistant", music_assistant)
sys.modules.setdefault("music_assistant.constants", music_assistant_constants)
sys.modules.setdefault("music_assistant.controllers", music_assistant_controllers)
sys.modules.setdefault("music_assistant.controllers.cache", music_assistant_cache)
sys.modules.setdefault("music_assistant.helpers", music_assistant_helpers)
sys.modules.setdefault("music_assistant.helpers.process", music_assistant_process)
sys.modules.setdefault("music_assistant.helpers.util", music_assistant_util)
sys.modules.setdefault("music_assistant.models", music_assistant_models)
sys.modules.setdefault("music_assistant.models.music_provider", music_assistant_music_provider)

from music_assistant_models.enums import MediaType

from music_assistant_youtube.youtube_provider.parsers import parse_playlist, parse_track
from music_assistant_youtube.youtube_provider.provider import YouTubeProvider


@pytest.fixture
def provider() -> YouTubeProvider:
    """Create a minimal provider instance for search tests."""
    instance = object.__new__(YouTubeProvider)
    instance.domain = "youtube"
    instance.instance_id = "test_instance"
    instance.mass = Mock()
    instance.mass.http_session = Mock()
    instance.logger = Mock()
    return instance


def run_search(
    provider: YouTubeProvider,
    search_query: str,
    media_types: list[MediaType],
    limit: int = 5,
):
    """Run the undecorated search implementation."""
    search_impl = getattr(YouTubeProvider.search, "__wrapped__", YouTubeProvider.search)
    return asyncio.run(search_impl(provider, search_query, media_types, limit))


def test_search_video_url_resolves_track(provider: YouTubeProvider) -> None:
    """A YouTube watch URL should resolve a single track, not a playlist."""
    track = parse_track(
        {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
        },
        provider.domain,
        provider.instance_id,
    )
    provider.get_track = AsyncMock(return_value=track)
    provider.get_playlist = AsyncMock(side_effect=AssertionError("playlist lookup was used"))
    provider._search_videos = AsyncMock(side_effect=AssertionError("text search was used"))
    provider._search_playlists = AsyncMock(side_effect=AssertionError("text search was used"))

    result = run_search(
        provider,
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123&t=42",
        [MediaType.TRACK, MediaType.PLAYLIST],
    )

    assert [item.item_id for item in result.tracks] == ["dQw4w9WgXcQ"]
    assert result.playlists == []
    provider.get_track.assert_awaited_once_with("dQw4w9WgXcQ")
    provider.get_playlist.assert_not_called()


def test_search_playlist_url_resolves_playlist(provider: YouTubeProvider) -> None:
    """A YouTube playlist URL should resolve a single playlist."""
    playlist = parse_playlist(
        {
            "id": "PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz",
            "title": "Playlist Title",
            "channel": "Channel Name",
        },
        provider.domain,
        provider.instance_id,
    )
    provider.get_playlist = AsyncMock(return_value=playlist)
    provider.get_track = AsyncMock(side_effect=AssertionError("track lookup was used"))
    provider._search_videos = AsyncMock(side_effect=AssertionError("text search was used"))
    provider._search_playlists = AsyncMock(side_effect=AssertionError("text search was used"))

    result = run_search(
        provider,
        "https://www.youtube.com/playlist?list=PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz&feature=share",
        [MediaType.TRACK, MediaType.PLAYLIST],
    )

    assert result.tracks == []
    assert [item.item_id for item in result.playlists] == ["PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz"]
    provider.get_playlist.assert_awaited_once_with("PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz")
    provider.get_track.assert_not_called()


def test_search_text_query_still_uses_text_search(provider: YouTubeProvider) -> None:
    """Plain text queries should keep using the existing search helpers."""
    provider.get_track = AsyncMock(side_effect=AssertionError("direct lookup was used"))
    provider.get_playlist = AsyncMock(side_effect=AssertionError("direct lookup was used"))
    provider._search_videos = AsyncMock(
        return_value=[
            {
                "id": "dQw4w9WgXcQ",
                "title": "Never Gonna Give You Up",
                "uploader": "Rick Astley",
            }
        ]
    )
    provider._search_playlists = AsyncMock(
        return_value=[
            {
                "id": "PL1234567890",
                "title": "Playlist Title",
                "channel": "Channel Name",
            }
        ]
    )

    result = run_search(
        provider,
        "never gonna give you up",
        [MediaType.TRACK, MediaType.PLAYLIST],
    )

    assert [item.item_id for item in result.tracks] == ["dQw4w9WgXcQ"]
    assert [item.item_id for item in result.playlists] == ["PL1234567890"]
    provider._search_videos.assert_awaited_once_with("never gonna give you up", 5)
    provider._search_playlists.assert_awaited_once_with("never gonna give you up", 5)


def test_search_video_url_with_list_param_does_not_resolve_as_playlist(
    provider: YouTubeProvider,
) -> None:
    """A watch URL with list parameters should still be treated as a video URL."""
    provider.get_track = AsyncMock(side_effect=AssertionError("track lookup was used"))
    provider.get_playlist = AsyncMock(side_effect=AssertionError("playlist lookup was used"))
    provider._search_videos = AsyncMock(side_effect=AssertionError("text search was used"))
    provider._search_playlists = AsyncMock(side_effect=AssertionError("text search was used"))

    result = run_search(
        provider,
        "https://www.youtube.com/watch?v=7t_ohlqvtaI&list=PLUmRr21IDW9WCW87FnbWAbIwwZHbf-lAz&index=1&pp=iAQB8AUBsAgC",
        [MediaType.PLAYLIST],
    )

    assert result.tracks == []
    assert result.playlists == []
    provider.get_track.assert_not_called()
    provider.get_playlist.assert_not_called()
