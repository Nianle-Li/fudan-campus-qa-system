# Seed Data

`001_initial_data.sql` 是本项目的初始测试数据脚本，覆盖：

- 用户、教师、学生
- 校区、建筑、设施
- 课程、课程班次、课程开设、授课教师、排课时段
- 活动、用户活动参与、查询记录

建议在建表和索引完成后导入：

```bash
psql -v ON_ERROR_STOP=1 -d fcqa -f db/seeds/001_initial_data.sql
```

也可以直接从仓库根目录执行完整初始化入口：

```bash
psql -v ON_ERROR_STOP=1 -d fcqa -f db/init.sql
```
