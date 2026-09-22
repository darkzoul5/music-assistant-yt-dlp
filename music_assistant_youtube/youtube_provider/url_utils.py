"""YouTube URL parsing helpers."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def resolve_youtube_search_target(search_query: str) -> tuple[str, str] | None:
    """Return the direct YouTube media target for a URL-like search query.

    Returns a tuple of ``(target_type, target_id)`` where ``target_type`` is
    ``"track"`` for videos and ``"playlist"`` for playlists.
    """
    raw_query = search_query.strip()
    if not raw_query:
        return None
    normalized = raw_query
    if not urlparse(raw_query).scheme and raw_query.startswith(
        ("youtube.com/", "www.youtube.com/", "m.youtube.com/", "youtu.be/")
    ):
        normalized = f"https://{raw_query}"
    parsed = urlparse(normalized)
    host = parsed.netloc.lower().split(":", 1)[0]
    query_params = parse_qs(parsed.query)
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        path = parsed.path.rstrip("/")
        if path == "/watch":
            video_id = query_params.get("v", [""])[0]
            if video_id:
                return "track", video_id
        if path == "/playlist":
            playlist_id = query_params.get("list", [""])[0]
            if playlist_id:
                return "playlist", playlist_id
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0]
        if video_id:
            return "track", video_id
    return None