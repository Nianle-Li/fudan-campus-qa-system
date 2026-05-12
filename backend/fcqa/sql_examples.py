from __future__ import annotations

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
