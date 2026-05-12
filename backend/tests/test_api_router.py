from __future__ import annotations

import unittest
from http import HTTPStatus

import context  # noqa: F401
from fcqa.api import ApiRouter
from fcqa.errors import ApiError
from fcqa.repositories.demo import DemoRepository


class ApiRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = ApiRouter(DemoRepository())

    def test_health_uses_repository_mode(self) -> None:
        result = self.router.route("GET", "/api/health")
        self.assertEqual(result["service"], "ok")
        self.assertEqual(result["database"]["mode"], "demo")

    def test_meta_returns_allowed_values(self) -> None:
        result = self.router.route("GET", "/api/meta")
        self.assertIn("教学楼", result["building_types"])
        self.assertIn("自习室", result["facility_types"])

    def test_create_update_delete_building_route(self) -> None:
        created = self.router.route(
            "POST",
            "/api/buildings",
            read_payload=lambda: {"name": "路由测试楼", "type": "教学楼", "campus_id": 1},
        )["item"]
        building_id = created["building_id"]

        updated = self.router.route(
            "PUT",
            f"/api/buildings/{building_id}",
            read_payload=lambda: {"name": "路由测试楼A", "type": "综合楼", "campus_id": 1},
        )["item"]
        self.assertEqual(updated["name"], "路由测试楼A")

        deleted = self.router.route("DELETE", f"/api/buildings/{building_id}")
        self.assertEqual(deleted, {"deleted": 1})

    def test_unknown_route_raises_404(self) -> None:
        with self.assertRaises(ApiError) as raised:
            self.router.route("GET", "/api/missing")
        self.assertEqual(raised.exception.status, HTTPStatus.NOT_FOUND)

    def test_query_browse_routes_return_items(self) -> None:
        history = self.router.route("GET", "/api/query-logs")["items"]
        popular_queries = self.router.route("GET", "/api/insights/popular-queries")["items"]
        popular_activities = self.router.route("GET", "/api/insights/popular-activities")["items"]

        self.assertGreaterEqual(len(history), 1)
        self.assertGreaterEqual(len(popular_queries), 1)
        self.assertGreaterEqual(len(popular_activities), 1)
        self.assertIn("query_content", history[0])
        self.assertIn("query_count", popular_queries[0])
        self.assertIn("participant_count", popular_activities[0])

    def test_user_reservation_routes(self) -> None:
        users = self.router.route("GET", "/api/users")["items"]
        self.assertGreaterEqual(len(users), 1)

        created = self.router.route(
            "POST",
            "/api/activities/3/reserve",
            read_payload=lambda: {"user_id": 4},
        )["item"]
        self.assertEqual(created["user_id"], 4)
        self.assertEqual(created["activity_id"], 3)

        reservations = self.router.route("GET", "/api/users/4/reservations")["items"]
        self.assertTrue(any(item["activity_id"] == 3 for item in reservations))

        deleted = self.router.route("DELETE", "/api/activities/3/reserve/4")
        self.assertEqual(deleted, {"deleted": 1})


if __name__ == "__main__":
    unittest.main()
