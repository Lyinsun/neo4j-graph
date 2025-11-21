"""
PRD Review Scenario Data Generator
Generate realistic PRD review data based on the Ontology model
"""
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from config import Config


class PRDDataGenerator:
    """Generate realistic PRD review scenario data"""

    def __init__(self):
        self.departments = [
            {"dept_id": "TECH", "dept_name": "技术部", "dept_type": "Tech", "lead_reviewer": "张工"},
            {"dept_id": "FIN", "dept_name": "财务部", "dept_type": "Finance", "lead_reviewer": "李会计"},
            {"dept_id": "HR", "dept_name": "人力资源部", "dept_type": "HR", "lead_reviewer": "王主管"},
            {"dept_id": "COMP", "dept_name": "合规部", "dept_type": "Compliance", "lead_reviewer": "赵律师"},
            {"dept_id": "SEC", "dept_name": "安全部", "dept_type": "Security", "lead_reviewer": "刘安全"}
        ]

        self.prd_templates = self._create_prd_templates()

    def _create_prd_templates(self) -> List[Dict[str, Any]]:
        """Create realistic PRD templates"""
        return [
            {
                "title": "移动应用用户行为分析系统开发",
                "description": "开发一个全面的移动应用用户行为分析系统，用于追踪用户在应用内的操作路径、停留时间、点击热区等行为数据。系统需要支持实时数据采集、大数据存储、可视化报表生成，并能够进行用户画像分析和个性化推荐。预计需要3个月开发周期，涉及前端、后端、数据分析团队共15人。",
                "priority": "High",
                "target_launch_date": 90
            },
            {
                "title": "GDPR数据隐私合规改造项目",
                "description": "为满足欧盟GDPR法规要求，需对现有系统进行全面数据隐私合规改造。包括用户数据加密、隐私政策更新、数据访问权限管理、数据删除机制、跨境数据传输合规性审查等。涉及法律、技术、运营多个部门协作，需要外部法律顾问支持，预计6个月完成。",
                "priority": "High",
                "target_launch_date": 180
            },
            {
                "title": "云服务成本优化方案",
                "description": "当前云服务月度开支达50万元，需要进行全面成本优化。方案包括：闲置资源清理、服务器规格右调整、存储分层优化、CDN流量优化、预留实例购买等。目标是在不影响性能的前提下，将月度成本降低30%，预计节省15万元/月。",
                "priority": "Medium",
                "target_launch_date": 60
            },
            {
                "title": "人力资源管理系统升级",
                "description": "现有HR系统已使用5年，功能老旧，性能低下。计划升级到最新版本，新增招聘管理、绩效考核、培训管理、员工自助服务等模块。支持移动端访问，集成钉钉/企业微信。涉及500+员工数据迁移，需要详细的迁移方案和应急预案。",
                "priority": "Medium",
                "target_launch_date": 120
            },
            {
                "title": "微服务架构改造",
                "description": "将现有单体应用拆分为微服务架构，提升系统可扩展性和稳定性。采用Spring Cloud技术栈，引入服务注册发现、配置中心、API网关、链路追踪等组件。需要逐步迁移，避免影响现有业务，预计12个月完成全部改造。技术风险较高，需要充分的POC验证。",
                "priority": "High",
                "target_launch_date": 365
            },
            {
                "title": "客户服务智能问答系统",
                "description": "基于大语言模型开发智能客服问答系统，替代部分人工客服工作。系统需要对接现有知识库，支持多轮对话、意图识别、情感分析。预计可减少40%的人工客服工作量，提升客户满意度。需要持续优化模型和知识库，涉及AI团队、客服部门协作。",
                "priority": "High",
                "target_launch_date": 150
            },
            {
                "title": "数据仓库建设项目",
                "description": "构建企业级数据仓库，整合来自ERP、CRM、电商平台等多个业务系统的数据。采用维度建模方法，建立统一的数据模型和指标体系。支持BI分析、数据挖掘、机器学习应用。预计存储PB级数据，需要高性能计算和存储资源。",
                "priority": "Medium",
                "target_launch_date": 180
            },
            {
                "title": "移动办公平台开发",
                "description": "开发企业移动办公平台，支持审批流程、公告通知、即时通讯、日程管理、移动考勤等功能。支持iOS和Android双平台，需要与现有OA系统集成。采用Flutter跨平台开发框架，预计3个月完成MVP版本。",
                "priority": "Medium",
                "target_launch_date": 90
            },
            {
                "title": "供应链管理系统优化",
                "description": "优化现有供应链管理系统，提升采购、库存、物流管理效率。引入智能补货算法，优化库存周转率。集成主流物流公司API，实现物流信息实时追踪。需要与ERP系统深度集成，涉及供应链部门、IT部门、财务部门协作。",
                "priority": "Medium",
                "target_launch_date": 120
            },
            {
                "title": "网络安全防护体系升级",
                "description": "全面升级网络安全防护体系，包括部署新一代防火墙、入侵检测系统、数据防泄漏系统、安全审计平台。建立7x24小时安全运营中心(SOC)，实施安全事件监控和应急响应。需要外部安全专家评估，预计投入200万元。",
                "priority": "High",
                "target_launch_date": 120
            },
            {
                "title": "电商平台性能优化",
                "description": "电商平台在促销活动期间频繁出现性能瓶颈，需要进行全面性能优化。包括数据库查询优化、缓存策略优化、CDN配置优化、前端资源优化等。目标是支持10倍并发量，确保大促期间系统稳定。需要进行压力测试验证。",
                "priority": "High",
                "target_launch_date": 45
            },
            {
                "title": "企业知识管理平台建设",
                "description": "建设企业知识管理平台，实现知识的沉淀、分享、检索、协作。支持文档管理、Wiki、问答社区、专家库等功能。引入智能推荐和语义搜索技术，提升知识利用效率。目标是将知识查找时间减少50%，促进组织学习。",
                "priority": "Low",
                "target_launch_date": 180
            },
            {
                "title": "区块链溯源系统开发",
                "description": "基于区块链技术开发产品溯源系统，记录产品从生产到销售的全流程信息。支持防伪验证、质量追溯、召回管理。采用联盟链架构，需要与上下游合作伙伴建立联盟。技术相对新颖，存在一定实施风险。",
                "priority": "Low",
                "target_launch_date": 240
            },
            {
                "title": "RPA流程自动化项目",
                "description": "引入RPA(机器人流程自动化)技术,自动化处理财务报销、数据录入、报表生成等重复性工作。预计可替代5个FTE的人力工作量，提升工作效率和准确性。需要选型RPA工具、流程分析、机器人开发、员工培训等环节。",
                "priority": "Medium",
                "target_launch_date": 90
            },
            {
                "title": "视频会议系统升级",
                "description": "现有视频会议系统稳定性差，画质模糊，需要升级到企业级方案。支持高清视频、屏幕共享、会议录制、虚拟背景等功能。支持100人同时在线会议，与日历系统集成。考虑采购腾讯会议或Zoom企业版，预算30万元/年。",
                "priority": "Low",
                "target_launch_date": 30
            },
            {
                "title": "IoT设备监控平台",
                "description": "开发IoT设备监控平台，实时监控工厂内数千台设备的运行状态。支持数据采集、异常告警、预测性维护、能耗分析等功能。采用时序数据库存储海量传感器数据，使用大屏可视化展示。需要硬件、软件、网络全方位配合。",
                "priority": "Medium",
                "target_launch_date": 180
            },
            {
                "title": "多语言国际化改造",
                "description": "为支持海外市场拓展，需对产品进行多语言国际化改造。支持英语、日语、韩语、西班牙语等主流语言。涉及界面翻译、时区处理、货币转换、本地化测试等工作。需要建立翻译管理流程，预计6个月完成。",
                "priority": "Medium",
                "target_launch_date": 180
            },
            {
                "title": "灾难恢复体系建设",
                "description": "建立完善的灾难恢复体系，确保业务连续性。包括异地数据中心建设、数据实时备份、应急切换演练、灾难恢复预案等。目标RTO(恢复时间目标)4小时，RPO(恢复点目标)1小时。需要大量基础设施投入，预算500万元。",
                "priority": "High",
                "target_launch_date": 240
            },
            {
                "title": "员工技能培训平台",
                "description": "开发在线员工技能培训平台，支持课程管理、在线学习、考试认证、学习路径规划等功能。引入微课、直播、互动练习等多种学习形式。与人力系统集成，将培训记录纳入绩效考核。目标是提升员工技能水平，降低培训成本。",
                "priority": "Low",
                "target_launch_date": 120
            },
            {
                "title": "数据安全分级分类项目",
                "description": "根据数据安全法要求，对企业数据进行分级分类管理。识别敏感数据、制定保护策略、实施访问控制、建立审计机制。涉及数据梳理、标签化、权限重构等大量工作。需要安全、合规、IT、业务部门联合推进。",
                "priority": "High",
                "target_launch_date": 150
            }
        ]

    def _generate_review_comments(self, prd_id: str, prd_description: str) -> List[Dict[str, Any]]:
        """Generate review comments for each department"""
        comments = []

        # Tech department review
        tech_comments = [
            {"content": "技术方案可行，建议采用微服务架构以提升可扩展性。需要进行POC验证关键技术点。", "recommendation": "NeedsModification", "risk_level": "Medium"},
            {"content": "技术栈选择合理，但需要考虑团队技术储备。建议增加2周技术培训时间。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "技术难度较高，现有团队能力不足，建议引入外部技术专家或延长开发周期。", "recommendation": "Reject", "risk_level": "High"},
            {"content": "技术方案清晰，架构设计合理，可以启动开发。建议加强代码评审和单元测试。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "涉及多个系统集成，接口复杂度高，建议先进行接口联调测试再全面开发。", "recommendation": "NeedsModification", "risk_level": "Medium"}
        ]

        # Finance department review
        finance_comments = [
            {"content": "预算超出年度计划50%，建议分阶段实施以分散财务压力。", "recommendation": "NeedsModification", "risk_level": "High"},
            {"content": "ROI分析合理，预计18个月回本，财务可行性好，建议批准。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "成本估算不够准确，缺少隐性成本考虑，建议重新核算后再审批。", "recommendation": "Reject", "risk_level": "Medium"},
            {"content": "预算合理，符合财务规划，可以批准。建议建立成本监控机制。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "项目收益不明确，难以量化，建议补充详细的成本收益分析。", "recommendation": "NeedsModification", "risk_level": "Medium"}
        ]

        # HR department review
        hr_comments = [
            {"content": "人力资源充足，可以支持项目开展。建议从现有团队抽调人员，避免新增编制。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "所需人力超出当前编制，需要招聘5名工程师，招聘周期至少2个月，建议延后启动。", "recommendation": "NeedsModification", "risk_level": "High"},
            {"content": "关键岗位人员流失风险高，建议增加激励措施或外包部分工作。", "recommendation": "NeedsModification", "risk_level": "Medium"},
            {"content": "人员配置合理，技能匹配度高，支持项目实施。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "涉及多部门协作，需要明确人员分工和考核机制。建议补充详细的团队组织架构。", "recommendation": "NeedsModification", "risk_level": "Low"}
        ]

        # Compliance department review
        compliance_comments = [
            {"content": "符合相关法律法规要求，数据处理流程合规，可以批准。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "涉及用户个人信息处理，必须完善隐私政策并获得用户明确同意。需要补充合规方案。", "recommendation": "NeedsModification", "risk_level": "High"},
            {"content": "跨境数据传输不符合最新监管要求，存在合规风险，建议暂缓实施。", "recommendation": "Reject", "risk_level": "High"},
            {"content": "合规审查通过，建议在实施过程中持续关注法规变化。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "需要进行数据安全影响评估，并报相关监管部门备案。建议增加合规流程时间。", "recommendation": "NeedsModification", "risk_level": "Medium"}
        ]

        # Security department review
        security_comments = [
            {"content": "安全架构设计合理，包含身份认证、权限管理、数据加密等安全措施，可以批准。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "缺少安全评估和渗透测试环节，建议增加安全测试阶段。", "recommendation": "NeedsModification", "risk_level": "Medium"},
            {"content": "涉及核心业务数据，安全风险高，必须通过外部安全审计才能上线。", "recommendation": "NeedsModification", "risk_level": "High"},
            {"content": "安全方案完善，符合安全规范，支持项目实施。", "recommendation": "Approve", "risk_level": "Low"},
            {"content": "第三方组件存在已知安全漏洞，必须升级到安全版本或更换其他组件。", "recommendation": "Reject", "risk_level": "High"}
        ]

        all_comments = [tech_comments, finance_comments, hr_comments, compliance_comments, security_comments]

        for i, dept in enumerate(self.departments):
            comment = random.choice(all_comments[i])
            comments.append({
                "comment_id": f"{prd_id}_REVIEW_{dept['dept_id']}",
                "department": dept["dept_type"],
                "dept_id": dept["dept_id"],
                "reviewer_name": dept["lead_reviewer"],
                "content": comment["content"],
                "risk_level": comment["risk_level"],
                "recommendation": comment["recommendation"],
                "feedback_type": dept["dept_type"]
            })

        return comments

    def _generate_risk_assessments(self, prd_id: str, comments: List[Dict]) -> List[Dict[str, Any]]:
        """Generate risk assessments based on review comments"""
        risks = []

        high_risk_comments = [c for c in comments if c["risk_level"] == "High"]

        for i, comment in enumerate(high_risk_comments):
            risk_category_map = {
                "Tech": "Technical",
                "Finance": "Financial",
                "HR": "Resource",
                "Compliance": "Compliance",
                "Security": "Security"
            }

            risks.append({
                "risk_id": f"{prd_id}_RISK_{i + 1}",
                "risk_category": risk_category_map.get(comment["department"], "Technical"),
                "severity": "High",
                "probability": random.uniform(0.6, 0.9),
                "impact": comment["content"],
                "mitigation_strategy": "需要制定详细的风险缓解方案并持续监控"
            })

        return risks

    def _generate_decision_recommendation(self, prd_id: str, comments: List[Dict]) -> Dict[str, Any]:
        """Generate AI decision recommendation based on review comments"""

        approve_count = sum(1 for c in comments if c["recommendation"] == "Approve")
        reject_count = sum(1 for c in comments if c["recommendation"] == "Reject")
        modify_count = sum(1 for c in comments if c["recommendation"] == "NeedsModification")

        if reject_count >= 2:
            decision = "Reject"
            confidence = 0.85
            reasoning = "多个部门建议拒绝，项目存在重大风险或不可行因素，建议暂缓实施。"
        elif approve_count >= 4:
            decision = "Approve"
            confidence = 0.90
            reasoning = "各部门评审意见积极，项目可行性高，建议批准实施。"
        elif modify_count >= 3:
            decision = "Modify"
            confidence = 0.75
            reasoning = "多个部门提出修改意见，建议完善方案后再审批。"
        else:
            decision = "RequestMoreInfo"
            confidence = 0.60
            reasoning = "评审意见分歧较大，建议补充更多信息并重新评估。"

        return {
            "recommendation_id": f"{prd_id}_RECOMMENDATION",
            "decision_type": decision,
            "confidence_score": confidence,
            "reasoning": reasoning,
            "alternative_options": ["分阶段实施", "引入外部专家", "调整预算和时间"],
            "risk_analysis": f"基于{len(comments)}个部门的评审意见，项目总体风险等级为中等。"
        }

    def generate_prd_data(self, num_prds: int = 15) -> Dict[str, Any]:
        """
        Generate complete PRD review scenario data

        Args:
            num_prds: Number of PRDs to generate

        Returns:
            dict: Complete dataset with PRDs, reviews, risks, and recommendations
        """
        # Select random PRD templates
        selected_templates = random.sample(self.prd_templates, min(num_prds, len(self.prd_templates)))

        prds = []
        all_comments = []
        all_risks = []
        all_recommendations = []

        base_date = datetime.now() - timedelta(days=180)

        for i, template in enumerate(selected_templates):
            prd_id = f"PRD_{i + 1:03d}"

            # Generate PRD
            created_at = base_date + timedelta(days=random.randint(0, 150))
            prd = {
                "prd_id": prd_id,
                "title": template["title"],
                "description": template["description"],
                "status": random.choice(["Draft", "InReview", "Approved", "Rejected", "NeedsRevision"]),
                "created_at": created_at.isoformat(),
                "updated_at": (created_at + timedelta(days=random.randint(1, 30))).isoformat(),
                "submitter": random.choice(["产品经理A", "产品经理B", "项目经理C", "业务负责人D"]),
                "priority": template["priority"],
                "target_launch_date": (created_at + timedelta(days=template["target_launch_date"])).isoformat()
            }
            prds.append(prd)

            # Generate review comments
            comments = self._generate_review_comments(prd_id, template["description"])
            for comment in comments:
                comment["created_at"] = (created_at + timedelta(days=random.randint(1, 5))).isoformat()
            all_comments.extend(comments)

            # Generate risk assessments
            risks = self._generate_risk_assessments(prd_id, comments)
            all_risks.extend(risks)

            # Generate decision recommendation
            recommendation = self._generate_decision_recommendation(prd_id, comments)
            recommendation["created_at"] = (created_at + timedelta(days=random.randint(6, 10))).isoformat()
            all_recommendations.append(recommendation)

        return {
            "departments": self.departments,
            "prds": prds,
            "review_comments": all_comments,
            "risk_assessments": all_risks,
            "decision_recommendations": all_recommendations,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "num_prds": len(prds),
                "num_comments": len(all_comments),
                "num_risks": len(all_risks),
                "num_recommendations": len(all_recommendations)
            }
        }

    def save_to_file(self, data: Dict[str, Any], filepath: Path = None):
        """Save generated data to JSON file"""
        filepath = filepath or Config.PRD_SCENARIOS_FILE

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✓ Data saved to {filepath}")
        return filepath


if __name__ == "__main__":
    # Test data generator
    print("Generating PRD Review Scenario Data...")
    print("=" * 50)

    generator = PRDDataGenerator()
    data = generator.generate_prd_data(num_prds=15)

    print(f"✓ Generated {data['metadata']['num_prds']} PRDs")
    print(f"✓ Generated {data['metadata']['num_comments']} review comments")
    print(f"✓ Generated {data['metadata']['num_risks']} risk assessments")
    print(f"✓ Generated {data['metadata']['num_recommendations']} recommendations")

    # Save to file
    generator.save_to_file(data)

    # Display sample
    print("\n" + "=" * 50)
    print("Sample PRD:")
    print(json.dumps(data['prds'][0], ensure_ascii=False, indent=2))
