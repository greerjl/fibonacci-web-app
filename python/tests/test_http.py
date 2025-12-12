import os
import threading
import time

import requests

from main import create_server


def _start_server():
  httpd = create_server("127.0.0.1", 0)
  port = httpd.server_port

  t = threading.Thread(target=httpd.serve_forever, daemon=True)
  t.start()
  time.sleep(0.05)

  return httpd, port

def _find_api_base(port: int) -> str:
  candidates = [
    "/fib",
    "/api/fib",
    "/fibonacci",
    "/api/fibonacci",
  ]

  for path in candidates:
    r = requests.get(f"http://127.0.0.1:{port}{path}?n=2", timeout=2)
    ctype = r.headers.get("Content-Type", "")
    if r.status_code == 200 and "application/json" in ctype:
      return path

  raise AssertionError("Could not find JSON API endpoint. Tried: " + ", ".join(candidates))

def test_valid_n_returns_200_and_sequence():
  httpd, port = _start_server()
  try:
    api = _find_api_base(port)
    r = requests.get(f"http://127.0.0.1:{port}{api}?n=6", timeout=2)
    assert r.status_code == 200
    body = r.json()
    assert body["n"] == 6
    assert body["sequence"] == [0, 1, 1, 2, 3, 5]
  finally:
    httpd.shutdown()
    httpd.server_close()

def test_invalid_n_returns_400():
  httpd, port = _start_server()
  try:
    api = _find_api_base(port)
    r = requests.get(f"http://127.0.0.1:{port}{api}?n=abc", timeout=2)
    assert r.status_code == 400
  finally:
    httpd.shutdown()
    httpd.server_close()

def test_above_max_returns_422():
  old = os.environ.get("MAX_N")
  os.environ["MAX_N"] = "5"

  httpd, port = _start_server()
  try:
    api = _find_api_base(port)
    r = requests.get(f"http://127.0.0.1:{port}{api}?n=10", timeout=2)
    assert r.status_code == 422
    body = r.json()
    assert body["max_n"] == 5
    assert "n must be <= 5" in body["error"]
  finally:
    httpd.shutdown()
    httpd.server_close()

    if old is None:
      os.environ.pop("MAX_N", None)
    else:
      os.environ["MAX_N"] = old

def test_ui_served():
  httpd, port = _start_server()
  try:
    r = requests.get(f"http://127.0.0.1:{port}/ui", timeout=2)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")
    assert "<!doctype html" in r.text.lower()
  finally:
    httpd.shutdown()
    httpd.server_close()

def test_root_serves_ui():
  httpd, port = _start_server()
  try:
    r = requests.get(f"http://127.0.0.1:{port}/", timeout=2)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")
    assert "<!doctype html" in r.text.lower()
  finally:
    httpd.shutdown()
    httpd.server_close()