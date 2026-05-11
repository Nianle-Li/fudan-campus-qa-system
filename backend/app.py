from __future__ import annotations

import json
import os
import re
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
HOST = os.getenv("FCQA_HOST", "127.0.0.1")
PORT = int(os.getenv("FCQA_PORT", os.getenv("PORT", "8000")))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fcqa")
DEMO_MODE = os.getenv("FCQA_DEMO_MODE", "").lower() in {"1", "true", "yes", "on"}


BUILDING_TYPES = ["教学楼", "图书馆", "宿舍", "食堂", "体育场馆", "办公楼", "实验楼", "医院", "综合楼", "其他"]
FACILITY_TYPES = ["教室", "自习室", "会议室", "实验室", "报告厅", "图书阅览室", "体育设施", "餐饮服务", "办公服务", "其他"]
QUERY_CATEGORIES = ["校区", "建筑", "设施", "课程", "教师", "活动", "用户", "统计", "其他"]


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    return str(value)


def clean_text(payload: dict[str, Any], key: str, *, required: bool = True, default: str | None = None) -> str:
    value = payload.get(key, default)
    if value is None:
        if required:
            raise ApiError(HTTPStatus.BAD_REQUEST, f"缺少字段：{key}")
        return ""
    value = str(value).strip()
    if required and not value:
        raise ApiError(HTTPStatus.BAD_REQUEST, f"字段不能为空：{key}")
    return value


def clean_int(payload: dict[str, Any], key: str, *, required: bool = True) -> int | None:
    value = payload.get(key)
    if value in (None, ""):
        if required:
            raise ApiError(HTTPStatus.BAD_REQUEST, f"缺少字段：{key}")
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ApiError(HTTPStatus.BAD_REQUEST, f"字段必须是整数：{key}") from exc


def parse_datetime_text(value: str | None) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip().replace("T", " ")
    try:
        datetime.fromisoformat(text)
    except ValueError as exc:
        raise ApiError(HTTPStatus.BAD_REQUEST, "时间格式应为 YYYY-MM-DD HH:MM:SS 或浏览器 datetime-local 格式") from exc
    return text


class PostgresRepository:
    mode = "postgres"

    def __init__(self, dsn: str):
        self.dsn = dsn

    def _connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise ApiError(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "缺少 psycopg 驱动，请先执行：python -m pip install -r backend/requirements.txt",
            ) from exc
        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=1)

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return list(cur.fetchall())
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(HTTPStatus.INTERNAL_SERVER_ERROR, f"数据库查询失败：{exc}") from exc

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def execute_returning(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    row = cur.fetchone()
                    conn.commit()
                    if row is None:
                        raise ApiError(HTTPStatus.NOT_FOUND, "目标记录不存在")
                    return dict(row)
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(HTTPStatus.BAD_REQUEST, f"数据库写入失败：{exc}") from exc

    def execute_count(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    affected = cur.rowcount
                    conn.commit()
                    return affected
        except Exception as exc:
            raise ApiError(HTTPStatus.BAD_REQUEST, f"数据库写入失败：{exc}") from exc

    def ping(self) -> bool:
        self.fetch_one("SELECT 1 AS ok")
        return True

    def campuses(self, query: dict[str, str]) -> list[dict[str, Any]]:
        q = query.get("q", "").strip()
        where = ""
        params: list[Any] = []
        if q:
            where = "WHERE name ILIKE %s OR address ILIKE %s"
            params = [f"%{q}%", f"%{q}%"]
        return self.fetch_all(
            f"""
            SELECT campus_id, name, address
            FROM campus
            {where}
            ORDER BY campus_id
            """,
            tuple(params),
        )

    def buildings(self, query: dict[str, str]) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []
        if query.get("campus_id"):
            conditions.append("b.campus_id = %s")
            params.append(int(query["campus_id"]))
        if query.get("q"):
            q = f"%{query['q'].strip()}%"
            conditions.append("(b.name ILIKE %s OR b.type ILIKE %s OR c.name ILIKE %s)")
            params.extend([q, q, q])
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return self.fetch_all(
            f"""
            SELECT b.building_id, b.name, b.type, b.campus_id, c.name AS campus_name
            FROM building b
            JOIN campus c ON c.campus_id = b.campus_id
            {where}
            ORDER BY c.campus_id, b.building_id
            """,
            tuple(params),
        )

    def create_building(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = clean_text(payload, "name")
        building_type = clean_text(payload, "type", default="其他")
        campus_id = clean_int(payload, "campus_id")
        if building_type not in BUILDING_TYPES:
            raise ApiError(HTTPStatus.BAD_REQUEST, "建筑类型不在允许范围内")
        return self.execute_returning(
            """
            WITH saved AS (
              INSERT INTO building (name, type, campus_id)
              VALUES (%s, %s, %s)
              RETURNING *
            )
            SELECT saved.building_id, saved.name, saved.type, saved.campus_id, c.name AS campus_name
            FROM saved
            JOIN campus c ON c.campus_id = saved.campus_id
            """,
            (name, building_type, campus_id),
        )

    def update_building(self, building_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        name = clean_text(payload, "name")
        building_type = clean_text(payload, "type", default="其他")
        campus_id = clean_int(payload, "campus_id")
        if building_type not in BUILDING_TYPES:
            raise ApiError(HTTPStatus.BAD_REQUEST, "建筑类型不在允许范围内")
        return self.execute_returning(
            """
            WITH saved AS (
              UPDATE building
              SET name = %s, type = %s, campus_id = %s
              WHERE building_id = %s
              RETURNING *
            )
            SELECT saved.building_id, saved.name, saved.type, saved.campus_id, c.name AS campus_name
            FROM saved
            JOIN campus c ON c.campus_id = saved.campus_id
            """,
            (name, building_type, campus_id, building_id),
        )

    def delete_building(self, building_id: int) -> dict[str, Any]:
        affected = self.execute_count("DELETE FROM building WHERE building_id = %s", (building_id,))
        if affected == 0:
            raise ApiError(HTTPStatus.NOT_FOUND, "建筑不存在")
        return {"deleted": affected}

    def facilities(self, query: dict[str, str]) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []
        if query.get("building_id"):
            conditions.append("f.building_id = %s")
            params.append(int(query["building_id"]))
        if query.get("q"):
            q = f"%{query['q'].strip()}%"
            conditions.append("(f.name ILIKE %s OR f.type ILIKE %s OR b.name ILIKE %s)")
            params.extend([q, q, q])
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return self.fetch_all(
            f"""
            SELECT f.facility_id, f.name, f.type, f.open_time, f.building_id,
                   b.name AS building_name, c.name AS campus_name
            FROM facility f
            JOIN building b ON b.building_id = f.building_id
            JOIN campus c ON c.campus_id = b.campus_id
            {where}
            ORDER BY c.campus_id, b.building_id, f.facility_id
            """,
            tuple(params),
        )

    def create_facility(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = clean_text(payload, "name")
        facility_type = clean_text(payload, "type", default="其他")
        open_time = clean_text(payload, "open_time", default="以现场公告为准")
        building_id = clean_int(payload, "building_id")
        if facility_type not in FACILITY_TYPES:
            raise ApiError(HTTPStatus.BAD_REQUEST, "设施类型不在允许范围内")
        return self.execute_returning(
            """
            WITH saved AS (
              INSERT INTO facility (name, type, open_time, building_id)
              VALUES (%s, %s, %s, %s)
              RETURNING *
            )
            SELECT saved.facility_id, saved.name, saved.type, saved.open_time, saved.building_id,
                   b.name AS building_name, c.name AS campus_name
            FROM saved
            JOIN building b ON b.building_id = saved.building_id
            JOIN campus c ON c.campus_id = b.campus_id
            """,
            (name, facility_type, open_time, building_id),
        )

    def update_facility(self, facility_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        name = clean_text(payload, "name")
        facility_type = clean_text(payload, "type", default="其他")
        open_time = clean_text(payload, "open_time", default="以现场公告为准")
        building_id = clean_int(payload, "building_id")
        if facility_type not in FACILITY_TYPES:
            raise ApiError(HTTPStatus.BAD_REQUEST, "设施类型不在允许范围内")
        return self.execute_returning(
            """
            WITH saved AS (
              UPDATE facility
              SET name = %s, type = %s, open_time = %s, building_id = %s
              WHERE facility_id = %s
              RETURNING *
            )
            SELECT saved.facility_id, saved.name, saved.type, saved.open_time, saved.building_id,
                   b.name AS building_name, c.name AS campus_name
            FROM saved
            JOIN building b ON b.building_id = saved.building_id
            JOIN campus c ON c.campus_id = b.campus_id
            """,
            (name, facility_type, open_time, building_id, facility_id),
        )

    def delete_facility(self, facility_id: int) -> dict[str, Any]:
        affected = self.execute_count("DELETE FROM facility WHERE facility_id = %s", (facility_id,))
        if affected == 0:
            raise ApiError(HTTPStatus.NOT_FOUND, "设施不存在")
        return {"deleted": affected}

    def courses(self, query: dict[str, str]) -> list[dict[str, Any]]:
        params: list[Any] = []
        where = ""
        if query.get("q"):
            q = f"%{query['q'].strip()}%"
            where = "WHERE c.name ILIKE %s OR co.course_code ILIKE %s OR u.name ILIKE %s"
            params = [q, q, q]
        return self.fetch_all(
            f"""
            SELECT co.offering_id, co.course_code, co.semester,
                   c.course_master_code, c.name AS course_name,
                   string_agg(DISTINCT u.name, '、' ORDER BY u.name) AS teachers,
                   string_agg(
                     DISTINCT cos.day_of_week || ' ' || cos.start_period || '-' || cos.end_period
                       || '节 ' || cos.week_type || ' @ ' || f.name,
                     '；' ORDER BY cos.day_of_week || ' ' || cos.start_period || '-' || cos.end_period
                       || '节 ' || cos.week_type || ' @ ' || f.name
                   ) AS schedules
            FROM course_offering co
            JOIN course_section cs ON cs.course_code = co.course_code
            JOIN course c ON c.course_master_code = cs.course_master_code
            LEFT JOIN course_offering_teacher cot ON cot.offering_id = co.offering_id
            LEFT JOIN teacher t ON t.user_id = cot.teacher_id
            LEFT JOIN users u ON u.user_id = t.user_id
            LEFT JOIN course_offering_schedule cos ON cos.offering_id = co.offering_id
            LEFT JOIN facility f ON f.facility_id = cos.facility_id
            {where}
            GROUP BY co.offering_id, co.course_code, co.semester, c.course_master_code, c.name
            ORDER BY c.name, co.course_code, co.offering_id
            """,
            tuple(params),
        )

    def activities(self, query: dict[str, str]) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []
        if query.get("q"):
            q = f"%{query['q'].strip()}%"
            conditions.append("(a.name ILIKE %s OR a.description ILIKE %s OR a.organizer ILIKE %s)")
            params.extend([q, q, q])
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return self.fetch_all(
            f"""
            SELECT a.activity_id, a.name, a.description, a.start_time, a.end_time, a.organizer,
                   a.facility_id, f.name AS facility_name, b.name AS building_name, c.name AS campus_name,
                   count(ua.user_id) AS participant_count
            FROM activity a
            JOIN facility f ON f.facility_id = a.facility_id
            JOIN building b ON b.building_id = f.building_id
            JOIN campus c ON c.campus_id = b.campus_id
            LEFT JOIN user_activity ua ON ua.activity_id = a.activity_id
            {where}
            GROUP BY a.activity_id, f.name, b.name, c.name
            ORDER BY a.start_time, a.activity_id
            """,
            tuple(params),
        )

    def create_activity(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = clean_text(payload, "name")
        description = clean_text(payload, "description", default="暂无简介")
        start_time = parse_datetime_text(clean_text(payload, "start_time"))
        end_time = parse_datetime_text(clean_text(payload, "end_time", required=False, default=""))
        organizer = clean_text(payload, "organizer", default="未填写")
        facility_id = clean_int(payload, "facility_id")
        return self.execute_returning(
            """
            INSERT INTO activity (name, description, start_time, end_time, organizer, facility_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING activity_id, name, description, start_time, end_time, organizer, facility_id
            """,
            (name, description, start_time, end_time, organizer, facility_id),
        )

    def update_activity(self, activity_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        name = clean_text(payload, "name")
        description = clean_text(payload, "description", default="暂无简介")
        start_time = parse_datetime_text(clean_text(payload, "start_time"))
        end_time = parse_datetime_text(clean_text(payload, "end_time", required=False, default=""))
        organizer = clean_text(payload, "organizer", default="未填写")
        facility_id = clean_int(payload, "facility_id")
        return self.execute_returning(
            """
            UPDATE activity
            SET name = %s, description = %s, start_time = %s, end_time = %s, organizer = %s, facility_id = %s
            WHERE activity_id = %s
            RETURNING activity_id, name, description, start_time, end_time, organizer, facility_id
            """,
            (name, description, start_time, end_time, organizer, facility_id, activity_id),
        )

    def delete_activity(self, activity_id: int) -> dict[str, Any]:
        affected = self.execute_count("DELETE FROM activity WHERE activity_id = %s", (activity_id,))
        if affected == 0:
            raise ApiError(HTTPStatus.NOT_FOUND, "活动不存在")
        return {"deleted": affected}

    def create_query_log(self, payload: dict[str, Any]) -> dict[str, Any]:
        user_id = clean_int(payload, "user_id")
        category = clean_text(payload, "query_category", default="其他")
        content = clean_text(payload, "query_content")
        if category not in QUERY_CATEGORIES:
            raise ApiError(HTTPStatus.BAD_REQUEST, "查询类别不在允许范围内")
        return self.execute_returning(
            """
            INSERT INTO query_log (user_id, query_category, query_content)
            VALUES (%s, %s, %s)
            RETURNING log_id, user_id, query_category, query_content, query_time
            """,
            (user_id, category, content),
        )

    def sql_examples(self) -> list[dict[str, Any]]:
        examples = []
        for item in SQL_EXAMPLES:
            examples.append({**item, "rows": self.fetch_all(item["sql"])})
        return examples


class DemoRepository(PostgresRepository):
    mode = "demo"

    def __init__(self):
        self.campus_rows = [
            {"campus_id": 1, "name": "邯郸校区", "address": "上海市杨浦区邯郸路220号"},
            {"campus_id": 2, "name": "江湾校区", "address": "上海市杨浦区淞沪路2005号"},
            {"campus_id": 3, "name": "枫林校区", "address": "上海市徐汇区医学院路138号"},
            {"campus_id": 4, "name": "张江校区", "address": "上海市浦东新区张衡路825号"},
        ]
        self.building_rows = [
            {"building_id": 1, "name": "光华楼", "type": "综合楼", "campus_id": 1},
            {"building_id": 2, "name": "第二教学楼", "type": "教学楼", "campus_id": 1},
            {"building_id": 3, "name": "文科图书馆", "type": "图书馆", "campus_id": 1},
            {"building_id": 4, "name": "江湾体育馆", "type": "体育场馆", "campus_id": 2},
            {"building_id": 5, "name": "枫林图书馆", "type": "图书馆", "campus_id": 3},
            {"building_id": 6, "name": "张江实验楼", "type": "实验楼", "campus_id": 4},
        ]
        self.facility_rows = [
            {"facility_id": 1, "name": "光华楼东辅楼102", "type": "教室", "open_time": "每日 08:00-22:00", "building_id": 1},
            {"facility_id": 2, "name": "光华楼报告厅", "type": "报告厅", "open_time": "工作日 09:00-21:00", "building_id": 1},
            {"facility_id": 3, "name": "H2201", "type": "教室", "open_time": "每日 07:30-22:30", "building_id": 2},
            {"facility_id": 4, "name": "H2303自习室", "type": "自习室", "open_time": "每日 08:00-23:00", "building_id": 2},
            {"facility_id": 5, "name": "文科图书馆阅览室", "type": "图书阅览室", "open_time": "周一至周日 08:00-22:00", "building_id": 3},
            {"facility_id": 6, "name": "江湾篮球馆", "type": "体育设施", "open_time": "周一至周日 09:00-21:00", "building_id": 4},
            {"facility_id": 8, "name": "张江AI实验室", "type": "实验室", "open_time": "工作日 09:00-18:00", "building_id": 6},
        ]
        self.activity_rows = [
            {"activity_id": 1, "name": "新生数据库实践讲座", "description": "介绍数据库建模和查询优化。", "start_time": "2026-05-20 14:00:00", "end_time": "2026-05-20 16:00:00", "organizer": "计算机科学技术学院", "facility_id": 2, "participant_count": 3},
            {"activity_id": 2, "name": "校园开放日导览", "description": "邯郸校区建筑与学习空间导览。", "start_time": "2026-05-18 09:00:00", "end_time": "2026-05-18 11:00:00", "organizer": "招生办公室", "facility_id": 1, "participant_count": 2},
            {"activity_id": 3, "name": "江湾篮球友谊赛", "description": "校内篮球社团交流赛。", "start_time": "2026-05-24 18:00:00", "end_time": "2026-05-24 20:00:00", "organizer": "体育教学部", "facility_id": 6, "participant_count": 1},
        ]
        self.next_building_id = 7
        self.next_facility_id = 9
        self.next_activity_id = 4
        self.next_log_id = 11

    def ping(self) -> bool:
        return True

    def _campus_name(self, campus_id: int) -> str:
        return next((c["name"] for c in self.campus_rows if c["campus_id"] == campus_id), "")

    def _building(self, building_id: int) -> dict[str, Any] | None:
        return next((b for b in self.building_rows if b["building_id"] == building_id), None)

    def _facility(self, facility_id: int) -> dict[str, Any] | None:
        return next((f for f in self.facility_rows if f["facility_id"] == facility_id), None)

    def _decorate_building(self, row: dict[str, Any]) -> dict[str, Any]:
        return {**row, "campus_name": self._campus_name(row["campus_id"])}

    def _decorate_facility(self, row: dict[str, Any]) -> dict[str, Any]:
        building = self._building(row["building_id"]) or {}
        return {
            **row,
            "building_name": building.get("name", ""),
            "campus_name": self._campus_name(building.get("campus_id", 0)),
        }

    def _decorate_activity(self, row: dict[str, Any]) -> dict[str, Any]:
        facility = self._facility(row["facility_id"]) or {}
        building = self._building(facility.get("building_id", 0)) or {}
        return {
            **row,
            "facility_name": facility.get("name", ""),
            "building_name": building.get("name", ""),
            "campus_name": self._campus_name(building.get("campus_id", 0)),
        }

    def _filter(self, rows: list[dict[str, Any]], q: str, keys: list[str]) -> list[dict[str, Any]]:
        if not q:
            return rows
        return [row for row in rows if any(q in str(row.get(key, "")) for key in keys)]

    def campuses(self, query: dict[str, str]) -> list[dict[str, Any]]:
        return self._filter(self.campus_rows, query.get("q", "").strip(), ["name", "address"])

    def buildings(self, query: dict[str, str]) -> list[dict[str, Any]]:
        rows = [self._decorate_building(row) for row in self.building_rows]
        if query.get("campus_id"):
            rows = [row for row in rows if row["campus_id"] == int(query["campus_id"])]
        return self._filter(rows, query.get("q", "").strip(), ["name", "type", "campus_name"])

    def create_building(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "building_id": self.next_building_id,
            "name": clean_text(payload, "name"),
            "type": clean_text(payload, "type", default="其他"),
            "campus_id": clean_int(payload, "campus_id"),
        }
        self.next_building_id += 1
        self.building_rows.append(row)
        return self._decorate_building(row)

    def update_building(self, building_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        row = self._building(building_id)
        if row is None:
            raise ApiError(HTTPStatus.NOT_FOUND, "建筑不存在")
        row.update({"name": clean_text(payload, "name"), "type": clean_text(payload, "type"), "campus_id": clean_int(payload, "campus_id")})
        return self._decorate_building(row)

    def delete_building(self, building_id: int) -> dict[str, Any]:
        if any(f["building_id"] == building_id for f in self.facility_rows):
            raise ApiError(HTTPStatus.BAD_REQUEST, "该建筑下仍有设施，演示约束模拟为禁止删除")
        before = len(self.building_rows)
        self.building_rows = [row for row in self.building_rows if row["building_id"] != building_id]
        if len(self.building_rows) == before:
            raise ApiError(HTTPStatus.NOT_FOUND, "建筑不存在")
        return {"deleted": 1}

    def facilities(self, query: dict[str, str]) -> list[dict[str, Any]]:
        rows = [self._decorate_facility(row) for row in self.facility_rows]
        if query.get("building_id"):
            rows = [row for row in rows if row["building_id"] == int(query["building_id"])]
        return self._filter(rows, query.get("q", "").strip(), ["name", "type", "building_name", "campus_name"])

    def create_facility(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "facility_id": self.next_facility_id,
            "name": clean_text(payload, "name"),
            "type": clean_text(payload, "type", default="其他"),
            "open_time": clean_text(payload, "open_time", default="以现场公告为准"),
            "building_id": clean_int(payload, "building_id"),
        }
        self.next_facility_id += 1
        self.facility_rows.append(row)
        return self._decorate_facility(row)

    def update_facility(self, facility_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        row = self._facility(facility_id)
        if row is None:
            raise ApiError(HTTPStatus.NOT_FOUND, "设施不存在")
        row.update({
            "name": clean_text(payload, "name"),
            "type": clean_text(payload, "type"),
            "open_time": clean_text(payload, "open_time"),
            "building_id": clean_int(payload, "building_id"),
        })
        return self._decorate_facility(row)

    def delete_facility(self, facility_id: int) -> dict[str, Any]:
        before = len(self.facility_rows)
        self.facility_rows = [row for row in self.facility_rows if row["facility_id"] != facility_id]
        if len(self.facility_rows) == before:
            raise ApiError(HTTPStatus.NOT_FOUND, "设施不存在")
        return {"deleted": 1}

    def courses(self, query: dict[str, str]) -> list[dict[str, Any]]:
        rows = [
            {"offering_id": 1, "course_code": "COMP130015.01", "semester": "2025-2026 春季学期", "course_master_code": "COMP130015", "course_name": "数据库系统原理", "teachers": "李芳", "schedules": "周一 3-4节 每周 @ H2201；周三 3-4节 双周 @ 张江AI实验室"},
            {"offering_id": 3, "course_code": "COMP130136.01", "semester": "2025-2026 春季学期", "course_master_code": "COMP130136", "course_name": "人工智能导论", "teachers": "李芳", "schedules": "周四 7-8节 每周 @ 张江AI实验室"},
            {"offering_id": 5, "course_code": "JOUR110001.01", "semester": "2025-2026 春季学期", "course_master_code": "JOUR110001", "course_name": "新闻传播导论", "teachers": "王强", "schedules": "周二 3-4节 每周 @ 文科图书馆阅览室"},
        ]
        return self._filter(rows, query.get("q", "").strip(), ["course_name", "course_code", "teachers"])

    def activities(self, query: dict[str, str]) -> list[dict[str, Any]]:
        rows = [self._decorate_activity(row) for row in self.activity_rows]
        return self._filter(rows, query.get("q", "").strip(), ["name", "description", "organizer", "facility_name"])

    def create_activity(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "activity_id": self.next_activity_id,
            "name": clean_text(payload, "name"),
            "description": clean_text(payload, "description", default="暂无简介"),
            "start_time": parse_datetime_text(clean_text(payload, "start_time")),
            "end_time": parse_datetime_text(clean_text(payload, "end_time", required=False, default="")),
            "organizer": clean_text(payload, "organizer", default="未填写"),
            "facility_id": clean_int(payload, "facility_id"),
            "participant_count": 0,
        }
        self.next_activity_id += 1
        self.activity_rows.append(row)
        return self._decorate_activity(row)

    def update_activity(self, activity_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        row = next((item for item in self.activity_rows if item["activity_id"] == activity_id), None)
        if row is None:
            raise ApiError(HTTPStatus.NOT_FOUND, "活动不存在")
        row.update({
            "name": clean_text(payload, "name"),
            "description": clean_text(payload, "description"),
            "start_time": parse_datetime_text(clean_text(payload, "start_time")),
            "end_time": parse_datetime_text(clean_text(payload, "end_time", required=False, default="")),
            "organizer": clean_text(payload, "organizer"),
            "facility_id": clean_int(payload, "facility_id"),
        })
        return self._decorate_activity(row)

    def delete_activity(self, activity_id: int) -> dict[str, Any]:
        before = len(self.activity_rows)
        self.activity_rows = [row for row in self.activity_rows if row["activity_id"] != activity_id]
        if len(self.activity_rows) == before:
            raise ApiError(HTTPStatus.NOT_FOUND, "活动不存在")
        return {"deleted": 1}

    def create_query_log(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "log_id": self.next_log_id,
            "user_id": clean_int(payload, "user_id"),
            "query_category": clean_text(payload, "query_category", default="其他"),
            "query_content": clean_text(payload, "query_content"),
            "query_time": datetime.now().isoformat(sep=" ", timespec="seconds"),
        }
        self.next_log_id += 1
        return row

    def sql_examples(self) -> list[dict[str, Any]]:
        return [
            {**SQL_EXAMPLES[0], "rows": [{"campus_name": "邯郸校区", "building_name": "光华楼", "type": "综合楼"}, {"campus_name": "邯郸校区", "building_name": "第二教学楼", "type": "教学楼"}]},
            {**SQL_EXAMPLES[1], "rows": [{"building_name": "第二教学楼", "facility_name": "H2201", "type": "教室", "open_time": "每日 07:30-22:30"}, {"building_name": "第二教学楼", "facility_name": "H2303自习室", "type": "自习室", "open_time": "每日 08:00-23:00"}]},
            {**SQL_EXAMPLES[2], "rows": [{"teacher_name": "李芳", "course_name": "数据库系统原理", "course_code": "COMP130015.01", "semester": "2025-2026 春季学期"}, {"teacher_name": "李芳", "course_name": "人工智能导论", "course_code": "COMP130136.01", "semester": "2025-2026 春季学期"}]},
            {**SQL_EXAMPLES[3], "rows": [{"activity_name": "校园开放日导览", "start_time": "2026-05-18 09:00:00", "campus_name": "邯郸校区", "building_name": "光华楼", "facility_name": "光华楼东辅楼102"}]},
            {**SQL_EXAMPLES[4], "rows": [{"campus_name": "邯郸校区", "type": "教学楼", "building_count": 1}, {"campus_name": "邯郸校区", "type": "图书馆", "building_count": 1}]},
            {**SQL_EXAMPLES[5], "rows": [{"query_category": "活动", "query_count": 2}, {"query_category": "设施", "query_count": 2}]},
            {**SQL_EXAMPLES[6], "rows": [{"activity_name": "新生数据库实践讲座", "participant_count": 3}, {"activity_name": "校园开放日导览", "participant_count": 2}]},
        ]


SQL_EXAMPLES = [
    {
        "key": "campus_buildings",
        "title": "查询邯郸校区建筑列表",
        "sql": """
SELECT c.name AS campus_name, b.name AS building_name, b.type
FROM campus c
JOIN building b ON b.campus_id = c.campus_id
WHERE c.name = '邯郸校区'
ORDER BY b.name
""".strip(),
    },
    {
        "key": "building_facilities",
        "title": "查询第二教学楼设施",
        "sql": """
SELECT b.name AS building_name, f.name AS facility_name, f.type, f.open_time
FROM building b
JOIN facility f ON f.building_id = b.building_id
WHERE b.name = '第二教学楼'
ORDER BY f.name
""".strip(),
    },
    {
        "key": "teacher_courses",
        "title": "查询李芳老师授课列表",
        "sql": """
SELECT u.name AS teacher_name, c.name AS course_name, co.course_code, co.semester
FROM users u
JOIN teacher t ON t.user_id = u.user_id
JOIN course_offering_teacher cot ON cot.teacher_id = t.user_id
JOIN course_offering co ON co.offering_id = cot.offering_id
JOIN course_section cs ON cs.course_code = co.course_code
JOIN course c ON c.course_master_code = cs.course_master_code
WHERE u.name = '李芳'
ORDER BY c.name, co.course_code
""".strip(),
    },
    {
        "key": "recent_activities",
        "title": "查询近期校园活动",
        "sql": """
SELECT a.name AS activity_name, a.start_time, c.name AS campus_name, b.name AS building_name, f.name AS facility_name
FROM activity a
JOIN facility f ON f.facility_id = a.facility_id
JOIN building b ON b.building_id = f.building_id
JOIN campus c ON c.campus_id = b.campus_id
WHERE a.start_time >= TIMESTAMP '2026-05-11 00:00:00'
ORDER BY a.start_time
""".strip(),
    },
    {
        "key": "building_stats",
        "title": "统计每个校区各类建筑数量",
        "sql": """
SELECT c.name AS campus_name, b.type, count(*) AS building_count
FROM campus c
JOIN building b ON b.campus_id = c.campus_id
GROUP BY c.name, b.type
ORDER BY c.name, b.type
""".strip(),
    },
    {
        "key": "query_categories",
        "title": "统计热门查询类别",
        "sql": """
SELECT query_category, count(*) AS query_count
FROM query_log
GROUP BY query_category
ORDER BY query_count DESC, query_category
""".strip(),
    },
    {
        "key": "hot_activities",
        "title": "统计热门活动",
        "sql": """
SELECT a.name AS activity_name, count(ua.user_id) AS participant_count
FROM activity a
LEFT JOIN user_activity ua ON ua.activity_id = a.activity_id
GROUP BY a.activity_id, a.name
ORDER BY participant_count DESC, a.name
""".strip(),
    },
]


repository: PostgresRepository = DemoRepository() if DEMO_MODE else PostgresRepository(DATABASE_URL)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "FCQA/0.1"

    def do_GET(self) -> None:
        self.dispatch("GET")

    def do_POST(self) -> None:
        self.dispatch("POST")

    def do_PUT(self) -> None:
        self.dispatch("PUT")

    def do_DELETE(self) -> None:
        self.dispatch("DELETE")

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api(method, parsed.path, parse_qs(parsed.query))
            return
        self.serve_static(parsed.path)

    def handle_api(self, method: str, path: str, raw_query: dict[str, list[str]]) -> None:
        query = {key: values[-1] for key, values in raw_query.items() if values}
        try:
            data = self.route_api(method, path, query)
            self.send_json(data)
        except ApiError as exc:
            self.send_json({"error": exc.message}, status=exc.status)
        except Exception as exc:
            self.send_json({"error": f"服务内部错误：{exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def route_api(self, method: str, path: str, query: dict[str, str]) -> Any:
        if method == "GET" and path == "/api/health":
            return self.health()
        if method == "GET" and path == "/api/meta":
            return {"building_types": BUILDING_TYPES, "facility_types": FACILITY_TYPES, "query_categories": QUERY_CATEGORIES}
        if method == "GET" and path == "/api/campuses":
            return {"items": repository.campuses(query)}
        if method == "GET" and path == "/api/buildings":
            return {"items": repository.buildings(query)}
        if method == "POST" and path == "/api/buildings":
            return {"item": repository.create_building(self.read_json())}
        if method == "GET" and path == "/api/facilities":
            return {"items": repository.facilities(query)}
        if method == "POST" and path == "/api/facilities":
            return {"item": repository.create_facility(self.read_json())}
        if method == "GET" and path == "/api/courses":
            return {"items": repository.courses(query)}
        if method == "GET" and path == "/api/activities":
            return {"items": repository.activities(query)}
        if method == "POST" and path == "/api/activities":
            return {"item": repository.create_activity(self.read_json())}
        if method == "POST" and path == "/api/query-log":
            return {"item": repository.create_query_log(self.read_json())}
        if method == "GET" and path == "/api/sql-examples":
            return {"items": repository.sql_examples()}

        building_match = re.fullmatch(r"/api/buildings/(\d+)", path)
        if building_match:
            building_id = int(building_match.group(1))
            if method == "PUT":
                return {"item": repository.update_building(building_id, self.read_json())}
            if method == "DELETE":
                return repository.delete_building(building_id)

        facility_match = re.fullmatch(r"/api/facilities/(\d+)", path)
        if facility_match:
            facility_id = int(facility_match.group(1))
            if method == "PUT":
                return {"item": repository.update_facility(facility_id, self.read_json())}
            if method == "DELETE":
                return repository.delete_facility(facility_id)

        activity_match = re.fullmatch(r"/api/activities/(\d+)", path)
        if activity_match:
            activity_id = int(activity_match.group(1))
            if method == "PUT":
                return {"item": repository.update_activity(activity_id, self.read_json())}
            if method == "DELETE":
                return repository.delete_activity(activity_id)

        raise ApiError(HTTPStatus.NOT_FOUND, "接口不存在")

    def health(self) -> dict[str, Any]:
        try:
            repository.ping()
            database = {"connected": True, "mode": repository.mode}
        except ApiError as exc:
            database = {"connected": False, "mode": repository.mode, "error": exc.message}
        return {"service": "ok", "database": database}

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(HTTPStatus.BAD_REQUEST, "请求体不是合法 JSON") from exc

    def send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=json_default).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def serve_static(self, path: str) -> None:
        if path in {"", "/"}:
            path = "/index.html"
        requested = (FRONTEND_DIR / path.lstrip("/")).resolve()
        if FRONTEND_DIR not in requested.parents and requested != FRONTEND_DIR:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not requested.exists() or not requested.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = "text/plain; charset=utf-8"
        if requested.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif requested.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif requested.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        body = requested.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    mode_text = "demo data" if DEMO_MODE else f"PostgreSQL {DATABASE_URL}"
    print(f"FCQA server listening on http://{HOST}:{PORT} ({mode_text})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
