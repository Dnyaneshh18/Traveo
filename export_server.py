import http.server
import socketserver
import os

PORT = 8089

class ExportHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/export' or self.path == '/export/' or self.path == '/':
            ps_file = '/home/user/Traveo/write-portal.ps1'
            with open(ps_file, 'r', encoding='utf-8') as f:
                content = f.read()
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Traveo - Full Project Copy Script</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
        .box {{ max-width: 900px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        h1 {{ color: #38bdf8; margin-top: 0; font-size: 24px; }}
        p {{ color: #94a3b8; font-size: 15px; line-height: 1.5; }}
        button {{ background: #22c55e; color: #022c22; font-weight: 800; font-size: 18px; border: none; border-radius: 8px; padding: 16px 24px; cursor: pointer; transition: background 0.2s; width: 100%; }}
        button:hover {{ background: #16a34a; }}
        textarea {{ width: 100%; height: 350px; background: #020617; color: #a5f3fc; border: 1px solid #334155; border-radius: 8px; font-family: monospace; font-size: 13px; padding: 12px; box-sizing: border-box; margin-top: 16px; white-space: pre; }}
        .copied {{ display: none; background: #10b981; color: white; padding: 10px; border-radius: 6px; text-align: center; font-weight: bold; margin-top: 10px; }}
        .step {{ background: #0f172a; padding: 12px 16px; border-radius: 6px; margin-top: 8px; border-left: 4px solid #38bdf8; font-family: monospace; font-size: 14px; color: #e2e8f0; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>📦 Traveo — Complete Project Copy Script</h1>
        <p>This script contains the <b>entire Traveo codebase</b> (226 files: frontend, backend, packages, mobile-ui, config, and assets).</p>
        
        <button id="copy-btn" onclick="copyCode()">📋 CLICK TO COPY FULL SCRIPT</button>
        <div id="copied-msg" class="copied">✓ COPIED TO CLIPBOARD!</div>

        <h3 style="color: #38bdf8; margin-top: 24px;">How to run on your PC:</h3>
        <div class="step">1. Open Notepad on Windows</div>
        <div class="step">2. Paste (Ctrl + V) the copied text</div>
        <div class="step">3. Save As &rarr; <b>C:\TRAVEO\write-portal.ps1</b> (Save as type: <b>All files</b>)</div>
        <div class="step">4. In PowerShell at <b>C:\TRAVEO&gt;</b> run: <span style="color:#4ade80;">.\write-portal.ps1</span></div>

        <textarea id="script-area" readonly>{content}</textarea>
    </div>

    <script>
        function copyCode() {{
            const ta = document.getElementById('script-area');
            ta.select();
            navigator.clipboard.writeText(ta.value).then(() => {{
                const msg = document.getElementById('copied-msg');
                msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 3000);
            }}).catch(() => {{
                document.execCommand('copy');
                const msg = document.getElementById('copied-msg');
                msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 3000);
            }});
        }}
    </script>
</body>
</html>"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return
        elif self.path == '/raw':
            ps_file = '/home/user/Traveo/write-portal.ps1'
            with open(ps_file, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="write-portal.ps1"')
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('0.0.0.0', PORT), ExportHandler) as httpd:
    print(f"Export server running on 0.0.0.0:{PORT}...")
    httpd.serve_forever()
