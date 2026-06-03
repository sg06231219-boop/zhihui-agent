"""
API路由：岗位能力图谱
POST /api/v1/skill-map - 生成岗位能力图谱
GET  /api/v1/skill-map/history - 图谱历史
POST /api/v1/new-job - 新岗位发现
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os

router = APIRouter()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


class SkillMapRequest(BaseModel):
    job_name: str
    major: str = "软件技术"


class NewJobRequest(BaseModel):
    trend_keywords: List[str]


@router.post("/skill-map")
async def create_skill_map(req: SkillMapRequest):
    """生成岗位能力图谱（AI + fallback）"""
    from core.agents.skill_map_agent import build_skill_map

    try:
        result = build_skill_map(req.job_name, req.major)
    except Exception as e:
        # AI调用失败时使用本地fallback数据
        result = _fallback_skill_map(req.job_name, req.major)
        result["warning"] = f"AI生成失败，使用预置数据（{str(e)[:60]}）"

    # 合并本地知识库（50条标注来源的专业知识）
    if not result.get("knowledge_points"):
        result["knowledge_points"] = _load_knowledge_base()

    # 保存到历史记录
    _save_history(req.job_name, req.major, result)

    return result


@router.get("/skill-map/history")
async def get_skill_map_history():
    """获取图谱生成历史"""
    history_file = os.path.join(DATA_DIR, "skill_map_history.json")
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


@router.post("/new-job")
async def discover_new_job(req: NewJobRequest):
    """发现新岗位（赛题要求），AI失败时使用fallback"""
    from core.agents.skill_map_agent import discover_new_job

    try:
        result = discover_new_job(req.trend_keywords)
    except Exception as e:
        # AI失败时基于关键词生成基础结果
        kw = ', '.join(req.trend_keywords)
        result = {
            "job_name": f"{req.trend_keywords[0]}应用工程师",
            "core_responsibility": f"将{kw}技术应用于实际业务场景，推动技术落地与创新",
            "required_skills": [req.trend_keywords[0], "Python", "API集成", "问题分析"],
            "bonus_skills": ["项目管理", "团队协作", "行业知识"],
            "scenarios": ["企业数字化转型", "智能化产品开发", "技术咨询与服务"],
            "why_emerging": f"随着{kw}等技术的快速发展，市场对能够将新技术与业务结合的复合型人才需求激增。",
            "warning": f"AI分析失败({str(e)[:50]})，使用基础模板",
        }
    return result


def _load_knowledge_base() -> list:
    """加载本地50条知识库"""
    kb_path = os.path.join(DATA_DIR, "knowledge_base.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def _save_history(job_name: str, major: str, result: dict):
    """保存到历史"""
    history_file = os.path.join(DATA_DIR, "skill_map_history.json")
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = []
    history.append({"job_name": job_name, "major": major, "result": result})
    history = history[-20:]
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass  # Render只读文件系统可能写不了


def _fallback_skill_map(job_name: str, major: str) -> dict:
    """AI失败时的完整预置图谱数据"""
    return {
        "job_name": job_name,
        "major": major,
        "skill_tree": {
            "核心能力": [
                {"name": "HTML5语义化", "level": "基础", "description": "掌握HTML5语义化标签，理解Web标准与可访问性"},
                {"name": "CSS3布局与动画", "level": "基础", "description": "Flexbox/Grid布局，CSS动画与过渡，响应式设计"},
                {"name": "JavaScript核心", "level": "核心", "description": "ES6+语法、DOM操作、异步编程、模块化开发"},
                {"name": "前端框架应用", "level": "进阶", "description": "Vue3/React等主流框架，组件化开发模式"},
                {"name": "工程化工具", "level": "进阶", "description": "Webpack/Vite构建工具，代码规范与自动化"},
                {"name": "网络通信", "level": "核心", "description": "HTTP协议、RESTful API、跨域处理、WebSocket"},
                {"name": "性能优化", "level": "高级", "description": "加载优化、渲染优化、代码分割、监控告警"},
                {"name": "安全防护", "level": "进阶", "description": "XSS/CSRF防御、CSP策略、HTTPS与加密"},
            ],
            "专业技能": [
                {"name": "组件化开发", "tools": ["Vue3", "React"], "proficiency": "熟练掌握"},
                {"name": "状态管理", "tools": ["Pinia", "Redux", "Vuex"], "proficiency": "熟练掌握"},
                {"name": "前端路由", "tools": ["Vue Router", "React Router"], "proficiency": "熟练掌握"},
                {"name": "响应式设计", "tools": ["媒体查询", "Tailwind CSS", "Bootstrap"], "proficiency": "掌握"},
                {"name": "数据可视化", "tools": ["ECharts", "D3.js", "Chart.js"], "proficiency": "了解"},
                {"name": "移动端开发", "tools": ["Uni-app", "微信小程序", "React Native"], "proficiency": "掌握"},
                {"name": "TypeScript", "tools": ["TypeScript"], "proficiency": "熟练掌握"},
                {"name": "Node.js后端", "tools": ["Express", "Koa"], "proficiency": "了解"},
                {"name": "自动化测试", "tools": ["Jest", "Cypress", "Vitest"], "proficiency": "掌握"},
                {"name": "CI/CD部署", "tools": ["GitHub Actions", "Jenkins", "Docker"], "proficiency": "了解"},
            ],
            "工具技能": [
                {"name": "Git版本控制", "category": "协作工具", "importance": "必备"},
                {"name": "VS Code", "category": "开发工具", "importance": "必备"},
                {"name": "Chrome DevTools", "category": "调试工具", "importance": "必备"},
                {"name": "Postman / Apifox", "category": "测试工具", "importance": "推荐"},
                {"name": "Figma", "category": "设计工具", "importance": "推荐"},
                {"name": "Docker", "category": "部署工具", "importance": "推荐"},
            ],
            "软技能": [
                {"name": "沟通协作", "scenario": "团队协作、需求对接、代码评审"},
                {"name": "问题分析", "scenario": "Bug定位、性能排查、架构决策"},
                {"name": "持续学习", "scenario": "技术迭代跟进、社区参与"},
                {"name": "代码审查", "scenario": "Pull Request审查、规范执行"},
                {"name": "文档撰写", "scenario": "技术文档、README、API文档"},
            ],
        },
        "career_path": [
            {"stage": "入门期", "duration": "0-3个月", "milestones": ["掌握HTML/CSS/JS基础", "能独立完成静态页面", "理解Web标准与浏览器兼容"]},
            {"stage": "初级前端", "duration": "3-12个月", "milestones": ["掌握一个前端框架", "能完成完整项目", "理解组件化开发", "掌握基本调试技能"]},
            {"stage": "中级前端", "duration": "1-3年", "milestones": ["掌握工程化工具", "性能优化实践", "主导项目开发", "参与技术选型"]},
            {"stage": "高级前端", "duration": "3年+", "milestones": ["架构设计能力", "跨端开发经验", "技术选型决策", "团队技术指导"]},
        ],
        "related_jobs": ["全栈开发工程师", "前端架构师", "Web性能工程师", "小程序开发工程师", "前端技术经理"],
    }
