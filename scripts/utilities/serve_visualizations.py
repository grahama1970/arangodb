#!/usr/bin/env python3
"""Simple HTTP server for D3 visualizations accessible from remote machines"""

import http.server
import socketserver
import os
from pathlib import Path

# Change to visualizations directory
viz_dir = Path("/home/graham/workspace/experiments/arangodb/visualizations")
os.chdir(viz_dir)

# Define server settings
PORT = 8888
HOST = "0.0.0.0"  # Listen on all interfaces

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow access from browser
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        super().end_headers()

# Create server
with socketserver.TCPServer((HOST, PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving D3 visualizations at http://192.168.86.49:{PORT}")
    print(f"Local access: http://localhost:{PORT}")
    print("\nAvailable visualizations:")
    for html_file in viz_dir.glob("*.html"):
        print(f"  - http://192.168.86.49:{PORT}/{html_file.name}")
    
    print("\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")