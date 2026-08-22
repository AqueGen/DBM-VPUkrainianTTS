#!/usr/bin/env python3
"""Serve the review page and open it in a browser.

The page plays audio from three places - this pack, the reference pack next door and
generation/variants - so the server is rooted at the AddOns folder rather than at the
pack. Opening review.html straight from disk is not enough for that.

Run:  python generation/serve.py      (Ctrl+C to stop)
"""
import http.server
import os
import socket
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
ADDONS = os.path.dirname(os.path.dirname(HERE))
PAGE = "/%s/generation/review.html" % os.path.basename(os.path.dirname(HERE))
PORT = 8787


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ADDONS, **kwargs)

    def log_message(self, *args):  # keep the console readable
        pass


def free_port(start):
    for port in range(start, start + 20):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit("no free port in %d-%d" % (start, start + 20))


def main():
    if not os.path.exists(os.path.join(HERE, "review.html")):
        raise SystemExit("review.html missing - run: python generation/build_review.py")
    port = free_port(PORT)
    url = "http://127.0.0.1:%d%s" % (port, PAGE)
    print("serving %s\n%s\nCtrl+C to stop" % (ADDONS, url))
    webbrowser.open(url)
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("stopped")


if __name__ == "__main__":
    main()
