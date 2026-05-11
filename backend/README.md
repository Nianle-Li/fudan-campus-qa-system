# Backend

轻量后端服务，负责把前端请求转换为 PostgreSQL 查询和写入操作，并提供阶段演示用的关键 SQL 查询结果。

## 运行方式

先初始化数据库：

```bash
createdb fcqa
psql -v ON_ERROR_STOP=1 -d fcqa -f db/init.sql
```

安装 PostgreSQL 驱动：

```bash
python -m pip install -r backend/requirements.txt
```

启动服务：

```bash
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fcqa"
python backend/app.py
```

默认访问地址为 `http://127.0.0.1:8000`。后端会同时托管 `frontend/` 静态页面。

如果当前机器暂时没有 PostgreSQL，可使用内置演示数据预览前后端交互：

```bash
$env:FCQA_DEMO_MODE="1"
python backend/app.py
```

演示模式只用于界面预览；正式联调请使用 PostgreSQL。

## 主要 API

- `GET /api/health`：服务与数据库连接状态
- `GET /api/campuses`：校区查询
- `GET/POST/PUT/DELETE /api/buildings`：建筑查询与维护
- `GET/POST/PUT/DELETE /api/facilities`：设施查询与维护
- `GET /api/courses`：课程、教师、排课综合查询
- `GET/POST/PUT/DELETE /api/activities`：活动查询与维护
- `POST /api/query-log`：写入用户查询记录
- `GET /api/sql-examples`：执行并展示关键 SQL 查询效果
