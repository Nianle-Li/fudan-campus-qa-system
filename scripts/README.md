# Scripts

辅助脚本用于最终交付前的本地自测。

## 冒烟测试

启动内置演示数据并完整跑一轮前后端 API：

```bash
python scripts/smoke_test.py --start-demo
```

测试已有后端服务：

```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

脚本会验证：

- 后端健康检查
- 前端首页可访问
- 校区、建筑、课程查询
- 建筑、设施、活动新增/修改/删除
- 自然语言查询
- 查询记录写入
- 关键 SQL 示例返回
