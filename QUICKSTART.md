# 快速启动指南

## 🚀 三种启动方式

### 方式1：快速启动（推荐新用户）
```bash
./scripts/quickstart.sh
```
这将自动完成：
- 安装依赖
- 验证配置
- 运行测试插入

### 方式2：启动API服务
```bash
# 从项目根目录
./start.sh

# 或者
./scripts/start_api.sh
```
API服务将在以下地址可用：
- 服务地址: http://localhost:8000
- API文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 方式3：使用CLI命令
```bash
# 导入航班数据
python -m interface.cli.main import-flight --data-dir data/Flight

# 创建向量索引
python -m interface.cli.main create-index \
  --index-name ontology_name_vector \
  --node-label Ontology \
  --property-name embedding

# 执行向量召回
python -m interface.cli.main recall \
  --query "航班延误处理" \
  --node-label Ontology \
  --top-k 5
```

## 📋 前置要求

1. **Python 3.9+**
2. **Neo4j 5.14+** 数据库运行中
3. **配置 .env 文件**（包含必要的API密钥和数据库连接信息）

## 🔧 脚本说明

### scripts/quickstart.sh
完整的快速启动流程，适合首次使用

### scripts/start_api.sh
启动FastAPI服务器，适合日常开发

### start.sh
便捷启动脚本（调用 scripts/start_api.sh）

## 📚 更多信息

- 完整架构文档: [CLAUDE.md](CLAUDE.md)
- 项目说明: [README.md](README.md)
- 重构总结: [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)
