"""
个性化学习路径 Agent
基于学情诊断推荐学习路径，可视化成长轨迹
"""

import os
import json
import requests
from typing import Dict, List

ZHIPUAI_API_KEY = os.environ.get(
    "ZHIPUAI_API_KEY",
    "a3a3123abff546999aeb4547885c4ae8.PocEri894pv9APeu"
)

def _call_glm(messages: list, temperature: float = 0.3) -> str:
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
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def diagnose_learning(user_profile: Dict, target_job: str) -> Dict:
    """
    学情诊断：分析用户当前技能水平与目标岗位的差距
    输入：用户画像（已掌握技能/学习时长/项目经验）
    输出：差距分析+学习建议
    """
    prompt = f"""
你是一位职业教育学情诊断专家。请分析以下学生画像与目标岗位的匹配度。

学生画像：
{json.dumps(user_profile, ensure_ascii=False, indent=2)}

目标岗位：{target_job}

请输出JSON格式：
{{
  "match_score": 75,
  "mastered_skills": ["已掌握的技能1"],
  "gap_skills": ["欠缺的技能1"],
  "gap_level": {{
    "基础技能": {{"gap": 0, "detail": "无差距"}},
    "核心技能": {{"gap": 2, "detail": "欠缺React和Vue框架经验"}},
    "工程化": {{"gap": 3, "detail": "完全不了解前端工程化"}}
  }},
  "diagnosis_summary": "综合诊断结论",
  "priority_skills": ["优先补强的技能1"],
  "estimated_hours": 320
}}
"""
    messages = [
        {"role": "system", "content": "你是职业教育学情诊断专家，擅长分析技能差距和制定学习计划。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = _call_glm(messages)
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        return json.loads(content)
    except Exception as e:
        return {"error": str(e), "match_score": 0}


def generate_learning_path(diagnosis: Dict, target_job: str, weeks: int = 12) -> Dict:
    """
    基于诊断结果生成个性化学习路径
    """
    prompt = f"""
基于以下学情诊断结果，为「{target_job}」岗位制定{weeks}周的学习路径。

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
    {{"week": 4, "score": 50}},
    {{"week": 8, "score": 70}},
    {{"week": 12, "score": 85}}
  ]
}}
"""
    messages = [
        {"role": "system", "content": "你是职业教育课程设计专家。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = _call_glm(messages)
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}
