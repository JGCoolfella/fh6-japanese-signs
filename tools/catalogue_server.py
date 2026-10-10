"""Local server for the sign catalogue: choices and custom images are saved straight to disk.

  python tools/catalogue_server.py          # then open http://127.0.0.1:8765
  (or double-click "Open sign catalogue.bat")

Saves into catalogue/choices/:
  choices.json            {id: {"choice": ..., "fit": ..., "rotate": ...}}
  choices.csv             same table the build tools read (also written by import_choices.py)
  <ID>_custom.png         the uploaded image for that sign
Only listens on 127.0.0.1 (this PC).
"""
import csv
import json
import os
import re
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "catalogue")
CH = os.path.join(CAT, "choices")
STATE = os.path.join(CH, "choices.json")
PORT = 8765
ID_RE = re.compile(r"^[PTDS]\d{3}$")
MAX_IMAGE = 25 * 1024 * 1024
LOCK = threading.Lock()


def catalogue_rows():
    path = os.path.join(CAT, "catalogue.csv")
    return {r["id"]: r for r in csv.DictReader(open(path, encoding="utf-8-sig"))} if os.path.exists(path) else {}


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    state = {}
    old = os.path.join(CH, "choices.csv")  # from an earlier exported file (import_choices.py)
    if os.path.exists(old):
        for r in csv.DictReader(open(old, encoding="utf-8-sig")):
            state[r["id"]] = {"choice": r.get("your_choice", ""), "fit": r.get("fit") or "logo",
                              "rotate": int(r.get("rotate") or 0)}
    return state


def save_state(state):
    os.makedirs(CH, exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump(state, open(tmp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.replace(tmp, STATE)
    cat = catalogue_rows()
    keys = ["id", "original_sign", "current_swap", "your_choice", "custom_image", "fit", "rotate", "source_texture", "where"]
    with open(os.path.join(CH, "choices.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for sid in sorted(state):
            s, c = state[sid], cat.get(sid, {})
            img = os.path.exists(image_path(sid))
            if not (s.get("choice") or img):
                continue
            w.writerow({"id": sid, "original_sign": c.get("original", ""), "current_swap": c.get("current_swap", ""),
                        "your_choice": s.get("choice", ""), "custom_image": f"{sid}_custom.png" if img else "",
                        "fit": s.get("fit", "") if img else "", "rotate": s.get("rotate", 0) if img else "",
                        "source_texture": c.get("source_texture", ""), "where": c.get("where", "")})


def image_path(sid):
    return os.path.join(CH, f"{sid}_custom.png")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=CAT, **k)

    def log_message(self, fmt, *args):  # quiet
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _sid(self):
        sid = parse_qs(urlparse(self.path).query).get("id", [""])[0]
        return sid if ID_RE.match(sid) else None

    def end_headers(self):
        if self.path.startswith("/choices/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/api/state":
            with LOCK:
                state = load_state()
                signs = {}
                for sid in set(state) | {f[:4] for f in os.listdir(CH) if f.endswith("_custom.png")} if os.path.isdir(CH) else state:
                    s = state.get(sid, {})
                    p = image_path(sid)
                    signs[sid] = {"choice": s.get("choice", ""), "fit": s.get("fit", "logo"), "rotate": s.get("rotate", 0),
                                  "image": f"choices/{sid}_custom.png?v={int(os.path.getmtime(p))}" if os.path.exists(p) else None}
            return self._json({"server": True, "folder": CH, "signs": signs})
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_IMAGE:
            return self._json({"error": "too large"}, 413)
        body = self.rfile.read(n)
        if path == "/api/choice":
            try:
                items = json.loads(body)
            except ValueError:
                return self._json({"error": "bad json"}, 400)
            items = items if isinstance(items, list) else [items]
            with LOCK:
                state = load_state()
                for it in items:
                    sid = it.get("id", "")
                    if not ID_RE.match(sid):
                        continue
                    state[sid] = {"choice": str(it.get("choice", ""))[:200], "fit": it.get("fit") if it.get("fit") in ("logo", "fill", "stretch") else "logo",
                                  "rotate": int(it.get("rotate", 0)) % 360}
                    if not state[sid]["choice"] and not os.path.exists(image_path(sid)):
                        del state[sid]
                save_state(state)
            return self._json({"ok": True})
        if path == "/api/image":
            sid = self._sid()
            if not sid or not body.startswith(b"\x89PNG"):
                return self._json({"error": "need ?id=P001 and a PNG body"}, 400)
            with LOCK:
                os.makedirs(CH, exist_ok=True)
                open(image_path(sid), "wb").write(body)
                save_state(load_state())
            return self._json({"ok": True, "url": f"choices/{sid}_custom.png?v={int(os.path.getmtime(image_path(sid)))}"})
        return self._json({"error": "unknown"}, 404)

    def do_DELETE(self):
        if urlparse(self.path).path == "/api/image" and self._sid():
            sid = self._sid()
            with LOCK:
                if os.path.exists(image_path(sid)):
                    os.remove(image_path(sid))
                save_state(load_state())
            return self._json({"ok": True})
        return self._json({"error": "unknown"}, 404)


def main():
    os.makedirs(CH, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Sign catalogue: {url}\nSaving to: {CH}\nLeave this window open while you work; close it when done.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
