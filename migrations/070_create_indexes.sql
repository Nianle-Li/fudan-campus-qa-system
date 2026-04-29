-- 070_create_indexes.sql
-- 建议在表创建完并导入种子数据后执行索引建立，部分索引可并行创建
BEGIN;

-- 为 Activity 添加 tsvector 列并建 GIN 索引（适用于英文/简单分词）
ALTER TABLE activity
  ADD COLUMN IF NOT EXISTS description_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(description,''))
  ) STORED;
CREATE INDEX IF NOT EXISTS idx_activity_description_tsv ON activity USING GIN (description_tsv);

-- 为 users/course/facility/query_log 添加 tsvector 列与 GIN 索引，提升全文查询
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS name_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(name,''))
  ) STORED;
CREATE INDEX IF NOT EXISTS idx_users_name_tsv ON users USING GIN (name_tsv);

ALTER TABLE course
  ADD COLUMN IF NOT EXISTS name_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(name,''))
  ) STORED;
CREATE INDEX IF NOT EXISTS idx_course_name_tsv ON course USING GIN (name_tsv);

ALTER TABLE facility
  ADD COLUMN IF NOT EXISTS name_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(name,''))
  ) STORED;
CREATE INDEX IF NOT EXISTS idx_facility_name_tsv ON facility USING GIN (name_tsv);

ALTER TABLE query_log
  ADD COLUMN IF NOT EXISTS content_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(query_content,''))
  ) STORED;
CREATE INDEX IF NOT EXISTS idx_querylog_content_tsv ON query_log USING GIN (content_tsv);

-- trigram 索引用于模糊/相似搜索
CREATE INDEX IF NOT EXISTS idx_user_name_trgm ON users USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_activity_name_trgm ON activity USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_querylog_content_trgm ON query_log USING gin (query_content gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_course_name_trgm ON course USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_facility_name_trgm ON facility USING gin (name gin_trgm_ops);

-- 外键常用查询索引
CREATE INDEX IF NOT EXISTS idx_facility_building ON facility (building_id);
CREATE INDEX IF NOT EXISTS idx_building_campus ON building (campus_id);
CREATE INDEX IF NOT EXISTS idx_course_master ON course (course_master_code);

COMMIT;
