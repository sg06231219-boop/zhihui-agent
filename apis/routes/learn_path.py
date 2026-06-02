"""
API路由：个性化学习路径
POST /api/v1/diagnose - 学情诊断
POST /api/v1/learn-path - 生成学习路径
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import os

router = APIRouter()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


class DiagnoseRequest(BaseModel):
    user_profile: Dict  # {skills: [...], experience: "...", projects: [...]}
    target_job: str


class LearnPathRequest(BaseModel):
    diagnosis: Dict
    target_job: str
    weeks: int = 12


@router.post("/diagnose")
async def diagnose(req: DiagnoseRequest):
    """学情诊断"""
    from core.agents.learn_path_agent import diagnose_learning
    
    try:
        result = diagnose_learning(req.user_profile, req.target_job)
    except Exception as e:
        # AI失败时返回基础诊断
        skills = req.user_profile.get("skills", [])
        result = {
            "match_score": min(len(skills) * 8, 60),
            "gap_level": {
                "核心能力": {"gap": 2, "detail": "部分缺失"},
                "专业技能": {"gap": 2, "detail": "需要加强"},
                "工具技能": {"gap": 1, "detail": "基本掌握"},
                "软技能": {"gap": 1, "detail": "需实践提升"},
            },
            "diagnosis_summary": f"已掌握{len(skills)}项技能，与目标岗位{req.target_job}存在一定差距，建议系统学习。",
            "warning": f"AI诊断失败({str(e)[:50]})，使用基础诊断",
        }
    
    # 保存
    diag_file = os.path.join(DATA_DIR, "diagnoses.json")
    try:
        with open(diag_file, "r", encoding="utf-8") as f:
            records = json.load(f)
    except:
        records = []
    records.append({"target_job": req.target_job, "result": result})
    records = records[-20:]
    with open(diag_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    
    return result


@router.post("/learn-path")
async def generate_learn_path(req: LearnPathRequest):
    """生成学习路径"""
    from core.agents.learn_path_agent import generate_learning_path
    
    try:
        result = generate_learning_path(req.diagnosis, req.target_job, req.weeks)
    except Exception as e:
        # AI失败时返回基础路径
        result = {
            "path": [
                {"phase": "Phase 1: 基础夯实", "weeks": f"第1-{req.weeks//3}周", "tasks": [
                    {"task_name": "HTML5/CSS3核心", "knowledge_points": ["HTML5语义化", "CSS3 Flexbox/Grid"], "practice": "完成3个静态页面"},
                    {"task_name": "JavaScript核心", "knowledge_points": ["ES6+语法", "DOM操作", "异步编程"], "practice": "实现交互组件"},
                ], "milestone": "能独立完成响应式页面"},
                {"phase": "Phase 2: 框架实战", "weeks": f"第{req.weeks//3+1}-{req.weeks*2//3}周", "tasks": [
                    {"task_name": "Vue3/React入门", "knowledge_points": ["组件化开发", "状态管理", "路由"], "practice": "完成SPA项目"},
                ], "milestone": "能使用框架完成完整项目"},
                {"phase": "Phase 3: 进阶提升", "weeks": f"第{req.weeks*2//3+1}-{req.weeks}周", "tasks": [
                    {"task_name": "工程化与性能优化", "knowledge_points": ["Webpack/Vite", "性能优化", "安全防护"], "practice": "优化项目性能"},
                ], "milestone": "达到岗位基本要求"},
            ],
            "growth_trajectory": [
                {"week": 0, "score": 30}, {"week": req.weeks//3, "score": 55},
                {"week": req.weeks*2//3, "score": 75}, {"week": req.weeks, "score": 85},
            ],
            "warning": f"AI生成失败({str(e)[:50]})，使用预置学习路径",
        }
    return result