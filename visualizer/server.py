"""
Simple local HTTP server for the RandAR confidence visualizer.

Run after generate_images.py has produced an output directory:

    python visualizer/server.py --output-dir visualizer/output
    # then open http://localhost:8000
"""

import argparse
import http.server
import mimetypes
import os
import socketserver
import sys


def make_handler(output_dir: str):
    """Return a request handler that serves files from output_dir."""

    # Resolve to absolute path once at startup
    root = os.path.realpath(output_dir)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # Strip query string
            path = self.path.split("?")[0].split("#")[0]

            # Default to index.html
            if path in ("/", ""):
                path = "/index.html"

            # Resolve and safety-check the path
            rel = path.lstrip("/").replace("/", os.sep)
            abs_path = os.path.realpath(os.path.join(root, rel))
            if not abs_path.startswith(root):
                self.send_error(403, "Forbidden")
                return

            if not os.path.isfile(abs_path):
                self.send_error(404, f"Not found: {path}")
                return

            self._serve(abs_path)

        def _serve(self, filepath: str):
            mime, _ = mimetypes.guess_type(filepath)
            mime = mime or "application/octet-stream"
            try:
                with open(filepath, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(data)
            except OSError as e:
                self.send_error(500, str(e))

        def log_message(self, fmt, *a):
            # Only log errors
            if int(a[1]) >= 400:
                super().log_message(fmt, *a)

    return Handler


def main():
    parser = argparse.ArgumentParser(
        description="Serve the RandAR confidence visualizer locally."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="visualizer/output",
        help="Directory produced by generate_images.py (default: visualizer/output)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind (default: localhost)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f"Error: output directory not found: {args.output_dir}")
        print("Run generate_images.py first to produce the output directory.")
        sys.exit(1)

    index = os.path.join(args.output_dir, "index.html")
    if not os.path.isfile(index):
        print(f"Warning: {index} not found. Did generate_images.py finish successfully?")

    handler = make_handler(args.output_dir)

    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        url = f"http://{args.host}:{args.port}"
        print(f"Serving {os.path.realpath(args.output_dir)}")
        print(f"Open in browser: {url}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
