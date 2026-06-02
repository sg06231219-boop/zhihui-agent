"""
个性化学习路径 Agent
基于学情诊断推荐学习路径，可视化成长轨迹
AI生成 + 完整fallback
"""

import os
import json
import re
import requests
from typing import Dict, List

ZHIPUAI_API_KEY = os.environ.get(
    "ZHIPUAI_API_KEY",
    "a3a3123abff546999aeb4547885c4ae8.PocEri894pv9APeu"
)

def _call_glm(messages: list, temperature: float = 0.3, timeout: int = 45) -> str:
    """调用智谱GLM-4-flash，带超时和重试"""
    last_err = None
    for attempt in range(2):
        try:
            resp = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ZHIPUAI_API_KEY}",
                },
                json={
                    "model": "glm-4-flash",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 2000,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            last_err = "AI请求超时"
        except requests.exceptions.ConnectionError:
            last_err = "AI服务连接失败"
            import time; time.sleep(2)
        except Exception as e:
            last_err = str(e)[:100]
            break
    raise RuntimeError(last_err or "AI调用失败")


def _extract_json(content: str) -> dict:
    """从AI返回中提取JSON"""
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if json_match:
        return json.loads(json_match.group(1))
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    if json_start >= 0 and json_end > json_start:
        return json.loads(content[json_start:json_end])
    raise ValueError("无法从AI返回中提取JSON")


def diagnose_learning(user_profile: Dict, target_job: str) -> Dict:
    """
    学情诊断：分析用户当前技能水平与目标岗位的差距
    AI生成 + fallback
    """
    prompt = f"""你是一位职业教育学情诊断专家。请分析以下学生画像与目标岗位的匹配度。

学生画像：
{json.dumps(user_profile, ensure_ascii=False, indent=2)}

目标岗位：{target_job}

请输出JSON格式：
{{
  "match_score": 75,
  "mastered_skills": ["已掌握的技能1"],
  "gap_skills": ["欠缺的技能1"],
  "gap_level": {{
    "核心能力": {{"gap": 2, "detail": "欠缺React和Vue框架经验"}},
    "专业技能": {{"gap": 2, "detail": "需要加强"}},
    "工具技能": {{"gap": 1, "detail": "基本掌握"}},
    "软技能": {{"gap": 1, "detail": "需实践提升"}}
  }},
  "diagnosis_summary": "综合诊断结论",
  "priority_skills": ["优先补强的技能1"],
  "estimated_hours": 320
}}"""
    messages = [
        {"role": "system", "content": "你是职业教育学情诊断专家，擅长分析技能差距和制定学习计划。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = _call_glm(messages)
        return _extract_json(content)
    except Exception as e:
        # fallback诊断
        skills = user_profile.get("skills", [])
        return {
            "match_score": min(len(skills) * 8, 60),
            "mastered_skills": skills,
            "gap_skills": ["JavaScript进阶", "前端框架", "工程化工具"],
            "gap_level": {
                "核心能力": {"gap": 2, "detail": "部分缺失"},
                "专业技能": {"gap": 2, "detail": "需要加强"},
                "工具技能": {"gap": 1, "detail": "基本掌握"},
                "软技能": {"gap": 1, "detail": "需实践提升"},
            },
            "diagnosis_summary": f"已掌握{len(skills)}项技能，与目标岗位{target_job}存在一定差距，建议系统学习。",
            "priority_skills": ["JavaScript核心", "Vue3/React框架", "前端工程化"],
            "estimated_hours": 320,
            "warning": f"AI诊断失败({str(e)[:50]})，使用基础诊断",
        }


def generate_learning_path(diagnosis: Dict, target_job: str, weeks: int = 12) -> Dict:
    """
    基于诊断结果生成个性化学习路径
    AI生成 + fallback
    """
    prompt = f"""基于以下学情诊断结果，为「{target_job}」岗位制定{weeks}周的学习路径。

诊断结果：
{json.dumps(diagnosis, ensure_ascii=False, indent=2)}

输出JSON格式：
{{
  "total_weeks": {weeks},
  "path": [
    {{
      "phase": "阶段名称",
      "weeks": "第1-3周",
      "objectives": ["目标1"],
      "tasks": [
        {{
          "task_name": "任务名",
          "knowledge_points": ["知识点1"],
          "practice": "实践任务",
          "resources": ["推荐资源1"],
          "assessment": "考核方式"
        }}
      ],
      "milestone": "阶段性成果"
    }}
  ],
  "growth_trajectory": [
    {{"week": 1, "score": 30}},
    {{"week": {weeks//3}, "score": 55}},
    {{"week": {weeks*2//3}, "score": 75}},
    {{"week": {weeks}, "score": 85}}
  ]
}}"""
    messages = [
        {"role": "system", "content": "你是职业教育课程设计专家。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = _call_glm(messages)
        return _extract_json(content)
    except Exception as e:
        # fallback学习路径
        w3 = max(weeks // 3, 1)
        w23 = max(weeks * 2 // 3, w3 + 1)
        return {
            "total_weeks": weeks,
            "path": [
                {
                    "phase": "Phase 1: 基础夯实",
                    "weeks": f"第1-{w3}周",
                    "tasks": [
                        {"task_name": "HTML5/CSS3核心", "knowledge_points": ["HTML5语义化", "CSS3 Flexbox/Grid"], "practice": "完成3个静态页面"},
                        {"task_name": "JavaScript核心", "knowledge_points": ["ES6+语法", "DOM操作", "异步编程"], "practice": "实现交互组件"},
                    ],
                    "milestone": "能独立完成响应式页面"
                },
                {
                    "phase": "Phase 2: 框架实战",
                    "weeks": f"第{w3+1}-{w23}周",
                    "tasks": [
                        {"task_name": "Vue3/React入门", "knowledge_points": ["组件化开发", "状态管理", "路由"], "practice": "完成SPA项目"},
                    ],
                    "milestone": "能使用框架完成完整项目"
                },
                {
                    "phase": "Phase 3: 进阶提升",
                    "weeks": f"第{w23+1}-{weeks}周",
                    "tasks": [
                        {"task_name": "工程化与性能优化", "knowledge_points": ["Webpack/Vite", "性能优化", "安全防护"], "practice": "优化项目性能"},
                    ],
                    "milestone": "达到岗位基本要求"
                },
            ],
            "growth_trajectory": [
                {"week": 0, "score": 30}, {"week": w3, "score": 55},
                {"week": w23, "score": 75}, {"week": weeks, "score": 85},
            ],
            "warning": f"AI生成失败({str(e)[:50]})，使用预置学习路径",
        }
