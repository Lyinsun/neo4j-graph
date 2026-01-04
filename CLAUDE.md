# Neo4j Graph - 向量召回智能知识检索系统

## 📋 项目概述

本项目是基于 **Neo4j 图数据库** 和 **向量召回技术** 的智能知识检索系统，采用 **领域驱动设计 (DDD)** 架构模式构建。

### 核心特性

- 🎯 **多场景支持**: PRD审核场景 + 航班运行场景
- 🔍 **智能召回**: 基于向量相似度的语义检索
- 🏗️ **DDD架构**: 清晰的分层设计，高内聚低耦合
- 🚀 **双接口**: CLI命令行 + FastAPI HTTP服务
- 📊 **向量索引**: 4096维 Qwen3 Embedding模型
- 🔧 **灵活扩展**: 支持多种节点类型的知识库检索

### 技术栈

- **后端框架**: FastAPI (Python 3.9+)
- **图数据库**: Neo4j 5.14+
- **向量模型**: Qwen3-Embedding-8B (OpenRouter API)
- **依赖管理**: pip + requirements.txt
- **开发工具**: Rich (CLI美化), Pydantic (数据验证)

---

## 🏛️ DDD 架构设计

本项目严格遵循 DDD 四层架构模式：

```
neo4j-graph/
├── domain/                    # 领域层 - 核心业务逻辑
│   ├── model/                 # 领域模型（实体、值对象）
│   └── service/               # 领域服务
│       ├── vector_recall.py   # 向量召回系统（674行）
│       └── vector_indexer.py  # 向量索引管理（398行）
│
├── application/               # 应用层 - 用例编排
│   └── service/
│       └── flight_csv_importer.py  # 航班数据导入器（356行）
│
├── infrastructure/            # 基础设施层 - 技术实现
│   ├── config/
│   │   ├── config.py          # 配置管理
│   │   └── schemas/           # 数据Schema定义
│   ├── persistence/
│   │   └── neo4j/
│   │       └── neo4j_client.py  # Neo4j数据库客户端（249行）
│   └── service/
│       └── embedding/
│           ├── embedding_service.py        # OpenRouter嵌入服务（234行）
│           └── mock_embedding_service.py   # Mock服务（测试用）
│
└── interface/                 # 接口层 - 用户交互
    ├── api/
    │   └── main.py            # FastAPI HTTP接口（423行）
    └── cli/
        └── main.py            # 命令行接口（239行）
```

### 层级职责

#### 1. Domain Layer (领域层)
- **职责**: 封装核心业务逻辑和规则
- **特点**: 不依赖外部框架，纯业务逻辑
- **核心类**:
  - `VectorRecallSystem`: 向量召回引擎
  - `VectorIndexer`: 索引管理器
  - `RecallResultFormatter`: 结果格式化器

#### 2. Application Layer (应用层)
- **职责**: 协调领域对象完成业务用例
- **特点**: 编排领域服务，处理事务边界
- **核心类**:
  - `FlightCSVImporter`: 航班数据导入流程

#### 3. Infrastructure Layer (基础设施层)
- **职责**: 提供技术能力支持（数据库、API、缓存等）
- **特点**: 可替换的技术实现
- **核心组件**:
  - `Neo4jClient`: 图数据库访问
  - `EmbeddingService`: 向量生成服务
  - `Config`: 配置管理

#### 4. Interface Layer (接口层)
- **职责**: 暴露系统能力给外部用户
- **特点**: 适配不同的交互方式
- **核心接口**:
  - FastAPI HTTP API (生产环境)
  - CLI命令行工具 (开发/运维)

---

## 📁 项目目录结构

```
neo4j-graph/
├── 📦 核心代码 (DDD分层)
│   ├── domain/                          # 领域层
│   │   ├── model/                       # 领域模型
│   │   └── service/                     # 领域服务
│   │       ├── vector_recall.py         # 向量召回系统
│   │       └── vector_indexer.py        # 向量索引管理
│   │
│   ├── application/                     # 应用层
│   │   └── service/
│   │       └── flight_csv_importer.py   # 航班CSV导入器
│   │
│   ├── infrastructure/                  # 基础设施层
│   │   ├── config/
│   │   │   ├── config.py                # 配置管理
│   │   │   └── schemas/                 # Schema定义
│   │   ├── persistence/
│   │   │   └── neo4j/
│   │   │       └── neo4j_client.py      # Neo4j客户端
│   │   └── service/
│   │       └── embedding/
│   │           ├── embedding_service.py         # 嵌入服务
│   │           └── mock_embedding_service.py    # Mock服务
│   │
│   └── interface/                       # 接口层
│       ├── api/
│       │   └── main.py                  # FastAPI接口
│       └── cli/
│           └── main.py                  # CLI接口
│
├── 🧪 测试代码
│   └── tests/
│       ├── unit/                        # 单元测试
│       │   ├── domain/
│       │   ├── application/
│       │   ├── infrastructure/
│       │   └── interface/
│       ├── integration/                 # 集成测试
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
│       └── e2e/                         # 端到端测试
│
├── 📊 数据文件
│   └── data/
│       ├── Flight/                      # 航班场景数据
│       │   ├── nodes_ontology_json.csv
│       │   ├── nodes_entities_json.csv
│       │   ├── rels_ontology_json.csv
│       │   └── rels_entities_json.csv
│       ├── flight_schema_v0.4.json      # 航班Schema定义
│       └── prd_scenarios.json           # PRD场景数据
│
├── 📚 文档
│   ├── docs/
│   │   ├── README_flight_schema.md      # 航班场景文档
│   │   └── 航班场景v0.4.pdf            # 需求文档
│   ├── README.md                        # 项目说明
│   └── CLAUDE.md                        # 架构文档（本文件）
│
├── 🔧 脚本工具
│   └── scripts/
│       ├── quickstart.sh                # 快速启动
│       └── start_api.sh                 # API服务启动
│
├── ⚙️ 配置文件
│   ├── .env                             # 环境变量
│   ├── .gitignore                       # Git忽略规则
│   ├── requirements.txt                 # Python依赖
│   └── .idea/                           # IDE配置
│
└── 🐍 虚拟环境
    └── .venv/                           # Python虚拟环境
```

---

## 🔌 FastAPI 接口文档

### 服务启动

```bash
# 方式1: 使用脚本（推荐）
./scripts/start_api.sh

# 方式2: 直接运行
python -m interface.api.main

# 方式3: uvicorn命令
uvicorn interface.api.main:app --host 0.0.0.0 --port 8010 --reload
```

### API 路由

#### 系统路由 (System)

```http
GET /health
```
健康检查接口

---

#### 召回路由 (Recall)

```http
POST /recall/knowledge-base
Content-Type: application/json

{
  "query": "航班延误处理",
  "node_label": "Ontology",
  "top_k": 5,
  "filters": {
    "version": "Flightv0_4"
  }
}
```
通用知识库搜索，支持多种节点类型和过滤条件

---

```http
POST /recall/similar-prds
Content-Type: application/json

{
  "query": "用户登录功能需求",
  "top_k": 3
}
```
查找相似的PRD文档

---

```http
POST /recall/review-suggestions
Content-Type: application/json

{
  "prd_id": "PRD-001",
  "department": "技术部"
}
```
获取智能评审建议

---

```http
POST /recall/risk-identification
Content-Type: application/json

{
  "prd_id": "PRD-001"
}
```
识别潜在风险

---

```http
POST /recall/hybrid
Content-Type: application/json

{
  "query": "机场协同决策",
  "node_label": "Ontology",
  "top_k": 10,
  "filters": {
    "entity_type": "Process"
  }
}
```
混合搜索（向量相似度 + 结构化过滤）

---

#### 嵌入路由 (Embedding)

```http
POST /embedding/generate
Content-Type: application/json

{
  "text": "这是需要生成向量的文本"
}
```
生成单个文本的向量嵌入

---

```http
POST /embedding/batch
Content-Type: application/json

{
  "texts": [
    "文本1",
    "文本2",
    "文本3"
  ]
}
```
批量生成向量嵌入

---

#### 向量索引管理 (Vector Index)

```http
POST /index/create
Content-Type: application/json

{
  "index_name": "ontology_name_vector",
  "node_label": "Ontology",
  "property_name": "embedding",
  "dimensions": 4096,
  "similarity_function": "cosine"
}
```
创建向量索引

---

```http
POST /index/create-all
```
创建所有预定义索引

---

```http
DELETE /index/{index_name}
```
删除指定索引

---

```http
GET /index/list
```
列出所有索引

### API 文档访问

- **Swagger UI**: http://localhost:8010/docs
- **ReDoc**: http://localhost:8010/redoc

---

## 🖥️ CLI 命令行接口

### 测试数据插入

```bash
python -m interface.cli.main test-insert
```

### 导入航班数据

```bash
python -m interface.cli.main import-flight --data-dir data/Flight
```

### 创建向量索引

```bash
python -m interface.cli.main create-index \
  --index-name ontology_name_vector \
  --node-label Ontology \
  --property-name embedding \
  --dimensions 4096
```

### 执行向量召回

```bash
python -m interface.cli.main recall \
  --query "航班延误处理" \
  --node-label Ontology \
  --top-k 5 \
  --scenario knowledge_base \
  --filter version=Flightv0_4
```

---

## 📊 数据模型

### PRD审核场景

#### 节点类型

- **PRD** - 产品需求文档
  - 属性: `prd_id`, `title`, `description`, `description_embedding` (向量)

- **ReviewComment** - 评审意见
  - 属性: `comment_id`, `content`, `content_embedding` (向量), `department`

- **RiskAssessment** - 风险评估
  - 属性: `risk_id`, `impact`, `impact_embedding` (向量), `severity`

- **Department** - 部门
  - 属性: `dept_id`, `name`

- **DecisionRecommendation** - 决策建议
  - 属性: `recommendation_id`, `content`

#### 关系类型

```cypher
(PRD)-[:HAS_REVIEW]->(ReviewComment)
(Department)-[:PROVIDES_REVIEW]->(ReviewComment)
(PRD)-[:HAS_RISK]->(RiskAssessment)
(PRD)-[:HAS_RECOMMENDATION]->(DecisionRecommendation)
(ReviewComment)-[:IDENTIFIES_RISK]->(RiskAssessment)
```

#### 向量索引

- `prd_description_vector` - PRD描述索引 (4096维)
- `review_content_vector` - 评审内容索引 (4096维)
- `risk_impact_vector` - 风险影响索引 (4096维)

---

### 航班场景

#### 数据层次

- **本体层 (Ontology)**: 定义概念和关系类型
- **实体层 (Entity)**: 具体的航班、机场、航线实例

#### 数据文件

- `nodes_ontology_json.csv` - 本体节点
- `rels_ontology_json.csv` - 本体关系
- `nodes_entities_json.csv` - 实体节点
- `rels_entities_json.csv` - 实体关系

#### 向量索引

- `ontology_name_vector` - 本体名称向量索引 (4096维)

参考文档: `docs/README_flight_schema.md`

---

## 🔧 核心组件详解

### 1. VectorRecallSystem (向量召回系统)

**文件**: `domain/service/vector_recall.py`

**核心方法**:

```python
class VectorRecallSystem:
    def find_similar_prds(self, query: str, top_k: int = 5) -> List[Dict]
        """场景1: 查找相似PRD"""

    def get_intelligent_review_suggestions(self, prd_id: str, department: str) -> Dict
        """场景2: 获取智能评审建议"""

    def identify_potential_risks(self, prd_id: str, top_k: int = 5) -> Dict
        """场景3: 识别潜在风险"""

    def search_knowledge_base(self, query: str, node_label: str, **kwargs) -> List[Dict]
        """场景4: 通用知识库检索"""

    def hybrid_search(self, query: str, node_label: str, filters: Dict, **kwargs) -> List[Dict]
        """混合搜索: 向量相似度 + 结构化过滤"""
```

**支持的节点类型**:
- `Ontology` - 本体知识
- `PRD` - 产品需求
- `ReviewComment` - 评审意见
- `RiskAssessment` - 风险评估

---

### 2. VectorIndexer (向量索引管理器)

**文件**: `domain/service/vector_indexer.py`

**核心功能**:

```python
class VectorIndexer:
    def create_node_vector_index(self, index_name: str, node_label: str, ...)
        """创建节点向量索引"""

    def create_relationship_vector_index(self, index_name: str, rel_type: str, ...)
        """创建关系向量索引"""

    def create_all_indexes(self, config: List[Dict]) -> Dict
        """批量创建索引"""

    def import_and_create_index(self, index_name: str, node_label: str, ...)
        """导入数据并生成嵌入向量"""

    def delete_index(self, index_name: str) -> bool
        """删除索引"""

    def list_indexes(self) -> List[Dict]
        """列出所有索引"""
```

---

### 3. Neo4jClient (Neo4j数据库客户端)

**文件**: `infrastructure/persistence/neo4j/neo4j_client.py`

**特性**:

- ✅ 连接池管理
- ✅ 上下文管理器支持
- ✅ 读/写事务分离
- ✅ 向量索引支持检测
- ✅ 约束管理

**使用示例**:

```python
# 使用上下文管理器
with Neo4jClient() as client:
    result = client.execute_read("MATCH (n) RETURN n LIMIT 10")

# 写事务
with Neo4jClient() as client:
    client.execute_write(
        "CREATE (p:PRD {prd_id: $id, title: $title})",
        id="PRD-001",
        title="用户登录功能"
    )
```

---

### 4. EmbeddingService (向量嵌入服务)

**文件**: `infrastructure/service/embedding/embedding_service.py`

**配置**:
- **模型**: `qwen/qwen3-embedding-8b`
- **维度**: 4096
- **API**: OpenRouter

**特性**:

- 🔄 自动批处理（防止API限流）
- 🔁 失败重试（指数退避）
- 💾 嵌入缓存（提升性能）
- 📊 进度显示（Rich库）

**使用示例**:

```python
from infrastructure.service.embedding.embedding_service import EmbeddingService

service = EmbeddingService()

# 单文本嵌入
embedding = service.generate_embedding("航班延误处理流程")

# 批量嵌入
texts = ["文本1", "文本2", "文本3"]
embeddings = service.generate_batch_embeddings(texts)
```

---

### 5. FlightCSVImporter (航班数据导入器)

**文件**: `application/service/flight_csv_importer.py`

**功能**:

```python
class FlightCSVImporter:
    def import_ontology_nodes(self, csv_file: str)
        """导入本体层节点"""

    def import_ontology_relationships(self, csv_file: str)
        """导入本体层关系"""

    def import_entity_nodes(self, csv_file: str)
        """导入实体层节点"""

    def import_entity_relationships(self, csv_file: str)
        """导入实体层关系"""

    def import_all(self, data_dir: str) -> Dict
        """导入所有数据"""
```

**特性**:
- CSV中的JSON属性自动解析
- MERGE策略支持增量更新
- 详细的导入统计和错误报告

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件:

```bash
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-your-api-key

# Neo4j环境选择
NEO4J_ENV=local  # local 或 production

# 本地环境
NEO4J_LOCAL_URI=neo4j://127.0.0.1:7687
NEO4J_LOCAL_USER=neo4j
NEO4J_LOCAL_PASSWORD=your-password
NEO4J_LOCAL_DATABASE=deepworld

# 生产环境
NEO4J_PROD_URI=bolt://your-prod-host:7687
NEO4J_PROD_USER=neo4j
NEO4J_PROD_PASSWORD=your-prod-password
```

### 3. 启动Neo4j数据库

确保Neo4j数据库已启动并可访问。

### 4. 导入数据

```bash
# 导入航班数据
python -m interface.cli.main import-flight --data-dir data/Flight

# 创建向量索引
python -m interface.cli.main create-index \
  --index-name ontology_name_vector \
  --node-label Ontology \
  --property-name embedding
```

### 5. 启动API服务

```bash
./scripts/start_api.sh
```

访问 http://localhost:8000/docs 查看API文档。

---

## 🧪 测试

### 运行集成测试

```bash
# 测试向量召回
python tests/integration/test_filtered_recall.py

# 测试索引创建
python tests/integration/test_index_create.py

# 测试嵌入服务
python tests/integration/test_qwen_embedding.py
```

### 测试目录结构

```
tests/
├── unit/              # 单元测试（针对单个类/函数）
├── integration/       # 集成测试（测试组件集成）
└── e2e/              # 端到端测试（完整业务流程）
```

---

## 📦 依赖说明

### 核心依赖

```txt
neo4j>=5.14.0              # Neo4j Python驱动
openai>=1.0.0              # OpenAI SDK (兼容OpenRouter)
python-dotenv>=1.0.0       # 环境变量管理
numpy>=1.24.0              # 数值计算
rich>=13.0.0               # CLI美化
fastapi>=0.104.0           # Web框架
uvicorn>=0.24.0            # ASGI服务器
pydantic>=2.0.0            # 数据验证
```

---

## 🔐 安全注意事项

1. **不要提交 `.env` 文件到版本控制**
   - 已添加到 `.gitignore`

2. **使用环境变量管理敏感信息**
   - API密钥
   - 数据库密码

3. **生产环境建议**
   - 使用密钥管理服务（AWS Secrets Manager, HashiCorp Vault等）
   - 为API添加认证机制（JWT, OAuth2等）
   - 启用HTTPS/TLS加密

---

## 🎯 未来规划

### 短期目标

- [ ] 补充完整的单元测试覆盖
- [ ] 添加API认证和授权
- [ ] 实现嵌入缓存持久化（Redis）
- [ ] 优化批量导入性能

### 长期目标

- [ ] 支持更多向量模型（BGE, M3E等）
- [ ] 添加图可视化界面
- [ ] 实现实时更新和增量索引
- [ ] 多语言支持
- [ ] 分布式部署支持

---

## 📖 参考文档

- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenRouter API](https://openrouter.ai/docs)
- [领域驱动设计 (DDD)](https://domain-driven-design.org/)

---

## 👥 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

---

## 📄 License

本项目采用 MIT 许可证。

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至项目维护者

---

**最后更新**: 2026-01-03
**版本**: v1.0.0
