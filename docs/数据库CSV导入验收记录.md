# 数据库 CSV 导入验收记录

本文档用于证明仓库已提供从空库出发的统一 CSV 初始化入口，并给出导入后的可复现验收结果。验收命令均从仓库根目录执行。

## 初始化命令

本机 PostgreSQL：

```bash
createdb fcqa
psql -v ON_ERROR_STOP=1 -d fcqa -f db/init_csv.sql
psql -v ON_ERROR_STOP=1 -d fcqa -f db/verify_basic_queries.sql
```

Docker Compose：

```bash
docker compose up -d db
docker compose exec -w /opt/fcqa db psql -v ON_ERROR_STOP=1 -U postgres -d fcqa -f db/init_csv.sql
docker compose exec -w /opt/fcqa db psql -v ON_ERROR_STOP=1 -U postgres -d fcqa -f db/verify_basic_queries.sql
```

`db/init_csv.sql` 会依次执行建表、CSV 导入和序列重置；`db/seeds/import_csv.sql` 会按外键依赖顺序导入 `db/seeds/csv/` 下的 14 份 CSV。

## 行数验收

执行 `db/verify_basic_queries.sql` 后，CSV 演示数据的行数应为：

```text
table_name                 | row_count
---------------------------+----------
activity                   | 15
building                   | 15
campus                     | 4
course                     | 20
course_offering            | 30
course_offering_schedule   | 60
course_offering_teacher    | 33
course_section             | 25
facility                   | 37
query_log                  | 100
student                    | 38
teacher                    | 12
user_activity              | 60
users                      | 50
```

## 序列验收

CSV 使用显式主键导入，因此导入完成后需要重置 `SERIAL` 序列。验收查询应能看到序列值已经推进到当前最大 ID：

```text
sequencename                         | last_value
-------------------------------------+-----------
activity_activity_id_seq             | 4015
building_building_id_seq             | 115
campus_campus_id_seq                 | 4
course_offering_offering_id_seq      | 3030
facility_facility_id_seq             | 1037
query_log_log_id_seq                 | 5100
users_user_id_seq                    | 2050
```

## 示例查询结果

按校区查询建筑：

```text
campus_name | building_name | type
------------+---------------+--------
邯郸校区    | 旦苑食堂      | 食堂
邯郸校区    | 第二教学楼    | 教学楼
邯郸校区    | 光华楼东辅楼  | 综合楼
邯郸校区    | 南区学生服务中心 | 综合楼
邯郸校区    | 文科图书馆    | 图书馆
```

按建筑查询设施：

```text
building_name | facility_name  | type   | open_time
--------------+----------------+--------+-------------------
第二教学楼    | H2201          | 教室   | 工作日 08:00-21:30
第二教学楼    | H2208          | 教室   | 工作日 08:00-21:30
第二教学楼    | H2303          | 教室   | 工作日 08:00-21:30
第二教学楼    | 第二教学楼报告厅 | 报告厅 | 工作日 09:00-21:00
```

按教师查询课程，节选结果：

```text
teacher_name | course_name  | course_code   | semester
-------------+--------------+---------------+--------------------
陈明远       | 操作系统     | COMP130108.01 | 2025-2026 秋季学期
陈明远       | 程序设计基础 | COMP130009.01 | 2025-2026 秋季学期
陈明远       | 计算机网络   | COMP130021.01 | 2025-2026 秋季学期
陈明远       | 人工智能导论 | COMP130030.01 | 2025-2026 秋季学期
陈明远       | 数据结构     | COMP130012.01 | 2025-2026 春季学期
陈明远       | 数据库系统   | COMP130015.01 | 2025-2026 秋季学期
```

活动与地点关联，节选结果：

```text
activity_name                         | start_time          | campus_name | building_name     | facility_name
--------------------------------------+---------------------+-------------+-------------------+----------------
计算与智能创新学院新生科研导引讲座   | 2025-09-15 18:30:00 | 邯郸校区    | 第二教学楼        | 第二教学楼报告厅
计算与智能创新学院数据库与数据智能竞赛宣讲会 | 2025-09-20 18:30:00 | 邯郸校区 | 光华楼东辅楼 | 光华楼报告厅
职涯咨询开放日                       | 2025-09-25 13:30:00 | 邯郸校区    | 南区学生服务中心  | 学生事务大厅
智能材料与未来能源创新学院实验室安全培训 | 2025-09-28 14:00:00 | 江湾校区 | 先进材料实验楼 | 材料实验室A
枫林校区健康跑                       | 2025-10-08 16:30:00 | 枫林校区    | 枫林体育中心      | 枫林健身房
```

查询日志分类统计：

```text
query_category | query_count
---------------+------------
课程           | 22
活动           | 16
设施           | 11
建筑           | 10
统计           | 9
用户           | 9
教师           | 8
其他           | 8
校区           | 7
```

## 写入联调验收

`db/verify_basic_queries.sql` 末尾包含事务内写入并回滚的冒烟测试。CSV 数据导入后，插入临时用户时应返回一条临时记录，并在事务内看到用户数临时增加为 51：

```text
user_id | name         | department
--------+--------------+--------------
999999  | 验收临时用户 | 数据库联调测试

user_count_inside_transaction
-----------------------------
51
```

随后执行 `ROLLBACK`，演示数据保持为 50 个用户。
