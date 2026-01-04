# 项目目录结构

## DDD 四层架构

```
neo4j-graph/                          # 项目根目录
│
├── 📁 DDD 核心代码层
│   │
│   ├── domain/                       # 【领域层】核心业务逻辑
│   │   ├── model/                    # 领域模型（实体、值对象）
│   │   ├── repository/               # 仓储接口定义
│   │   └── service/                  # 领域服务
│   │       ├── vector_recall.py      # ⭐ 向量召回系统（674行）
│   │       └── vector_indexer.py     # ⭐ 向量索引管理（398行）
│   │
│   ├── application/                  # 【应用层】用例编排
│   │   ├── port/                     # 端口适配器接口
│   │   └── service/                  # 应用服务
│   │       └── flight_csv_importer.py  # ⭐ 航班CSV导入器（356行）
│   │
│   ├── infrastructure/               # 【基础设施层】技术实现
│   │   ├── config/                   # 配置管理
│   │   │   ├── config.py             # ⭐ 配置管理（94行）
│   │   │   └── schemas/              # Schema定义目录
│   │   ├── persistence/              # 持久化
│   │   │   └── neo4j/
│   │   │       └── neo4j_client.py   # ⭐ Neo4j客户端（249行）
│   │   └── service/                  # 基础设施服务
│   │       └── embedding/
│   │           ├── embedding_service.py        # ⭐ OpenRouter嵌入服务（234行）
│   │           └── mock_embedding_service.py   # Mock服务（测试用）
│   │
│   └── interface/                    # 【接口层】用户交互
│       ├── api/
│       │   └── main.py               # ⭐ FastAPI HTTP接口（423行）
│       └── cli/
│           └── main.py               # ⭐ CLI命令行接口（239行）
│
├── 📁 测试代码
│   └── tests/                        # 测试目录
│       ├── unit/                     # 单元测试
│       │   ├── domain/               # 领域层测试
│       │   ├── application/          # 应用层测试
│       │   ├── infrastructure/       # 基础设施层测试
│       │   └── interface/            # 接口层测试
│       ├── integration/              # 集成测试
│       │   ├── test_filtered_recall.py
│       │   ├── test_index_create.py
│       │   ├── test_openrouter.py
│       │   ├── test_openrouter_embedding.py
│       │   ├── test_qwen_embedding.py
│       │   ├── check_ontology_nodes.py
│       │   ├── analyze_ontology_attributes.py
│       │   ├── generate_ontology_embeddings.py
│       │   ├── generate_ontology_class_embeddings.py
│       │   └── drop_ontology_index.py
│       └── e2e/                      # 端到端测试
│
├── 📁 数据文件
│   └── data/
│       ├── Flight/                   # 航班场景数据
│       │   ├── nodes_ontology_json.csv
│       │   ├── nodes_entities_json.csv
│       │   ├── rels_ontology_json.csv
│       │   └── rels_entities_json.csv
│       ├── Flight0.41/               # 航班v0.41数据（旧版本）
│       ├── flight_schema_v0.4.json   # 航班Schema定义（29KB）
│       └── prd_scenarios.json        # PRD场景数据（57KB）
│
├── 📁 文档
│   └── docs/
│       ├── README_flight_schema.md   # 航班场景数据模型文档
│       └── 航班场景v0.4.pdf         # 需求文档（1.2MB）
│
├── 📁 脚本工具
│   └── scripts/
│       ├── quickstart.sh             # 🚀 快速启动脚本
│       └── start_api.sh              # 🚀 API服务启动脚本
│
├── 📄 配置文件
│   ├── .env                          # 环境变量（包含敏感信息，不提交）
│   ├── .gitignore                    # Git忽略规则
│   └── requirements.txt              # Python依赖（11个核心包）
│
├── 📄 文档文件
│   ├── README.md                     # 项目说明（13KB）
│   ├── CLAUDE.md                     # 🌟 架构文档（19KB）
│   ├── QUICKSTART.md                 # 🚀 快速启动指南
│   ├── REFACTOR_SUMMARY.md           # 重构总结报告
│   └── PROJECT_STRUCTURE.md          # 项目结构说明（本文件）
│
├── 📄 启动脚本
│   └── start.sh                      # 🚀 便捷启动脚本
│
└── 📁 其他
    ├── .idea/                        # PyCharm IDE配置
    ├── .claude/                      # Claude Code配置
    └── .venv/                        # Python虚拟环境
```

## 文件统计

### 代码文件
- **核心代码**: 14个Python文件，约5,977行
- **测试代码**: 10个测试文件，约778行
- **总代码量**: 约6,755行Python代码

### 文档文件
- README.md（13KB）
- CLAUDE.md（19KB）
- QUICKSTART.md（新增）
- REFACTOR_SUMMARY.md（新增）
- PROJECT_STRUCTURE.md（新增）
- docs/README_flight_schema.md
- docs/航班场景v0.4.pdf（1.2MB）

### 配置文件
- .env（环境变量）
- .gitignore（Git忽略规则）
- requirements.txt（11个依赖包）

### 脚本文件
- scripts/quickstart.sh（快速启动）
- scripts/start_api.sh（API启动）
- start.sh（便捷启动）

## DDD 层级依赖关系

```
┌─────────────────────────────────────────┐
│           Interface Layer               │  用户交互
│     (FastAPI + CLI)                     │  ↓ 调用
├─────────────────────────────────────────┤
│         Application Layer               │  用例编排
│     (FlightCSVImporter)                 │  ↓ 调用
├─────────────────────────────────────────┤
│           Domain Layer                  │  核心业务
│  (VectorRecallSystem, VectorIndexer)    │  ↓ 使用
├─────────────────────────────────────────┤
│       Infrastructure Layer              │  技术支撑
│  (Neo4jClient, EmbeddingService)        │
└─────────────────────────────────────────┘
```

### 依赖规则
- ✅ **允许**: 上层依赖下层
- ❌ **禁止**: 下层依赖上层
- ✅ **推荐**: Domain层不依赖Infrastructure层（通过接口反转）

## 核心组件说明

### ⭐ 核心服务（Domain Layer）

1. **vector_recall.py** (674行)
   - VectorRecallSystem: 向量召回引擎
   - RecallResultFormatter: 结果格式化器
   - 支持4种召回场景

2. **vector_indexer.py** (398行)
   - VectorIndexer: 索引管理器
   - 支持节点和关系索引
   - 批量索引创建

### ⭐ 应用服务（Application Layer）

3. **flight_csv_importer.py** (356行)
   - FlightCSVImporter: CSV数据导入器
   - 支持本体层和实体层
   - MERGE策略增量更新

### ⭐ 基础设施（Infrastructure Layer）

4. **neo4j_client.py** (249行)
   - Neo4jClient: 图数据库客户端
   - 连接池管理
   - 读写事务分离

5. **embedding_service.py** (234行)
   - EmbeddingService: 向量生成服务
   - Qwen3-Embedding-8B模型
   - 4096维向量

### ⭐ 接口层（Interface Layer）

6. **api/main.py** (423行)
   - FastAPI HTTP接口
   - 11个API端点
   - Swagger文档

7. **cli/main.py** (239行)
   - CLI命令行工具
   - Rich美化输出
   - 交互式命令

## 测试目录说明

```
tests/
├── unit/              # 单元测试（针对单个类/函数）
│   ├── domain/        # 领域层单元测试
│   ├── application/   # 应用层单元测试
│   ├── infrastructure/# 基础设施层单元测试
│   └── interface/     # 接口层单元测试
│
├── integration/       # 集成测试（测试组件集成）
│   ├── test_*.py      # 各种集成测试
│   └── *.py           # 工具脚本
│
└── e2e/              # 端到端测试（完整业务流程）
```

## 快速导航

- 🚀 **启动项目**: [QUICKSTART.md](QUICKSTART.md)
- 📚 **架构文档**: [CLAUDE.md](CLAUDE.md)
- 📖 **项目说明**: [README.md](README.md)
- 🔄 **重构总结**: [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)
- 🏗️ **目录结构**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)（本文件）

---

**最后更新**: 2026-01-03
**项目版本**: v1.0.0
