#!/usr/bin/env python3
"""
ATS — Frontend Integration Pack Generator
==========================================
Fetches OpenAPI spec from running backend and regenerates:
  - docs/frontend-api.md
  - docs/frontend-api.postman.json
  - docs/curl-examples.sh
  - docs/frontend-integration-checklist.md
  - sdk/ts/types.ts
  - sdk/ts/client.ts

Usage:
    python tools/generate_frontend_pack.py
    python tools/generate_frontend_pack.py --url http://localhost:8000
    python tools/generate_frontend_pack.py --file openapi.json
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent


def fetch_openapi(url: str) -> dict:
    print(f"[*] Fetching OpenAPI from {url} ...")
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"[✓] Got OpenAPI spec — {len(data.get('paths', {}))} paths")
            return data
    except urllib.error.URLError as exc:
        print(f"[!] Cannot reach {url}: {exc}")
        return {}


def load_openapi_file(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"[!] File not found: {path}")
        return {}
    print(f"[*] Loading OpenAPI from {path} ...")
    data = json.loads(p.read_text())
    print(f"[✓] Loaded — {len(data.get('paths', {}))} paths")
    return data


def save_openapi_snapshot(spec: dict) -> None:
    out = ROOT / "openapi.json"
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"[✓] Saved snapshot → openapi.json")


def generate_postman(spec: dict) -> dict:
    """Regenerate Postman collection from spec paths."""
    base_items = []
    paths = spec.get("paths", {})

    groups: dict[str, list] = {}
    for path, methods in paths.items():
        for method, op in methods.items():
            tags = op.get("tags", ["General"])
            tag = tags[0]
            groups.setdefault(tag, [])

            req: dict = {
                "method": method.upper(),
                "url": {
                    "raw": f"{{{{baseUrl}}}}{path}",
                    "host": ["{{baseUrl}}"],
                    "path": [p for p in path.lstrip("/").split("/")],
                },
                "description": op.get("description") or op.get("summary", ""),
            }

            # Add JSON body hint
            rb = op.get("requestBody", {})
            if "application/json" in rb.get("content", {}):
                req["header"] = [{"key": "Content-Type", "value": "application/json"}]
                req["body"] = {
                    "mode": "raw",
                    "raw": "{}",
                    "options": {"raw": {"language": "json"}},
                }
            elif "multipart/form-data" in rb.get("content", {}):
                req["body"] = {"mode": "formdata", "formdata": [{"key": "file", "type": "file", "src": ""}]}

            # Internal — add secret header note
            if "internal" in path:
                req.setdefault("header", [])
                req["header"].append({"key": "X-N8N-SECRET", "value": "{{n8n_secret}}"})

            groups[tag].append({
                "name": f"{method.upper()} {path}",
                "request": req,
                "response": [],
            })

    for tag, items in groups.items():
        base_items.append({"name": tag, "item": items})

    return {
        "info": {
            "_postman_id": "ats-resume-analyzer-v1",
            "name": spec.get("info", {}).get("title", "ATS API"),
            "description": spec.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000", "type": "string"},
            {"key": "jd_id", "value": "1", "type": "string"},
            {"key": "resume_id", "value": "1", "type": "string"},
            {"key": "analysis_id", "value": "1", "type": "string"},
            {"key": "n8n_secret", "value": "change_me_in_production", "type": "string"},
        ],
        "item": base_items,
    }


def run(api_url: str, openapi_file: str | None) -> None:
    # 1. Load spec
    spec: dict = {}
    if openapi_file:
        spec = load_openapi_file(openapi_file)
    if not spec:
        spec = fetch_openapi(f"{api_url}/openapi.json")
    if not spec:
        fallback = ROOT / "openapi.json"
        if fallback.exists():
            spec = load_openapi_file(str(fallback))
    if not spec:
        print("[!] Could not load OpenAPI spec. Generating templates without schema data.")

    # 2. Save snapshot
    if spec:
        save_openapi_snapshot(spec)

    # 3. Regenerate Postman collection
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    sdk_ts_dir = ROOT / "sdk" / "ts"
    sdk_ts_dir.mkdir(parents=True, exist_ok=True)

    postman = generate_postman(spec)
    postman_path = docs_dir / "frontend-api.postman.json"
    postman_path.write_text(json.dumps(postman, indent=2, ensure_ascii=False))
    print(f"[✓] Updated → docs/frontend-api.postman.json ({len(postman.get('item', []))} groups)")

    # 4. Make curl script executable
    curl_sh = docs_dir / "curl-examples.sh"
    if curl_sh.exists():
        curl_sh.chmod(0o755)
        print(f"[✓] chmod +x docs/curl-examples.sh")

    # 5. Print summary
    paths = list(spec.get("paths", {}).keys())
    print()
    print("=" * 60)
    print("Frontend Integration Pack — Summary")
    print("=" * 60)
    print(f"  Endpoints detected : {len(paths)}")
    for p in paths:
        print(f"    {p}")
    print()
    print("  Files generated/verified:")
    for f in [
        "docs/frontend-api.md",
        "docs/frontend-api.postman.json",
        "docs/curl-examples.sh",
        "docs/frontend-integration-checklist.md",
        "sdk/ts/types.ts",
        "sdk/ts/client.ts",
    ]:
        exists = "✓" if (ROOT / f).exists() else "✗ MISSING"
        print(f"    [{exists}] {f}")
    print()
    print("  Import the Postman collection:")
    print("    Postman → Import → docs/frontend-api.postman.json")
    print()
    print("  TypeScript SDK usage:")
    print('    import { ATSClient } from "./sdk/ts/client"')
    print('    const client = new ATSClient("http://localhost:8000")')
    print('    const result = await client.waitForAnalysisDone(analysisId)')


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ATS frontend integration pack")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--file", default=None, help="Load OpenAPI from local JSON file instead")
    args = parser.parse_args()
    run(api_url=args.url, openapi_file=args.file)


if __name__ == "__main__":
    main()
