import argparse
import json
import mimetypes
import os
import uuid
from pathlib import Path
from urllib import request


def build_multipart(field_name: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    file_bytes = file_path.read_bytes()
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

    lines = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"',
        f"Content-Type: {mime_type}",
        "",
    ]
    body_start = "\r\n".join(lines).encode("utf-8") + b"\r\n"
    body_end = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = body_start + file_bytes + body_end

    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def run_smoke_test(base_url: str, image_path: Path) -> None:
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    body, content_type = build_multipart("image", image_path)
    endpoint = f"{base_url.rstrip('/')}/predict"

    req = request.Request(endpoint, method="POST", data=body)
    req.add_header("Content-Type", content_type)

    with request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    print("Smoke test successful")
    print(f"label: {payload.get('label')}")
    print(f"probability: {payload.get('probability')}")
    print("gradcam returned:", bool(payload.get("gradcam")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send one image to /predict and print result summary.")
    parser.add_argument("image", type=str, help="Path to an image file")
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("BASE_URL", "http://127.0.0.1:8000"),
        help="Backend base URL",
    )
    args = parser.parse_args()

    run_smoke_test(args.base_url, Path(args.image))
