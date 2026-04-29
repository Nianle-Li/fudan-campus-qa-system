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


