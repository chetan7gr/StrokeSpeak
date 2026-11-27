"""
Test FastAPI video streaming endpoints
"""
import urllib.request
import json

lessons = [61, 339, 55, 223, 348]

for lid in lessons:
    url = f"http://127.0.0.1:8000/api/v1/lessons/{lid}/video"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type")
            content_length = resp.headers.get("Content-Length")
            chunk = resp.read(1024)
            print(f"Lesson {lid:3d}: Status {resp.status}, Content-Type: {content_type}, Size: {int(content_length)/1024:.1f} KB, First 1KB read OK")
    except Exception as e:
        print(f"Lesson {lid:3d}: Error: {e}")
