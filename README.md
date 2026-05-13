# fudan-campus-qa-system

复旦校园百事通问答系统数据库设计课程项目。

## 小组成员

李佳凝（Nianle-Li），刘嘉文（posaka），卢浩达（Haoda Lu）

## 项目概览

- 项目主题：复旦校园百事通问答系统
- 数据库：PostgreSQL 16
- 当前状态：已完成需求分析、关系模式设计、规范化分析、逻辑结构定稿、数据库物理实现、约束与索引落地、测试数据导入和基础验收查询。
- 验收建议：优先使用 Docker Compose 直接启动数据库并执行验收脚本，路径最短、结果最直观。

## 快速验收

推荐在仓库根目录执行以下命令：

```bash
docker compose up -d db
docker compose exec db psql -P pager=off -v ON_ERROR_STOP=1 -U postgres -d fcqa -f /opt/fcqa/db/verify_basic_queries.sql
```

这两条命令分别完成：

1. 启动 PostgreSQL 容器，并在首次建卷时自动执行 [db/init.sql](db/init.sql) 初始化表结构、约束、索引和初始 SQL 测试数据。
2. 执行 [db/verify_basic_queries.sql](db/verify_basic_queries.sql) 展示基础查询、聚合统计和事务写入回滚能力。

如果需要展示更大规模的 CSV 演示数据，可执行：

```bash
docker compose up -d db
docker compose exec -w /opt/fcqa db psql -P pager=off -v ON_ERROR_STOP=1 -U postgres -d fcqa -f db/init_csv.sql
docker compose exec -w /opt/fcqa db psql -P pager=off -v ON_ERROR_STOP=1 -U postgres -d fcqa -f db/verify_basic_queries.sql
```

如果不使用 Docker，也可在本机 PostgreSQL 上执行：

```bash
createdb fcqa
psql -P pager=off -v ON_ERROR_STOP=1 -d fcqa -f db/init.sql
psql -P pager=off -v ON_ERROR_STOP=1 -d fcqa -f db/verify_basic_queries.sql
```

验收通过时，通常可以直接观察到以下结果：

1. 初始化和查询脚本执行过程中没有出现 `ERROR`。
2. `db/verify_basic_queries.sql` 能正常输出多组查询结果与统计结果。
3. 事务写入测试会插入一条临时用户记录，随后通过 `ROLLBACK` 恢复，不污染演示数据。
4. 如需核对更详细的导入规模与展示步骤，可直接查看 [docs/数据库导入查询展示说明.md](docs/数据库导入查询展示说明.md) 和 [docs/数据库CSV导入验收记录.md](docs/数据库CSV导入验收记录.md)。

## 验收时可重点查看

- 从空库初始化： [db/init.sql](db/init.sql)
- CSV 演示数据初始化： [db/init_csv.sql](db/init_csv.sql)
- 基础验收查询： [db/verify_basic_queries.sql](db/verify_basic_queries.sql)
- 导入与查询展示说明： [docs/数据库导入查询展示说明.md](docs/数据库导入查询展示说明.md)
- CSV 导入验收记录： [docs/数据库CSV导入验收记录.md](docs/数据库CSV导入验收记录.md)
- 完整表结构定稿： [docs/完整表结构说明（定稿）.md](docs/完整表结构说明（定稿）.md)
- 主要约束设计说明： [docs/主要约束设计说明.md](docs/主要约束设计说明.md)

## 第四阶段交付物

第四阶段已完成数据库物理实现，当前脚本可从空库创建表结构、导入测试数据，并支撑基础存储、查询与后续功能联调。

| 类别               | 入口文件                                                         |
| :----------------- | :--------------------------------------------------------------- |
| 建表与索引入口     | [db/schema.sql](db/schema.sql)                                   |
| 一键初始化入口     | [db/init.sql](db/init.sql)                                       |
| CSV 统一初始化入口 | [db/init_csv.sql](db/init_csv.sql)                               |
| CSV 导入脚本       | [db/seeds/import_csv.sql](db/seeds/import_csv.sql)               |
| 建表与迁移脚本     | [migrations](migrations)                                         |
| 核心 SQL 快照      | [db/schema_core.sql](db/schema_core.sql)                         |
| 初始 SQL 测试数据  | [db/seeds/001_initial_data.sql](db/seeds/001_initial_data.sql)   |
| CSV 演示数据说明   | [db/seeds/README.md](db/seeds/README.md)                         |
| CSV 演示数据目录   | [db/seeds/csv](db/seeds/csv)                                     |
| 基础验收查询       | [db/verify_basic_queries.sql](db/verify_basic_queries.sql)       |
| 导入、查询展示说明 | [docs/数据库导入查询展示说明.md](docs/数据库导入查询展示说明.md) |
| CSV 导入验收记录   | [docs/数据库CSV导入验收记录.md](docs/数据库CSV导入验收记录.md)   |

## 各阶段成果导航

### 第一阶段

- 完成内容：选题确定、需求分析与概念设计，形成初步实体关系结构。
- 主要材料：
  - [docs/需求分析说明书.md](docs/需求分析说明书.md)
  - [docs/attachments](docs/attachments)
  - [design/ER.drawio](design/ER.drawio)
  - [design/ER.png](design/ER.png)

### 第二阶段

- 完成内容：关系模式设计与规范化分析，明确实体表、关系表、关键字段及第三范式分析。
- 主要材料：
  - [docs/关系模式初稿及说明.md](docs/关系模式初稿及说明.md)
  - [docs/规范性分析.md](docs/规范性分析.md)
  - [design/ER.drawio](design/ER.drawio)
  - [design/ER.png](design/ER.png)

### 第三阶段

- 完成内容：数据库逻辑结构定稿，明确完整表结构、主要约束设计与核心 SQL 草稿。
- 主要材料：
  - [docs/完整表结构说明（定稿）.md](docs/完整表结构说明（定稿）.md)
  - [docs/主要约束设计说明.md](docs/主要约束设计说明.md)
  - [db/schema_core.sql](db/schema_core.sql)
  - [migrations](migrations)

### 第四阶段

- 完成内容：完成数据库实现，提交建表 SQL、主要约束实现⽅案、必要的索引设计及初始测试数据。数据库可以正确创建并导入数据，能够⽀持基本的数据存储、查询与后续功能联调。
- 主要材料：见上方“第四阶段交付物”和“验收时可重点查看”。

## 仓库目录说明

- [backend](backend)：后端预留目录。
- [frontend](frontend)：前端预留目录。
- [db](db)：数据库脚本、初始化入口、验收查询、种子数据与说明。
- [migrations](migrations)：按阶段拆分的迁移脚本。
- [docs](docs)：需求、关系模式、规范性分析、定稿表结构、约束说明和验收文档。
- [design](design)：ER 图源文件与导出文件。
- [data](data)：数据目录预留。

