import threading
import time

import requests

# HTTP integration-ish tests that spin up the local server and exercise routes.
from python.main import create_server


def _start_server():
  try:
    httpd = create_server("127.0.0.1", 0)
  except PermissionError as exc:  # Sandbox environments may block binds
    pytest.skip(f"Cannot bind test server: {exc}")
  port = httpd.server_port

  t = threading.Thread(target=httpd.serve_forever, daemon=True)
  t.start()

  # Give the server a moment to start
  time.sleep(0.05)
  return httpd, port


def test_valid_n_returns_200_and_sequence():
  httpd, port = _start_server()
  try:
    r = requests.get(f"http://127.0.0.1:{port}/?n=6")
    assert r.status_code == 200
    body = r.json()
    assert body["n"] == 6
    assert body["sequence"] == [0, 1, 1, 2, 3, 5]
  finally:
    httpd.shutdown()


def test_invalid_n_returns_400():
  httpd, port = _start_server()
  try:
    r = requests.get(f"http://127.0.0.1:{port}/?n=abc")
    assert r.status_code == 400
    assert "n must be an integer" in r.json()["error"]
  finally:
    httpd.shutdown()


def test_above_max_returns_422():
  httpd, port = _start_server()
  try:
    os.environ["MAX_N"] = "5"
    r = requests.get(f"http://127.0.0.1:{port}/?n=10")
    assert r.status_code == 422
    body = r.json()
    assert body["max_n"] == 5
    assert "n must be <= 5" in body["error"]
  finally:
    os.environ.pop("MAX_N", None)
    httpd.shutdown()


def test_ui_served():
  httpd, port = _start_server()
  try:
    r = requests.get(f"http://127.0.0.1:{port}/ui")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")
    assert "<!DOCTYPE html>" in r.text
  finally:
    httpd.shutdown()


def test_root_serves_ui():
  httpd, port = _start_server()
  try:
    r = requests.get(f"http://127.0.0.1:{port}/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")
    assert "<!DOCTYPE html>" in r.text
  finally:
    httpd.shutdown()
