from __future__ import annotations

import unittest
from http import HTTPStatus

import context  # noqa: F401
from fcqa.errors import ApiError
from fcqa.repositories.demo import DemoRepository


class DemoRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = DemoRepository()

    def test_building_lifecycle(self) -> None:
        created = self.repository.create_building({"name": "测试楼", "type": "教学楼", "campus_id": 1})
        self.assertEqual(created["campus_name"], "邯郸校区")

        updated = self.repository.update_building(
            created["building_id"],
            {"name": "测试楼A", "type": "综合楼", "campus_id": 1},
        )
        self.assertEqual(updated["name"], "测试楼A")

        deleted = self.repository.delete_building(created["building_id"])
        self.assertEqual(deleted, {"deleted": 1})

    def test_delete_building_with_facilities_is_rejected(self) -> None:
        with self.assertRaises(ApiError) as raised:
            self.repository.delete_building(1)
        self.assertEqual(raised.exception.status, HTTPStatus.BAD_REQUEST)

    def test_natural_language_query_returns_demo_rows(self) -> None:
        result = self.repository.natural_language_query({"question": "李芳老师教什么课？"})
        self.assertEqual(result["intent"], "teacher_courses")
        self.assertGreaterEqual(result["row_count"], 1)
        self.assertIn("SELECT", result["sql"])

    def test_query_logs_include_written_records(self) -> None:
        self.repository.create_query_log({"user_id": 4, "query_category": "其他", "query_content": "测试查询"})
        rows = self.repository.query_logs({"q": "测试查询"})
        self.assertEqual(rows[0]["query_content"], "测试查询")

    def test_popular_browse_methods(self) -> None:
        popular_queries = self.repository.popular_queries({})
        popular_activities = self.repository.popular_activities({})

        self.assertGreaterEqual(popular_queries[0]["query_count"], 1)
        self.assertGreaterEqual(popular_activities[0]["participant_count"], 1)

    def test_activity_reservation_lifecycle(self) -> None:
        created = self.repository.reserve_activity(3, {"user_id": 4})
        self.assertEqual(created["status"], "待参加")

        reservations = self.repository.user_reservations(4)
        self.assertTrue(any(row["activity_id"] == 3 for row in reservations))

        deleted = self.repository.cancel_activity_reservation(3, 4)
        self.assertEqual(deleted, {"deleted": 1})


if __name__ == "__main__":
    unittest.main()
