# Neo4j航班场景数据模型 v0.4

## 📖 概述

本项目基于《航班场景v0.4.pdf》文档，构建了完整的Neo4j图数据库模型，用于航班运行（Flight Operation）和机场协同决策（A-CDM, Airport Collaborative Decision Making）场景。

### 核心特性

- ✅ **完整的本体建模**：基于FO/O/E三层对象体系
- ✅ **版本控制**：所有实体和关系标记为"Flight0.4"
- ✅ **事件驱动模型**：Event → Action → Update链路
- ✅ **结构化输出**：JSON Schema + Python导入脚本
- ✅ **示例数据**：完整的航班延误场景（CA123延误50分钟）

### 三层对象体系

```
FO（Form Object）  → 形式对象，最抽象层
  ↓
O（Ontology Object） → 本体对象，类型定义层
  ↓
E（Entity Object）   → 实体对象，具体实例层
```

---

## 📊 数据模型

### 节点类型（10种核心类型）

#### 1. 航班类
- **Flight** - 运行航班（执行层）
  - 状态：Created → Planned → Active → Landed → Closed
- **FlightPlan** - 航班计划（计划层）
  - 状态：Draft → Published → Updated → Archived

#### 2. 资源类 (extends Asset)
- **Airport** - 机场
- **Runway** - 跑道
- **Gate** - 登机口
- **ParkingStand** - 机位
- **Aircraft** - 飞机

#### 3. 行为主体类 (extends Actor)
- **Tower** - 塔台
- **ATCUnit** - 管制单元
- **ExternalSystem** - 外部系统（AODB, FOC, MRO等）

#### 4. 事件类 (extends Event)
- **Event** - 事件基类
- **FlightDelayedEvent** - 航班延误事件
- **FlightPlanChangedEvent** - 计划变更事件
- **ResourceConflictEvent** - 资源冲突事件

### 关系类型（8种）

#### 静态关系 (LINK TYPE - LT)
| 关系类型 | 描述 | 示例 |
|---------|------|------|
| USES | 航班使用资源 | (Flight)-[:USES]->(Gate) |
| PARKED_AT | 航班停靠机位 | (Flight)-[:PARKED_AT]->(ParkingStand) |
| ASSIGNED_TO | 飞机分配 | (Aircraft)-[:ASSIGNED_TO]->(Flight) |
| MANAGES | 机场管理资源 | (Airport)-[:MANAGES]->(Runway) |
| CONTROLS | 塔台控制资源 | (Tower)-[:CONTROLS]->(Runway) |
| IMPACTS | 事件影响实体 | (Event)-[:IMPACTS]->(Flight) |

#### 动态关系 (ACTION TYPE - AT)
| 关系类型 | 描述 | 示例 |
|---------|------|------|
| TRIGGERS | 事件触发动作 | (Event)-[:TRIGGERS]->(Flight) |
| DERIVED_FROM | 航班派生自计划 | (Flight)-[:DERIVED_FROM]->(FlightPlan) |

### 版本标识

所有节点和关系都包含 `version: "Flight0.4"` 属性，便于：
- 多版本共存
- 版本隔离查询
- 渐进式迁移

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保Neo4j已安装并运行
# 推荐版本：Neo4j 5.x+

# 安装Python依赖
pip install neo4j python-dotenv
```

### 2. 配置连接

编辑 `.env` 文件：

```env
NEO4J_URI=http://10.160.4.92:7474
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3. 导入数据

```bash
cd /Users/von/Code/test/neo4j/src

# 方式1：标准导入（保留现有数据）
python flight_importer.py

# 方式2：清空数据库后导入（谨慎使用！）
python flight_importer.py --clear

# 方式3：仅创建约束和索引
python flight_importer.py --constraints-only

# 方式4：指定自定义Schema文件
python flight_importer.py --schema /path/to/custom_schema.json
```

### 4. 验证导入

```bash
# 查看导入日志，确认：
# ✓ Constraints created: 10
# ✓ Indexes created: 4
# ✓ Nodes created: 12
# ✓ Relationships created: 13
```

---

## 📝 示例场景

### 场景描述
基于文档第9章的完整链路：

**航班延误 → 通知塔台 → 再分配Gate → 更新状态**

```
初始状态：
  - CA123航班计划09:00从ZBAA起飞，使用登机口T3-52
  - 飞机B-1234已分配

事件触发（09:30）：
  - 延误事件发生：delayMinutes=50, reasonCode=WX（天气）

动作链：
  1. NotifyTower → 通知塔台ZBAA-T3
  2. CheckGateConflict → 检测Gate冲突
  3. ReassignGate → 重分配到T3-66

最终状态：
  - Flight.status = "Delayed"
  - Flight.gateId = "T3-66"
  - Gate T3-52 释放（status = "Available"）
```

### 图谱可视化

在Neo4j Browser中运行：

```cypher
// 查看完整的延误事件链路
MATCH path = (e:Event {eventId: 'EVT-CA123-001'})-[*1..3]-(n)
WHERE e.version = 'Flight0.4'
RETURN path
```

---

## 🔍 查询示例

### 1. 查找所有延误的航班

```cypher
MATCH (f:Flight)
WHERE f.status = 'Delayed' AND f.version = 'Flight0.4'
RETURN f.flightNumber, f.origin, f.destination
```

### 2. 查看航班的所有事件

```cypher
MATCH (e:Event)-[:IMPACTS]->(f:Flight {flightId: 'CA123-20240208'})
WHERE e.version = 'Flight0.4'
RETURN e.eventType, e.eventTime, e.severity
ORDER BY e.eventTime
```

### 3. 查找登机口使用情况

```cypher
MATCH (f:Flight)-[r:USES]->(g:Gate)
WHERE g.version = 'Flight0.4'
RETURN f.flightNumber, g.gateId, r.startTime, r.endTime
ORDER BY r.startTime
```

### 4. 追踪事件触发的动作链

```cypher
MATCH (e:Event {eventId: 'EVT-CA123-001'})-[t:TRIGGERS]->(f:Flight)
WHERE e.version = 'Flight0.4'
RETURN e.eventType, t.actionType, t.triggerTime, f.flightId
ORDER BY t.triggerTime
```

### 5. 查看机场管理的所有资源

```cypher
MATCH (a:Airport {airportCode: 'ZBAA'})-[:MANAGES]->(r)
WHERE a.version = 'Flight0.4'
RETURN labels(r) AS resourceType, r
```

### 6. 查找飞机的航班链

```cypher
MATCH (aircraft:Aircraft {aircraftId: 'B-1234'})-[:ASSIGNED_TO]->(f:Flight)
WHERE f.version = 'Flight0.4'
RETURN f.flightNumber, f.origin, f.destination, f.status
ORDER BY f.actualDepTime
```

### 7. 检测Gate冲突（业务规则验证）

```cypher
// 查找可能的Gate时间冲突
MATCH (f1:Flight)-[r1:USES]->(g:Gate)<-[r2:USES]-(f2:Flight)
WHERE f1 <> f2
  AND r1.startTime < r2.endTime
  AND r1.endTime > r2.startTime
  AND f1.version = 'Flight0.4'
RETURN g.gateId, f1.flightNumber, f2.flightNumber,
       r1.startTime AS f1_start, r1.endTime AS f1_end,
       r2.startTime AS f2_start, r2.endTime AS f2_end
```

### 8. 航班状态机查询

```cypher
// 查看所有处于Active状态的航班
MATCH (f:Flight {status: 'Active'})
WHERE f.version = 'Flight0.4'
RETURN f.flightNumber, f.origin, f.destination, f.actualDepTime
```

---

## 📁 文件结构

```
/Users/von/Code/test/neo4j/
├── data/
│   └── flight_schema_v0.4.json       # JSON Schema定义（⭐核心文件）
│
├── src/
│   ├── config.py                      # 配置管理
│   ├── neo4j_client.py                # Neo4j客户端
│   └── flight_importer.py             # 导入脚本（⭐核心文件）
│
└── docs/
    └── README_flight_schema.md        # 本文档
```

---

## ⚙️ 业务规则与约束

### 1. Gate冲突约束
```
同一时间段内，Gate不得被两个航班同时占用
```

### 2. Turnaround（过站）规则
```
后续航班起飞时间 >= 前序航班落地时间 + 最小过站时间
```

### 3. Runway占用约束
```
连续两架飞机使用跑道之间必须满足最小安全间隔
```

### 4. Aircraft排班约束
```
同一时刻一架飞机只能执行一个航班
```

### 5. 状态机约束
```
航班状态必须按定义的生命周期路径迁移：
Created → Planned → Active → Landed → Closed
```

### 6. 事件-动作映射

| 事件类型 | 触发的动作 |
|---------|----------|
| FlightDelayedEvent | NotifyTower, CheckGateConflict, ReassignGate, UpdateFlightStatus |
| FlightPlanChangedEvent | UpdateFlightPlan, ReassignResource |
| ResourceConflictEvent | AlertConflict, ResolveConflict |

---

## 🔧 扩展指南

### 添加新的事件类型

1. 在JSON Schema中添加新节点类型：

```json
{
  "label": "WeatherImpactEvent",
  "extends": "Event",
  "properties": {
    "weatherType": {
      "type": "enum",
      "values": ["WX_Storm", "WX_Fog", "WX_Snow"]
    },
    "impactLevel": {
      "type": "enum",
      "values": ["Minor", "Major", "Severe"]
    }
  }
}
```

2. 定义事件影响关系：

```json
{
  "type": "IMPACTS",
  "from": "WeatherImpactEvent",
  "to": ["Flight", "Airport"]
}
```

3. 重新运行导入脚本

### 添加新的资源类型

```json
{
  "label": "Taxiway",
  "base_type": "Asset",
  "properties": {
    "taxiwayId": {"type": "string", "required": true, "unique": true},
    "length": {"type": "integer"},
    "version": {"type": "string", "default": "Flight0.4"}
  }
}
```

---

## 🎯 使用场景

### 1. 航班运行管理
- 实时航班状态监控
- 延误预警和处理
- 资源冲突检测

### 2. 机场协同决策（A-CDM）
- 里程碑事件管理（TOBT, TSAT, TTOT）
- 多部门协同（塔台、管制、地面保障）
- 容量管理

### 3. 数据分析与预测
- 延误原因分析
- 资源利用率分析
- 航班链关联分析

### 4. 智能调度
- 基于图算法的资源优化
- 冲突自动解决
- 事件驱动的自动化流程

---

## ⚠️ 注意事项

### 数据清理

```bash
# 仅删除Flight0.4版本的数据
MATCH (n)
WHERE n.version = 'Flight0.4'
DETACH DELETE n
```

### 性能优化

1. **使用索引**：所有常用查询字段已创建索引
2. **版本过滤**：始终在查询中添加 `WHERE n.version = 'Flight0.4'`
3. **批量操作**：大规模导入时使用 `UNWIND` 和批量提交

### 数据一致性

1. **唯一性约束**：所有实体ID都有唯一性约束
2. **状态验证**：航班状态迁移需遵循状态机
3. **关系验证**：导入后运行验证查询确认数据完整性

---

## 📚 参考资料

- **源文档**：航班场景v0.4.pdf
- **Neo4j官方文档**：https://neo4j.com/docs/
- **Cypher查询语言**：https://neo4j.com/docs/cypher-manual/

---

## 🤝 贡献与反馈

如需扩展或修改Schema，请：

1. 更新 `flight_schema_v0.4.json`
2. 测试导入脚本
3. 更新本文档
4. 提交变更

---

## 📄 许可证

本项目基于《航班场景v0.4.pdf》文档构建，用于航班运行知识图谱建设。

---

**版本**：Flight0.4
**创建日期**：2025-12-08
**作者**：Claude Code

