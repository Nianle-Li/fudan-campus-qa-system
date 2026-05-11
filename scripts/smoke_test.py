from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]


class SmokeFailure(Exception):
    pass


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {}
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SmokeFailure(f"{method} {path} failed with HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise SmokeFailure(f"{method} {path} failed: {exc}") from exc


def request_text(base_url: str, path: str) -> str:
    try:
        with urlopen(f"{base_url}{path}", timeout=10) as response:
            return response.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise SmokeFailure(f"GET {path} failed: {exc}") from exc


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def wait_for_server(base_url: str, deadline_seconds: int = 15) -> None:
    deadline = time.time() + deadline_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            request_json(base_url, "GET", "/api/health")
            return
        except Exception as exc:  # noqa: BLE001 - keep polling while the dev server warms up.
            last_error = exc
            time.sleep(0.5)
    raise SmokeFailure(f"server did not become ready: {last_error}")


def start_demo_server(port: int) -> subprocess.Popen[Any]:
    env = os.environ.copy()
    env["FCQA_DEMO_MODE"] = "1"
    env["FCQA_PORT"] = str(port)
    return subprocess.Popen(
        [sys.executable, "-u", str(ROOT_DIR / "backend" / "app.py")],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_smoke(base_url: str) -> list[str]:
    passed: list[str] = []
    created_activity_id: int | None = None
    created_facility_id: int | None = None
    created_building_id: int | None = None

    health = request_json(base_url, "GET", "/api/health")
    assert_true(health.get("service") == "ok", "health check did not return service=ok")
    passed.append("health")

    index_html = request_text(base_url, "/")
    assert_true("复旦校园百事通" in index_html, "frontend index page did not render expected title")
    passed.append("frontend")

    campuses = request_json(base_url, "GET", "/api/campuses")["items"]
    assert_true(len(campuses) >= 1, "campus query returned no rows")
    passed.append("campus query")

    buildings = request_json(base_url, "GET", "/api/buildings")["items"]
    assert_true(len(buildings) >= 1, "building query returned no rows")
    passed.append("building query")

    created_building = request_json(
        base_url,
        "POST",
        "/api/buildings",
        {"name": "Smoke Test Building", "type": "教学楼", "campus_id": campuses[0]["campus_id"]},
    )["item"]
    created_building_id = int(created_building["building_id"])
    updated_building = request_json(
        base_url,
        "PUT",
        f"/api/buildings/{created_building_id}",
        {"name": "Smoke Test Building Updated", "type": "综合楼", "campus_id": campuses[0]["campus_id"]},
    )["item"]
    assert_true(updated_building["name"] == "Smoke Test Building Updated", "building update did not persist")
    passed.append("building create/update")

    created_facility = request_json(
        base_url,
        "POST",
        "/api/facilities",
        {
            "name": "Smoke Test Room",
            "type": "教室",
            "open_time": "09:00-18:00",
            "building_id": created_building_id,
        },
    )["item"]
    created_facility_id = int(created_facility["facility_id"])
    updated_facility = request_json(
        base_url,
        "PUT",
        f"/api/facilities/{created_facility_id}",
        {
            "name": "Smoke Test Room Updated",
            "type": "自习室",
            "open_time": "08:00-22:00",
            "building_id": created_building_id,
        },
    )["item"]
    assert_true(updated_facility["name"] == "Smoke Test Room Updated", "facility update did not persist")
    passed.append("facility create/update")

    created_activity = request_json(
        base_url,
        "POST",
        "/api/activities",
        {
            "name": "Smoke Test Activity",
            "description": "Smoke test activity description",
            "start_time": "2026-05-30T10:00",
            "end_time": "2026-05-30T11:00",
            "organizer": "Smoke Test",
            "facility_id": created_facility_id,
        },
    )["item"]
    created_activity_id = int(created_activity["activity_id"])
    updated_activity = request_json(
        base_url,
        "PUT",
        f"/api/activities/{created_activity_id}",
        {
            "name": "Smoke Test Activity Updated",
            "description": "Smoke test activity description updated",
            "start_time": "2026-05-30T10:30",
            "end_time": "2026-05-30T11:30",
            "organizer": "Smoke Test",
            "facility_id": created_facility_id,
        },
    )["item"]
    assert_true(updated_activity["name"] == "Smoke Test Activity Updated", "activity update did not persist")
    passed.append("activity create/update")

    courses = request_json(base_url, "GET", "/api/courses")["items"]
    assert_true(len(courses) >= 1, "course query returned no rows")
    passed.append("course join query")

    sql_examples = request_json(base_url, "GET", "/api/sql-examples")["items"]
    assert_true(len(sql_examples) >= 7, "sql examples endpoint returned too few examples")
    assert_true(all("sql" in item and "rows" in item for item in sql_examples), "sql examples missing sql or rows")
    passed.append("sql examples")

    log = request_json(
        base_url,
        "POST",
        "/api/query-log",
        {"user_id": 4, "query_category": "其他", "query_content": "Smoke test query"},
    )["item"]
    assert_true("log_id" in log, "query log insert did not return log_id")
    passed.append("query log insert")

    request_json(base_url, "DELETE", f"/api/activities/{created_activity_id}")
    created_activity_id = None
    request_json(base_url, "DELETE", f"/api/facilities/{created_facility_id}")
    created_facility_id = None
    request_json(base_url, "DELETE", f"/api/buildings/{created_building_id}")
    created_building_id = None
    passed.append("cleanup delete")

    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke tests against the campus QA demo API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="running backend base URL")
    parser.add_argument("--start-demo", action="store_true", help="start backend/app.py with FCQA_DEMO_MODE=1")
    parser.add_argument("--port", type=int, default=8899, help="port used with --start-demo")
    args = parser.parse_args()

    process: subprocess.Popen[Any] | None = None
    base_url = args.base_url
    if args.start_demo:
        base_url = f"http://127.0.0.1:{args.port}"
        process = start_demo_server(args.port)

    try:
        wait_for_server(base_url)
        passed = run_smoke(base_url)
    except SmokeFailure as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    print("SMOKE TEST PASSED")
    for item in passed:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
