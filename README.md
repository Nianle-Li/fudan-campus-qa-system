# fudan-campus-qa-system

复旦校园百事通问答系统 - 数据库设计课程项目

## 小组成员

李佳凝（Nianle-Li），刘嘉文（posaka），卢浩达（Haoda Lu）

## 第一阶段完成情况

- 完成任务：选题确定、需求分析与概念设计，形成初步实体—关系结构。
- 选题：复旦校园百事通问答系统
- 提交材料：
  - 需求分析（markdown）：docs/需求分析说明书.md
  - 需求分析（PDF）：docs/需求分析说明书.pdf
  - 需求分析附件（流程图）：docs/attachments
  - ER 图初稿与设计说明（PDF）：design/ER.pdf

## 第二阶段完成情况

- 完成任务：完成关系模式设计以及规范化分析。说明各表的设计依据，明确主要实体表、关系表及关键字段设置，并结合第三范式分析设计中的数据冗余、更新异常和查询支持情况。
- 提交材料：
  - 关系模式设计与说明： [docs/关系模式初稿及说明.md](docs/关系模式初稿及说明.md)
  - 规范性分析： [docs/规范性分析.md](docs/规范性分析.md)
  - 更新的 ER 图（源文件）： [design/ER.drawio](design/ER.drawio)
  - 更新的 ER 图（导出图片）： [design/ER.png](design/ER.png)

## 第三阶段完成情况

- 完成任务：完成数据库逻辑结构定稿，提交完整表结构说明、主要约束设计说明及核心 SQL 草稿。体现业务规则在数据库层的实现方式，包括主键、外键、非空、唯一、检查约束或默认值等，并保证数据库设计已经能够支撑后续系统开发。
- 选取数据库：PostgreSQL（设计与迁移脚本基于 Postgres 特性：`SERIAL`、`tsvector`、GIN 索引、生成列等；建议部署 PostgreSQL 16）。
- 提交材料：
  - 完整表结构说明： [docs/完整表结构说明（定稿）.md](docs/完整表结构说明（定稿）.md)
  - 主要约束设计说明： [docs/主要约束设计说明.md](docs/主要约束设计说明.md)
  - 核心 SQL 草稿（单文件快照）： [db/schema_core.sql](db/schema_core.sql)
  - 迁移脚本（按序）： migrations文件夹

## 第四阶段完成情况

- 完成任务：已完成数据库物理实现，提交了可执行建表 SQL、主要约束实现、必要索引设计、初始测试数据和基础验收查询。当前脚本可从空库创建表结构、导入测试数据，并支撑基础存储、查询与后续功能联调。
- 提交材料：
  - 建表与索引入口： [db/schema.sql](db/schema.sql)
  - 一键初始化入口： [db/init.sql](db/init.sql)
  - 建表与迁移脚本（按序）： [migrations](migrations)
  - 核心 SQL 快照： [db/schema_core.sql](db/schema_core.sql)
  - 主要约束设计说明： [docs/主要约束设计说明.md](docs/主要约束设计说明.md)
  - 初始 SQL 测试数据： [db/seeds/001_initial_data.sql](db/seeds/001_initial_data.sql)
  - 初始/演示数据说明： [db/seeds/README.md](db/seeds/README.md)
  - 初始/演示 CSV 数据： [db/seeds/csv](db/seeds/csv)
  - 基础验收查询： [db/verify_basic_queries.sql](db/verify_basic_queries.sql)
  - 导入查询展示说明： [docs/数据库导入查询展示说明.md](docs/数据库导入查询展示说明.md)
- 快速初始化：

```bash
docker compose up -d db
docker compose exec db psql -v ON_ERROR_STOP=1 -U postgres -d fcqa -f /opt/fcqa/db/verify_basic_queries.sql
```

或使用本机 PostgreSQL：

```bash
createdb fcqa
psql -v ON_ERROR_STOP=1 -d fcqa -f db/init.sql
psql -v ON_ERROR_STOP=1 -d fcqa -f db/verify_basic_queries.sql
```
