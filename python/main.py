import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


# Static assets and docs are resolved relative to this file location so the server
# works consistently in Docker, local dev, and tests.
STATIC_DIR = Path(__file__).parent / "static"
DOCS_DIR = Path(__file__).parent.parent / "docs"


def fibonacci_first_n(n: int) -> list[int]:
  """Return the first n Fibonacci numbers."""
  # Handle edge cases
  if n <= 0:
    raise ValueError("n must be a positive integer")
  if n == 1:
    return [0]

  # Iterative approach keeps memory small and avoids recursion depth limits.
  numbers = [0, 1]
  a, b = 0, 1
  while len(numbers) < n:
    a, b = b, a + b
    numbers.append(b)
  return numbers


def _json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
  """Standard JSON response helper to keep headers consistent."""
  body = json.dumps(payload).encode("utf-8")
  handler.send_response(status)
  handler.send_header("Content-Type", "application/json; charset=utf-8")
  handler.send_header("Content-Length", str(len(body)))
  handler.end_headers()
  handler.wfile.write(body)

def _html(handler: BaseHTTPRequestHandler, status: int, body: bytes) -> None:
  """Serve pre-rendered HTML (static UI)."""
  handler.send_response(status)
  handler.send_header("Content-Type", "text/html; charset=utf-8")
  handler.send_header("Content-Length", str(len(body)))
  handler.end_headers()
  handler.wfile.write(body)

def _binary(handler: BaseHTTPRequestHandler, status: int, body: bytes, content_type: str) -> None:
  """Serve binary assets like the fun fact PNG."""
  handler.send_response(status)
  handler.send_header("Content-Type", content_type)
  handler.send_header("Content-Length", str(len(body)))
  handler.end_headers()
  handler.wfile.write(body)


class GetFibs(BaseHTTPRequestHandler):
  server_version = "fibonacci-web-app/1.0"
  logger = logging.getLogger("fibonacci.request")

  def log_message(self, fmt: str, *args):
    # Emit simple, structured-ish logs to stdout for container collection.
    self.logger.info(
      "%s - - [%s] " + fmt,
      self.address_string(),
      self.log_date_time_string(),
      *args,
    )

  def do_GET(self):
    parsed = urlparse(self.path)

    # Serve static UI from Python so no extra web server is required in the image.
    if parsed.path in ("/", "/ui", "/index.html"):
      html_path = STATIC_DIR / "index.html"
      if not html_path.exists():
        return _json(self, 404, {"error": "ui not found"})
      return _html(self, 200, html_path.read_bytes())

    # Ship the fun fact image bundled under docs so it matches the request.
    if parsed.path == "/fun-fact.png":
      img_path = DOCS_DIR / "fib-fun-fact.png"
      if not img_path.exists():
        return _json(self, 404, {"error": "fun fact image not found"})
      return _binary(self, 200, img_path.read_bytes(), "image/png")

    # Probe endpoints for k8s / uptime checks.
    if parsed.path in ("/healthz", "/readyz"):
      return _json(self, 200, {"status": "ok"})

    # Only accept the documented paths.
    if parsed.path not in ("/", "/fib"):
      return _json(self, 404, {"error": "not found"})

    params = parse_qs(parsed.query)

    # Required query param guardrails before doing work.
    if "n" not in params or not params["n"]:
      return _json(self, 400, {"error": "missing query param n"})

    try:
      n = int(params["n"][0])
    except (ValueError, TypeError):
      return _json(self, 400, {"error": "n must be an integer"})

    if n <= 0:
      return _json(self, 400, {"error": "n must be a positive integer"})

    # MAX_N caps CPU work per request to keep the service predictable.
    max_n = int(os.getenv("MAX_N", "10000"))
    if n > max_n:
      return _json(self, 422, {"error": f"n must be <= {max_n}", "max_n": max_n})

    nums = fibonacci_first_n(n)
    return _json(self, 200, {"n": n, "sequence": nums})


def main():
  # Configure logging once; children handlers reuse this.
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
  )

  port = int(os.getenv("PORT", "8000"))
  host = os.getenv("HOST", "0.0.0.0")

  httpd = HTTPServer((host, port), GetFibs)
  logging.getLogger("fibonacci").info("Listening on http://%s:%s", host, port)
  httpd.serve_forever()

def create_server(host: str, port: int):
  return HTTPServer((host, port), GetFibs)

if __name__ == "__main__":
  port = int(os.getenv("PORT", "8000"))
  httpd = create_server("0.0.0.0", port)
  httpd.serve_forever()
