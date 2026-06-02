"""
岗位能力图谱 Agent
输入岗位名称，输出结构化能力图谱（技能树）
基于GLM-4-flash API
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
    """调用智谱GLM-4-flash"""
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
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_skill_map(job_name: str, major: str = "软件技术") -> Dict:
    """
    生成岗位能力图谱
    输出结构化JSON：
    {
      "job_name": "...",
      "major": "...",
      "skill_tree": {
        "核心能力": [...],
        "专业技能": [...],
        "工具技能": [...],
        "软技能": [...]
      },
      "knowledge_points": [...],   # 知识点列表
      "career_path": [...],        # 成长路径
      "related_jobs": [...]         # 关联岗位
    }
    """
    prompt = f"""
你是一位职业教育专家，请为"{major}"专业群的"{job_name}"岗位生成完整的能力图谱。

请严格按照以下JSON格式输出（不要输出任何其他内容）：

```json
{{
  "job_name": "{job_name}",
  "major": "{major}",
  "skill_tree": {{
    "核心能力": [
      {{"name": "能力名称", "level": "基础/进阶/高级", "description": "描述"}}
    ],
    "专业技能": [
      {{"name": "技能名称", "tools": ["工具1", "工具2"], "proficiency": "掌握程度"}}
    ],
    "工具技能": [
      {{"name": "工具名", "category": "开发工具/测试工具/设计工具", "importance": "必备/推荐"}}
    ],
    "软技能": [
      {{"name": "软技能名", "scenario": "适用场景"}}
    ]
  }},
  "knowledge_points": [
    {{"point": "知识点", "category": "基础/核心/拓展", "reference": "参考来源或标准"}}
  ],
  "career_path": [
    {{"stage": "入门/初级/中级/高级", "duration": "所需时间", "milestones": ["里程碑1", "里程碑2"]}}
  ],
  "related_jobs": ["关联岗位1", "关联岗位2"]
}}
```

要求：
1. 知识点必须参考《Web前端开发职业技能等级标准》等权威标准
2. 至少包含8个核心能力、10个专业技能、6个工具技能、5个软技能
3. 知识点至少20条，覆盖HTML/CSS/JS/框架/工程化等方向
4. 所有内容必须专业、准确，符合行业实际
"""

    messages = [
        {"role": "system", "content": "你是职业教育领域专家，擅长岗位能力分析和课程体系设计。"},
        {"role": "user", "content": prompt},
    ]

    try:
        content = _call_glm(messages)
        # 提取JSON
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        else:
            # 尝试直接解析
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                content = content[json_start:json_end]
        
        result = json.loads(content)
        return result
    except Exception as e:
        # 返回结构化错误+默认数据
        return {
            "job_name": job_name,
            "major": major,
            "skill_tree": {
                "核心能力": [
                    {"name": "HTML5语义化", "level": "基础", "description": "掌握HTML5语义化标签，理解Web标准"},
                    {"name": "CSS3布局与动画", "level": "基础", "description": "掌握Flexbox/Grid布局，CSS动画"},
                    {"name": "JavaScript核心", "level": "核心", "description": "掌握ES6+语法、DOM操作、异步编程"},
                    {"name": "前端框架应用", "level": "进阶", "description": "熟练使用Vue/React等主流框架"},
                    {"name": "工程化工具", "level": "进阶", "description": "掌握Webpack/Vite等构建工具"},
                ],
                "专业技能": [],
                "工具技能": [],
                "软技能": []
            },
            "knowledge_points": [],
            "career_path": [],
            "related_jobs": [],
            "error": str(e)
        }


def discover_new_job(trend_keywords: List[str]) -> Dict:
    """
    新岗位发现（赛题要求功能1）
    根据技术趋势关键词，发现并定义新兴岗位
    """
    prompt = f"""
你是一位IT行业分析师，请根据以下技术趋势关键词：{', '.join(trend_keywords)}，
提出一个正在兴起的新兴岗位，并给出完整定义。

输出JSON格式：
{{
  "job_name": "新兴岗位名称",
  "core_responsibility": "核心职责",
  "required_skills": ["必备技能1", "必备技能2"],
  "bonus_skills": ["加分技能1"],
  "scenarios": ["典型应用场景1"],
  "why_emerging": "为什么这是新兴岗位"
}}
"""
    messages = [
        {"role": "system", "content": "你是IT行业趋势分析师。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = _call_glm(messages)
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        result = json.loads(content)
        return result
    except Exception as e:
        return {"error": str(e)}
