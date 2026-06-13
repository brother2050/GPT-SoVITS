#!/usr/bin/env python3
"""GPT-SoVITS 参考音频上传助手

在 GPT-SoVITS 服务器上运行，提供 HTTP 上传接口供 ai-drama-pipeline 上传参考音频。

用法:
    python gpt_sovits_upload_server.py                    # 默认端口 9881
    python gpt_sovits_upload_server.py -p 9881 -d /path/to/refs

上传后参考音频会保存到指定目录，可直接在 ai-drama-pipeline 角色配置中使用该路径。

接口:
    POST /upload?name=linxia.wav  — 上传音频文件
    GET  /files                   — 列出已上传的文件
    GET  /files/<name>            — 下载文件
    GET  /health                  — 健康检查
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import cgi
import io


class UploadHandler(BaseHTTPRequestHandler):
    """简易 HTTP 文件上传处理器"""

    upload_dir: str = "./refs"

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "ok", "upload_dir": self.upload_dir})
        elif self.path == "/files":
            self._list_files()
        elif self.path.startswith("/files/"):
            self._serve_file(self.path[7:])
        else:
            self._json_response(200, {
                "message": "GPT-SoVITS 参考音频上传服务",
                "usage": "POST /upload?name=filename.wav (body: raw audio bytes)",
                "endpoints": ["/upload", "/files", "/health"],
            })

    def do_POST(self):
        if self.path.startswith("/upload"):
            self._handle_upload()
        else:
            self._json_response(404, {"error": "not found"})

    def _handle_upload(self):
        """处理文件上传 — 支持两种方式:
        1. POST /upload?name=xxx.wav + body 为原始音频字节
        2. POST /upload + multipart/form-data
        """
        # 解析 query 参数
        query_name = ""
        if "?" in self.path:
            query = self.path.split("?", 1)[1]
            for part in query.split("&"):
                if part.startswith("name="):
                    query_name = part[5:]

        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        if content_length > 50 * 1024 * 1024:
            self._json_response(400, {"error": "文件过大，最大 50MB"})
            return

        if "multipart/form-data" in content_type:
            # Multipart 上传
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
            )
            file_field = form["file"] if "file" in form else None
            if not file_field:
                self._json_response(400, {"error": "缺少 file 字段"})
                return
            filename = query_name or file_field.filename or "upload.wav"
            content = file_field.file.read()
        else:
            # 原始字节上传
            content = self.rfile.read(content_length)
            filename = query_name or "upload.wav"

        # 安全文件名
        filename = Path(filename).name
        if not filename or filename.startswith("."):
            filename = "upload.wav"

        # 写入
        dest = Path(self.upload_dir) / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

        self._json_response(200, {
            "status": "ok",
            "filename": filename,
            "size": len(content),
            "path": str(dest.resolve()),
        })

    def _list_files(self):
        d = Path(self.upload_dir)
        if not d.exists():
            self._json_response(200, {"files": []})
            return
        files = []
        for f in sorted(d.iterdir()):
            if f.is_file() and f.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}:
                files.append({"name": f.name, "size": f.stat().st_size,
                              "path": str(f.resolve())})
        self._json_response(200, {"files": files})

    def _serve_file(self, name: str):
        name = Path(name).name  # 防路径遍历
        fpath = Path(self.upload_dir) / name
        if not fpath.exists():
            self._json_response(404, {"error": "文件不存在"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(fpath.stat().st_size))
        self.end_headers()
        self.wfile.write(fpath.read_bytes())

    def _json_response(self, code: int, data: dict):
        import json
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[上传服务] {args[0]}")


def main():
    parser = argparse.ArgumentParser(description="GPT-SoVITS 参考音频上传服务")
    parser.add_argument("-p", "--port", type=int, default=9881, help="端口（默认 9881）")
    parser.add_argument("-d", "--dir", type=str, default="./refs", help="上传目录（默认 ./refs）")
    parser.add_argument("-a", "--addr", type=str, default="0.0.0.0", help="绑定地址")
    args = parser.parse_args()

    UploadHandler.upload_dir = args.dir
    Path(args.dir).mkdir(parents=True, exist_ok=True)

    server = HTTPServer((args.addr, args.port), UploadHandler)
    print(f"🎵 参考音频上传服务已启动")
    print(f"   地址: http://{args.addr}:{args.port}")
    print(f"   目录: {os.path.abspath(args.dir)}")
    print(f"   用法: POST /upload?name=xxx.wav + 音频字节")
    print(f"   列表: GET /files")

    def shutdown(sig, frame):
        print("\n正在关闭...")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    server.serve_forever()


if __name__ == "__main__":
    main()
