# PRD Review Vector Recall System

基于Neo4j向量索引和OpenRouter API的PRD审核场景智能召回系统。

## 系统架构

```
PRD审核向量召回系统
├── 数据层: Neo4j 5.23.0 图数据库
├── 向量化: OpenRouter API (text-embedding-3-small, 1536维)
├── 业务层: Python应用程序
└── 场景: 4种智能召回场景
```

## 功能特性

### 核心功能

1. **相似PRD查找** - 基于描述向量查找历史相似需求及其审批结果
2. **智能评审建议** - 从相似PRD的历史评审意见中提取建议
3. **风险识别预警** - 识别类似场景的历史风险点
4. **部门知识库检索** - 按部门检索相关审核经验和知识
5. **航班数据管理** - 完整的航班运行和机场协同决策数据模型支持

### 数据模型支持

本项目同时支持PRD审核和航班场景两种数据模型：

- **PRD审核模型**：用于产品需求文档的智能评审和召回
- **航班场景模型**：基于《航班场景v0.4.pdf》构建的完整Neo4j图数据库模型，用于航班运行和机场协同决策

详细的航班场景数据模型说明请参考：`docs/README_flight_schema.md`

### 数据模型

#### 节点类型 (Nodes)
- **PRD**: 产品需求文档
  - 属性: prd_id, title, description, status, priority, description_embedding (1536维向量)
- **ReviewComment**: 评审意见
  - 属性: comment_id, department, content, risk_level, recommendation, content_embedding
- **Department**: 部门
  - 属性: dept_id, dept_name, dept_type, lead_reviewer
- **RiskAssessment**: 风险评估
  - 属性: risk_id, risk_category, severity, probability, impact, impact_embedding
- **DecisionRecommendation**: 决策建议
  - 属性: recommendation_id, decision_type, confidence_score, reasoning

#### 关系类型 (Relationships)
- `(PRD)-[:HAS_REVIEW]->(ReviewComment)`
- `(Department)-[:PROVIDES_REVIEW]->(ReviewComment)`
- `(PRD)-[:HAS_RISK]->(RiskAssessment)`
- `(PRD)-[:HAS_RECOMMENDATION]->(DecisionRecommendation)`
- `(ReviewComment)-[:IDENTIFIES_RISK]->(RiskAssessment)`

#### 向量索引
- `prd_description_vector`: PRD描述向量索引
- `review_content_vector`: 评审内容向量索引
- `risk_impact_vector`: 风险影响向量索引

## 安装步骤

### 1. 环境要求

- Python 3.8+
- Neo4j 5.23.0 (推荐Enterprise版本以确保向量索引支持)
- OpenRouter API Key (用于生成嵌入向量)

### 2. 安装依赖

```bash
cd /Users/bytedance/Documents/Code/deep-world/neo4j-graph
pip install -r requirements.txt
```

### 3. 配置环境变量

确保 `.env` 文件包含以下配置:

```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-your-api-key

# Neo4j Environment Selection
# Set to 'local' for local development or 'production' for online environment
NEO4J_ENV = local

# Local Neo4j Configuration
NEO4J_LOCAL_URI = neo4j://127.0.0.1:7687
NEO4J_LOCAL_USER = neo4j
NEO4J_LOCAL_PASSWORD = 818iai818!
NEO4J_LOCAL_DATABASE = deepworld

# Production Neo4j Configuration
NEO4J_PROD_URI = http://10.160.4.92:7474
NEO4J_PROD_USER = neo4j
NEO4J_PROD_PASSWORD = 818iai818!
NEO4J_PROD_DATABASE = 
```

### 4. 验证配置

```bash
python -m infrastructure.config.config
```

## 使用方法

### 极速启动 - Quickstart脚本

为了方便快速上手，我们提供了`quickstart.sh`脚本，可以一键完成安装、配置验证和演示运行：

```bash
chmod +x quickstart.sh
./quickstart.sh
```

该脚本将：
1. 安装所有Python依赖
2. 验证环境变量配置
3. 运行完整演示程序

### 快速开始 - CLI命令行接口

本系统提供了统一的CLI命令行接口，所有功能都可以通过`interface.cli.main`模块访问:

```bash
python -m interface.cli.main --help
```

### 核心功能命令

#### 1. 测试Neo4j连接和插入功能

```bash
python -m interface.cli.main test-insert
```

此命令将:
- 连接到Neo4j数据库
- 创建3个测试节点(张三、李四、王五)
- 创建2个测试关系(朋友关系)
- 验证数据库写入功能

#### 2. 导入航班数据(CSV文件)

```bash
python -m interface.cli.main import-flight --data-dir data/Flight
```

#### 3. 创建向量索引

```bash
python -m interface.cli.main create-index --index-name prd-embedding-index --node-label PRD --property-name embedding
```

#### 4. 执行向量召回

```bash
python -m interface.cli.main recall --query "如何优化系统性能" --node-label PRD --top-k 5 --scenario similar_prds
```

### Python API 使用

如果你需要在Python代码中使用本系统，可以通过以下方式导入:

```python
# 导入核心组件
from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService
from domain.service.vector_indexer import VectorIndexer
from domain.service.vector_recall import VectorRecallSystem, RecallResultFormatter

# 初始化组件
with Neo4jClient() as client:
    embedding_service = EmbeddingService()
    indexer = VectorIndexer(client, embedding_service)
    recall_system = VectorRecallSystem(client, embedding_service)
    formatter = RecallResultFormatter()
    
    # 使用功能
    # ...
```

## 4种召回场景详解

### 场景1: 相似PRD查找

**用途**: 查找历史上类似的产品需求，了解其审批结果和决策依据

**示例查询**:
```python
query = "开发一个基于AI的智能客服系统，支持自然语言对话"
results = recall.find_similar_prds(query, top_k=5)
```

**返回信息**:
- 相似PRD的标题和描述
- 相似度分数 (0-1)
- 审批状态和优先级
- 最终决策类型和置信度
- 决策理由

**应用价值**:
- 快速了解类似需求的历史处理方式
- 参考历史决策避免重复错误
- 加速新需求的评估过程

### 场景2: 智能评审建议

**用途**: 基于历史相似PRD的评审意见，为新需求提供各部门的审核建议

**示例查询**:
```python
query = "实施GDPR数据隐私合规改造"
suggestions = recall.get_intelligent_review_suggestions(query, top_k=10)
# 或指定部门
suggestions = recall.get_intelligent_review_suggestions(query, department="Compliance", top_k=5)
```

**返回信息**:
- 按部门分组的历史评审意见
- 评审建议 (批准/拒绝/需修改)
- 风险等级
- 来源PRD和相似度

**应用价值**:
- 提前预知各部门可能的关注点
- 准备更充分的需求文档
- 提高首次审批通过率

### 场景3: 风险识别

**用途**: 从历史类似项目中识别潜在风险点，提前预警

**示例查询**:
```python
query = "进行大规模的云基础设施迁移和微服务改造"
risks = recall.identify_potential_risks(query, top_k=5)
```

**返回信息**:
- 风险类别 (技术/财务/资源/合规/安全)
- 严重程度和发生概率
- 风险影响描述
- 缓解策略建议
- 识别该风险的部门

**应用价值**:
- 提前识别潜在风险
- 准备风险应对方案
- 降低项目失败概率

### 场景4: 部门知识库检索

**用途**: 从特定部门的历史评审经验中检索相关知识

**示例查询**:
```python
# 查询技术部门的知识
knowledge = recall.search_department_knowledge_base(
    "系统架构升级项目",
    department="Tech",
    top_k=5
)

# 支持的部门: Tech, Finance, HR, Compliance, Security
```

**返回信息**:
- 相关的历史评审意见
- 评审人和相关性分数
- 评审建议和风险等级
- 来源PRD标题

**应用价值**:
- 构建部门知识图谱
- 传承部门审核经验
- 快速培训新员工

## 项目结构

本项目采用**领域驱动设计(DDD)**的多层级架构，将代码组织为清晰的职责层次:

```
neo4j-graph/
├── .env                          # 环境变量配置
├── requirements.txt              # Python依赖
├── README.md                     # 本文档
├── domain/                       # 领域层 (业务核心)
│   └── service/                  # 领域服务
│       ├── vector_indexer.py     # 向量索引管理
│       └── vector_recall.py      # 向量召回系统 (核心)
├── application/                  # 应用层 (业务用例)
│   └── service/                  # 应用服务
│       └── flight_csv_importer.py # 航班数据CSV导入器
├── infrastructure/               # 基础设施层 (技术实现)
│   ├── config/                   # 配置管理
│   │   └── config.py             # 配置类
│   ├── persistence/              # 持久化
│   │   └── neo4j/                # Neo4j实现
│   │       └── neo4j_client.py   # Neo4j数据库客户端
│   └── service/                  # 外部服务
│       └── embedding/            # 嵌入服务
│           └── embedding_service.py # OpenRouter嵌入服务
├── interface/                    # 接口层 (用户交互)
│   └── cli/                      # 命令行接口
│       └── main.py               # CLI入口
├── data/                         # 数据目录
│   ├── Flight/                   # 航班数据CSV
│   └── prd_scenarios.json        # PRD场景模拟数据
└── src/                          # 旧代码目录 (已废弃，用于参考)
    ├── config.py
    ├── neo4j_client.py
    ├── embedding_service.py
    ├── data_generator.py
    ├── vector_indexer.py
    ├── vector_recall.py
    └── demo.py
```

### 分层架构说明

1. **领域层(Domain)**
   - 包含核心业务逻辑和业务规则
   - 不依赖于任何外部技术或框架
   - 专注于业务问题而非技术实现

2. **应用层(Application)**
   - 协调领域层的服务来实现业务用例
   - 处理事务边界和工作流管理
   - 作为领域层和基础设施层的桥梁

3. **基础设施层(Infrastructure)**
   - 提供技术实现细节
   - 包括数据库、外部API、文件系统等
   - 为上层提供技术支持

4. **接口层(Interface)**
   - 提供用户交互接口
   - 包括CLI、Web API、GUI等
   - 处理输入输出和用户请求

## 技术细节

### 向量嵌入

- **模型**: OpenRouter API - `openai/text-embedding-3-small`
- **维度**: 1536维
- **相似度函数**: Cosine相似度
- **批处理**: 支持批量生成嵌入 (每批最多20条)

### 向量索引配置

```cypher
CREATE VECTOR INDEX `prd_description_vector`
FOR (p:PRD) ON (p.description_embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

### 向量召回查询

```cypher
CALL db.index.vector.queryNodes('prd_description_vector', $k, $embedding)
YIELD node, score
RETURN node, score
ORDER BY score DESC
```

## 性能优化建议

1. **批量嵌入生成**: 使用 `generate_embeddings_batch()` 而非单条生成
2. **向量维度**: 1536维在准确性和性能间取得平衡
3. **召回数量**: top_k建议设置为5-10，过大会影响响应速度
4. **缓存策略**: 对频繁查询的文本使用 `EmbeddingCache`
5. **索引优化**: 定期重建向量索引以优化查询性能

## 常见问题

### Q1: Neo4j Community版本是否支持向量索引？

**A**: 根据官方文档，向量索引功能主要在Enterprise版本和AuraDB中可用。Community版本的支持情况不明确，建议:
- 运行 `python neo4j_client.py` 测试向量索引支持
- 如不支持，考虑使用Neo4j Enterprise试用版或Aura Free Tier

### Q2: OpenRouter API调用失败怎么办？

**A**: 检查以下事项:
1. API Key是否正确配置在 `.env` 文件中
2. 网络连接是否正常
3. 账户余额是否充足
4. 运行 `python embedding_service.py` 测试API连接

### Q3: 向量索引创建失败

**A**: 可能原因:
1. Community版本不支持向量索引
2. Neo4j版本低于5.11
3. 索引名称冲突 - 先删除旧索引再创建

### Q4: 如何调整召回精度？

**A**:
1. 增加 `top_k` 参数获取更多候选结果
2. 调整相似度阈值过滤低分结果
3. 使用 `hybrid_search()` 结合结构化过滤
4. 优化PRD描述的详细程度

### Q5: 数据量大时如何优化性能？

**A**:
1. 分批导入数据，避免一次性导入过多
2. 使用事务批处理写入
3. 考虑启用Neo4j量化功能减少内存占用
4. 升级到Enterprise版本获得更好的性能

## 扩展方向

### 短期扩展
- [ ] 添加更多PRD场景数据模板
- [ ] 支持多模型嵌入对比 (OpenAI vs 开源模型)
- [ ] 实现评审意见的情感分析
- [ ] 添加Web界面展示

### 中期扩展
- [ ] 集成真实的审批工作流
- [ ] 实现PRD自动评分系统
- [ ] 添加时间序列分析 (审批周期趋势)
- [ ] 构建部门协作网络分析

### 长期扩展
- [ ] 接入大语言模型生成完整评审报告
- [ ] 实现多轮对话式PRD需求澄清
- [ ] 构建行业benchmark对比
- [ ] 开发插件集成到JIRA/Confluence

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系项目维护者。

---

**最后更新**: 2025-12-29

**系统版本**: v1.0.0

**作者**: AI Generated with Claude
