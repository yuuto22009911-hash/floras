"""Local preview server with file-watch-based live reload.

`floras preview <dir>` serves an HTML gallery of every `.bloom` file in the
given directory. The server watches the directory by polling mtimes once per
``poll_interval`` seconds and pushes Server-Sent Events to any connected
browser, which swaps the matching ``<svg>`` in place without a full reload.

The implementation only uses Python's standard library so the package keeps
its zero-dependency promise.
"""

from __future__ import annotations

import html
import json
import socket
import sys
import threading
import time
import urllib.parse
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue
from typing import Any

import floras
from floras.errors import FlorasError

_DEFAULT_PORT = 7878
_PORT_RETRY = 10
_BROADCAST_TIMEOUT = 0.5


class _Watcher(threading.Thread):
    """Polls the watched directory for `.bloom` mtime changes."""

    def __init__(
        self,
        directory: Path,
        on_change: Callable[[str, bool], None],
        poll_interval: float,
    ) -> None:
        super().__init__(daemon=True)
        self.directory = directory
        self.on_change = on_change
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._mtimes: dict[str, float] = {}
        # Seed the initial state so the first iteration doesn't fire spurious
        # change events for files that already exist.
        for path in self._iter_blooms():
            self._mtimes[path.name] = path.stat().st_mtime

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                self._scan_once()
            except Exception:  # pragma: no cover - watcher must keep running
                pass
            self._stop.wait(self.poll_interval)

    def _iter_blooms(self) -> list[Path]:
        if not self.directory.is_dir():
            return []
        return sorted(self.directory.glob("*.bloom"))

    def _scan_once(self) -> None:
        current: dict[str, float] = {}
        for path in self._iter_blooms():
            current[path.name] = path.stat().st_mtime
        # Removed files
        for name in set(self._mtimes) - set(current):
            self.on_change(name, True)
        # New / modified files
        for name, mtime in current.items():
            if self._mtimes.get(name) != mtime:
                self.on_change(name, False)
        self._mtimes = current


class PreviewServer:
    """An HTTP + SSE server that serves a live gallery of `.bloom` files."""

    def __init__(
        self,
        directory: Path,
        port: int = _DEFAULT_PORT,
        *,
        poll_interval: float = 1.0,
    ) -> None:
        self.directory = Path(directory).resolve()
        self.requested_port = port
        self.poll_interval = poll_interval
        self.port: int = 0
        self._subscribers: list[Queue[dict[str, Any]]] = []
        self._lock = threading.Lock()
        self._http: ThreadingHTTPServer | None = None
        self._watcher: _Watcher | None = None
        self._http_thread: threading.Thread | None = None

    # ------- lifecycle ------------------------------------------------------

    def start(self) -> None:
        if self._http is not None:
            return
        if not self.directory.is_dir():
            raise FileNotFoundError(f"directory not found: {self.directory}")

        handler_cls = self._build_handler()
        self._http, self.port = _bind_server(self.requested_port, handler_cls)
        self._http_thread = threading.Thread(
            target=self._http.serve_forever, daemon=True, name="floras-preview-http"
        )
        self._http_thread.start()

        self._watcher = _Watcher(
            self.directory, self._broadcast_change, self.poll_interval
        )
        self._watcher.start()

    def stop(self) -> None:
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None
        if self._http is not None:
            self._http.shutdown()
            self._http.server_close()
            self._http = None

    # ------- broadcast ------------------------------------------------------

    def _broadcast_change(self, name: str, removed: bool) -> None:
        event: dict[str, Any] = {"file": name, "removed": removed}
        with self._lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(event)
                except Exception:  # pragma: no cover - subscriber backpressure
                    pass

    def _subscribe(self) -> Queue[dict[str, Any]]:
        q: Queue[dict[str, Any]] = Queue()
        with self._lock:
            self._subscribers.append(q)
        return q

    def _unsubscribe(self, q: Queue[dict[str, Any]]) -> None:
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    # ------- rendering ------------------------------------------------------

    def list_blooms(self) -> list[Path]:
        return sorted(self.directory.glob("*.bloom"))

    def render_gallery(self) -> str:
        cards: list[str] = []
        for path in self.list_blooms():
            cards.append(self._card(path))
        return _GALLERY_TEMPLATE.format(
            title=html.escape(self.directory.name),
            cards="\n".join(cards),
        )

    def render_one(self, name: str) -> str:
        path = self.directory / name
        if not path.is_file():
            return _error_svg(f"file not found: {name}")
        try:
            return floras.render(path.read_text(encoding="utf-8"))
        except FlorasError as exc:
            return _error_svg(str(exc))
        except Exception as exc:  # pragma: no cover
            return _error_svg(f"unexpected error: {exc}")

    def _card(self, path: Path) -> str:
        try:
            svg = floras.render(path.read_text(encoding="utf-8"))
            error_class = ""
            error_html = ""
        except FlorasError as exc:
            svg = ""
            error_class = " has-error"
            error_html = (
                f'<pre class="error">{html.escape(str(exc))}</pre>'
            )
        slug = path.name
        return (
            f'<figure class="card{error_class}" data-file="{html.escape(slug)}">\n'
            f'  <div class="preview" data-file="{html.escape(slug)}">{svg}</div>\n'
            f'  {error_html}'
            f'  <figcaption>{html.escape(path.stem)}'
            f'<code>{html.escape(slug)}</code></figcaption>\n'
            f'</figure>'
        )

    # ------- handler --------------------------------------------------------

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:  # noqa: A002
                # Quiet by default — preview runs as a foreground tool and the
                # default access log clutters the terminal.
                return

            def do_GET(self) -> None:  # noqa: N802
                # Drop any query string and percent-decode the path so callers
                # can request files whose names contain non-ASCII characters.
                path = urllib.parse.urlsplit(self.path).path
                path = urllib.parse.unquote(path)
                if path == "/" or path == "/index.html":
                    self._send_html(server.render_gallery())
                elif path == "/events":
                    self._send_sse(server)
                elif path.startswith("/svg/"):
                    name = path[len("/svg/") :]
                    self._send_svg(server.render_one(name))
                else:
                    self.send_error(404)

            def _send_html(self, body: str) -> None:
                payload = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)

            def _send_svg(self, body: str) -> None:
                payload = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)

            def _send_sse(self, srv: PreviewServer) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                queue = srv._subscribe()
                try:
                    self.wfile.write(b"retry: 1500\n\n")
                    self.wfile.flush()
                    while True:
                        try:
                            event = queue.get(timeout=15.0)
                        except Empty:
                            # Heartbeat keeps proxies and load balancers happy.
                            self.wfile.write(b": ping\n\n")
                            self.wfile.flush()
                            continue
                        data = json.dumps(event, ensure_ascii=False)
                        chunk = f"event: change\ndata: {data}\n\n".encode()
                        self.wfile.write(chunk)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
                finally:
                    srv._unsubscribe(queue)

        return Handler


def run_preview(directory: Path, port: int = _DEFAULT_PORT) -> int:
    """CLI entry — start the server and block until interrupted."""
    server = PreviewServer(directory, port=port)
    try:
        server.start()
    except FileNotFoundError as exc:
        sys.stderr.write(f"Floras Error: {exc}\n")
        return 2

    sys.stderr.write(
        f"floras preview is serving {server.directory} on "
        f"http://127.0.0.1:{server.port} (Ctrl-C to stop)\n"
    )
    try:
        while True:
            time.sleep(60.0)
    except KeyboardInterrupt:
        sys.stderr.write("\nstopping...\n")
    finally:
        server.stop()
    return 0


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _bind_server(
    port: int, handler: type[BaseHTTPRequestHandler]
) -> tuple[ThreadingHTTPServer, int]:
    """Bind an HTTP server, trying ``[port, port+_PORT_RETRY)``.

    A zero port asks the OS to pick any available port and is used by tests
    so they don't collide with each other or with a long-running preview.
    """
    if port == 0:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        return server, server.server_address[1]
    last_err: OSError | None = None
    for candidate in range(port, port + _PORT_RETRY):
        try:
            return ThreadingHTTPServer(("127.0.0.1", candidate), handler), candidate
        except OSError as exc:
            last_err = exc
            continue
    raise OSError(f"no available port in [{port}, {port + _PORT_RETRY})") from last_err


def _error_svg(message: str) -> str:
    safe = html.escape(message)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">'
        '<rect width="400" height="200" fill="#FFE5E5"/>'
        '<text x="20" y="40" font-family="ui-monospace, monospace" '
        f'font-size="14" fill="#7A1F1F">{safe}</text>'
        "</svg>"
    )


# Server-Sent Events keep-alive: many Python http.server installations don't
# expose a public knob for the underlying socket timeout, so we leave it at
# the default and rely on the per-event 15 s heartbeat above.
_ = socket  # silence "imported but unused"


_GALLERY_TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>floras preview — {title}</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg: #FAF7F2; --ink: #2C2825; --muted: #8A847C;
    --card: #FFFFFF; --border: rgba(44,40,37,0.08);
    --error-bg: #FFE5E5; --error-ink: #7A1F1F;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #15110D; --ink: #F4EFE6; --muted: #A39C90;
            --card: #1F1A14; --border: rgba(244,239,230,0.08);
            --error-bg: #3A1717; --error-ink: #F4B7B7; }}
  }}
  html, body {{ margin: 0; background: var(--bg); color: var(--ink); }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", system-ui, sans-serif;
    padding: clamp(16px, 4vw, 48px);
  }}
  header {{ display: flex; align-items: baseline; gap: 16px; margin-bottom: 32px; }}
  h1 {{ font-size: clamp(24px, 4vw, 40px); margin: 0; letter-spacing: -0.02em; }}
  header small {{ color: var(--muted); font-size: 13px; }}
  main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }}
  .card {{
    margin: 0; background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; padding: 18px; display: flex; flex-direction: column; gap: 12px;
    transition: transform 120ms ease, box-shadow 120ms ease;
  }}
  .card.flash {{ box-shadow: 0 0 0 3px rgba(80, 160, 255, 0.4); }}
  .card.has-error {{ border-color: var(--error-ink); background: var(--error-bg); }}
  .preview {{
    aspect-ratio: 1; display: grid; place-items: center; min-height: 220px;
    background:
      repeating-linear-gradient(45deg, transparent 0 8px, rgba(44,40,37,0.025) 8px 9px);
    border-radius: 8px; overflow: hidden;
  }}
  .preview svg {{ width: 100%; height: 100%; max-width: 320px; }}
  figcaption {{ display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }}
  figcaption code {{ color: var(--muted); font-size: 12px; }}
  pre.error {{
    margin: 0; padding: 10px 12px; border-radius: 6px;
    background: rgba(122,31,31,0.1); color: var(--error-ink);
    font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12px;
    white-space: pre-wrap;
  }}
  .status {{
    position: fixed; right: 12px; bottom: 12px; padding: 6px 10px;
    border-radius: 999px; background: var(--card); border: 1px solid var(--border);
    font-size: 12px; color: var(--muted);
  }}
  .status.live::before {{
    content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 6px;
    border-radius: 50%; background: #4CAF50; vertical-align: middle;
  }}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <small>編集して保存すると自動で再描画されます</small>
</header>
<main id="gallery">
{cards}
</main>
<div class="status" id="status">connecting…</div>
<script>
(() => {{
  const status = document.getElementById('status');
  const setLive = () => {{
    status.classList.add('live'); status.textContent = 'live';
  }};
  const setOffline = () => {{
    status.classList.remove('live'); status.textContent = 'offline';
  }};

  function refreshFile(name) {{
    const card = document.querySelector(`figure.card[data-file="${{name}}"]`);
    if (!card) {{ window.location.reload(); return; }}
    fetch(`/svg/${{encodeURIComponent(name)}}?ts=${{Date.now()}}`)
      .then(r => r.text())
      .then(svg => {{
        const preview = card.querySelector('.preview');
        if (preview) preview.innerHTML = svg;
        const oldErr = card.querySelector('pre.error');
        if (oldErr) oldErr.remove();
        card.classList.remove('has-error');
        card.classList.add('flash');
        setTimeout(() => card.classList.remove('flash'), 600);
      }})
      .catch(() => {{}});
  }}

  function connect() {{
    const es = new EventSource('/events');
    es.addEventListener('open', setLive);
    es.addEventListener('error', () => {{ setOffline(); }});
    es.addEventListener('change', (ev) => {{
      try {{
        const payload = JSON.parse(ev.data);
        if (payload.removed) {{ window.location.reload(); return; }}
        refreshFile(payload.file);
      }} catch {{ /* ignore */ }}
    }});
  }}
  connect();
}})();
</script>
</body>
</html>
"""
