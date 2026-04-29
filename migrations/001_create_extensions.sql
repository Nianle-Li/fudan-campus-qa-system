-- 001_create_extensions.sql
-- 启用项目所需的 PostgreSQL 扩展
-- 在 fcqa 数据库上以有权限的用户执行

-- pg_trgm: 用于相似度/模糊匹配索引
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- unaccent: 可选，用于去除 Unicode 重音符，改善文本搜索
CREATE EXTENSION IF NOT EXISTS unaccent;

-- pgvector: 向量检索扩展（仅当服务器已安装二进制时启用）
-- 如果在本机报错：请参考项目文档使用带 pgvector 的 Docker 镜像或在服务器上安装扩展
-- CREATE EXTENSION IF NOT EXISTS vector;
