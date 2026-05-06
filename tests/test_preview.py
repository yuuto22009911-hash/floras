"""Preview server tests."""

from __future__ import annotations

import threading
import time
import urllib.parse
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

from floras.preview import PreviewServer

SAMPLE_BLOOM = (
    "花 さくら { 花弁数 5; 大きさ 200; 色 知覚色(0.85 0.10 12); }\n"
)


@pytest.fixture
def preview_dir(tmp_path: Path) -> Path:
    (tmp_path / "さくら.bloom").write_text(SAMPLE_BLOOM, encoding="utf-8")
    return tmp_path


@pytest.fixture
def server(preview_dir: Path) -> Iterator[PreviewServer]:
    srv = PreviewServer(preview_dir, port=0, poll_interval=0.05)
    srv.start()
    yield srv
    srv.stop()


def _get(url: str, *, timeout: float = 2.0) -> str:
    # Percent-encode any non-ASCII characters in the path so urllib.request
    # can send the URL over the wire. Equivalent to a browser's encodeURI.
    parts = urllib.parse.urlsplit(url)
    quoted_path = urllib.parse.quote(parts.path, safe="/")
    encoded = urllib.parse.urlunsplit(parts._replace(path=quoted_path))
    with urllib.request.urlopen(encoded, timeout=timeout) as resp:
        body: bytes = resp.read()
    return body.decode("utf-8")


def test_gallery_root_serves_html_with_card(server: PreviewServer) -> None:
    body = _get(f"http://127.0.0.1:{server.port}/")
    assert "<title>floras preview" in body
    assert 'data-file="さくら.bloom"' in body


def test_svg_endpoint_returns_an_svg(server: PreviewServer) -> None:
    body = _get(
        f"http://127.0.0.1:{server.port}/svg/さくら.bloom"
    )
    assert body.startswith("<svg ")


def test_unknown_file_returns_error_svg_not_500(server: PreviewServer) -> None:
    body = _get(f"http://127.0.0.1:{server.port}/svg/missing.bloom")
    assert body.startswith("<svg ")
    assert "file not found" in body


def test_sse_emits_change_event_when_file_modified(
    preview_dir: Path, server: PreviewServer
) -> None:
    received: list[bytes] = []
    done = threading.Event()

    def reader() -> None:
        url = f"http://127.0.0.1:{server.port}/events"
        try:
            with urllib.request.urlopen(url, timeout=5.0) as resp:
                while not done.is_set():
                    chunk = resp.fp.readline()
                    if not chunk:
                        break
                    received.append(chunk)
                    if b"event: change" in chunk:
                        # Read the data line that follows.
                        data = resp.fp.readline()
                        received.append(data)
                        return
        except Exception:
            pass

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    # Give the SSE handler a moment to subscribe before we mutate.
    time.sleep(0.2)

    target = preview_dir / "さくら.bloom"
    target.write_text(SAMPLE_BLOOM + "※ touched\n", encoding="utf-8")

    t.join(timeout=4.0)
    done.set()

    blob = b"".join(received)
    assert b"event: change" in blob, blob
    assert b"\xe3\x81\x95\xe3\x81\x8f\xe3\x82\x89.bloom" in blob, blob


def test_render_error_in_bloom_renders_error_svg_not_500(
    preview_dir: Path, server: PreviewServer
) -> None:
    (preview_dir / "壊れた.bloom").write_text("花 桜 {", encoding="utf-8")
    # Wait briefly for the watcher to pick up the new file.
    time.sleep(0.2)
    body = _get(f"http://127.0.0.1:{server.port}/svg/壊れた.bloom")
    assert body.startswith("<svg ")
    # It should be the red error SVG, not blank.
    assert "Floras" in body


def test_directory_not_found_raises() -> None:
    srv = PreviewServer(Path("/nonexistent-floras-preview-dir"), port=0)
    with pytest.raises(FileNotFoundError):
        srv.start()


def test_port_collision_falls_back_to_next_port(
    preview_dir: Path,
) -> None:
    a = PreviewServer(preview_dir, port=7878, poll_interval=1.0)
    a.start()
    try:
        b = PreviewServer(preview_dir, port=7878, poll_interval=1.0)
        b.start()
        try:
            assert b.port != a.port
        finally:
            b.stop()
    finally:
        a.stop()
