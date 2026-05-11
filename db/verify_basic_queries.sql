-- Basic verification queries for the campus QA database.
-- Run after db/init.sql:
--   psql -v ON_ERROR_STOP=1 -d fcqa -f db/verify_basic_queries.sql

\set ON_ERROR_STOP on

SELECT 'users' AS table_name, count(*) AS row_count FROM users
UNION ALL SELECT 'teacher', count(*) FROM teacher
UNION ALL SELECT 'student', count(*) FROM student
UNION ALL SELECT 'campus', count(*) FROM campus
UNION ALL SELECT 'building', count(*) FROM building
UNION ALL SELECT 'facility', count(*) FROM facility
UNION ALL SELECT 'course', count(*) FROM course
UNION ALL SELECT 'course_offering', count(*) FROM course_offering
UNION ALL SELECT 'activity', count(*) FROM activity
UNION ALL SELECT 'query_log', count(*) FROM query_log
UNION ALL SELECT 'user_activity', count(*) FROM user_activity
ORDER BY table_name;

-- 查询某个校区的建筑列表。
SELECT c.name AS campus_name, b.name AS building_name, b.type
FROM campus c
JOIN building b ON b.campus_id = c.campus_id
WHERE c.name = '邯郸校区'
ORDER BY b.name;

-- 查询某栋建筑中的设施信息。
SELECT b.name AS building_name, f.name AS facility_name, f.type, f.open_time
FROM building b
JOIN facility f ON f.building_id = b.building_id
WHERE b.name = '第二教学楼'
ORDER BY f.name;

-- 查询某位教师所教授的课程列表。
SELECT u.name AS teacher_name, c.name AS course_name, co.course_code, co.semester
FROM users u
JOIN teacher t ON t.user_id = u.user_id
JOIN course_offering_teacher cot ON cot.teacher_id = t.user_id
JOIN course_offering co ON co.offering_id = cot.offering_id
JOIN course_section cs ON cs.course_code = co.course_code
JOIN course c ON c.course_master_code = cs.course_master_code
WHERE u.name = '李芳'
ORDER BY c.name, co.course_code;

-- 查询近期校园活动及其校区、建筑、设施。
SELECT a.name AS activity_name, a.start_time, c.name AS campus_name, b.name AS building_name, f.name AS facility_name
FROM activity a
JOIN facility f ON f.facility_id = a.facility_id
JOIN building b ON b.building_id = f.building_id
JOIN campus c ON c.campus_id = b.campus_id
WHERE a.start_time >= TIMESTAMP '2026-05-11 00:00:00'
ORDER BY a.start_time;

-- 统计每个校区各类建筑数量。
SELECT c.name AS campus_name, b.type, count(*) AS building_count
FROM campus c
JOIN building b ON b.campus_id = c.campus_id
GROUP BY c.name, b.type
ORDER BY c.name, b.type;

-- 统计最常被查询的校园信息类别。
SELECT query_category, count(*) AS query_count
FROM query_log
GROUP BY query_category
ORDER BY query_count DESC, query_category;

-- 统计热门活动。
SELECT a.name AS activity_name, count(ua.user_id) AS participant_count
FROM activity a
LEFT JOIN user_activity ua ON ua.activity_id = a.activity_id
GROUP BY a.activity_id, a.name
ORDER BY participant_count DESC, a.name;
