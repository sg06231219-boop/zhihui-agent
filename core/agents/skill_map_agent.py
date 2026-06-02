"""
岗位能力图谱 Agent
输入岗位名称，输出结构化能力图谱（技能树）
基于GLM-4-flash API，支持fallback
"""

import os
import json
import re
import time
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
            time.sleep(2)  # 等一下再重试
        except Exception as e:
            last_err = str(e)[:100]
            break  # 非网络错误不重试
    raise RuntimeError(last_err or "AI调用失败")


def _extract_json(content: str) -> dict:
    """从AI返回中提取JSON"""
    # 尝试提取```json代码块
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if json_match:
        return json.loads(json_match.group(1))
    # 尝试直接找JSON对象
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    if json_start >= 0 and json_end > json_start:
        return json.loads(content[json_start:json_end])
    raise ValueError("无法从AI返回中提取JSON")


def build_skill_map(job_name: str, major: str = "软件技术") -> Dict:
    """
    生成岗位能力图谱（AI生成 + 本地fallback）
    """
    prompt = f"""你是一位职业教育专家，请为"{major}"专业群的"{job_name}"岗位生成完整的能力图谱。

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
4. 所有内容必须专业、准确，符合行业实际"""

    messages = [
        {"role": "system", "content": "你是职业教育领域专家，擅长岗位能力分析和课程体系设计。"},
        {"role": "user", "content": prompt},
    ]

    try:
        content = _call_glm(messages)
        result = _extract_json(content)
        return result
    except Exception as e:
        raise RuntimeError(f"AI生成失败: {str(e)[:100]}")


def discover_new_job(trend_keywords: List[str]) -> Dict:
    """
    新岗位发现（赛题要求功能1）
    根据技术趋势关键词，发现并定义新兴岗位
    """
    prompt = f"""你是一位IT行业分析师，请根据以下技术趋势关键词：{', '.join(trend_keywords)}，
提出一个正在兴起的新兴岗位，并给出完整定义。

输出JSON格式：
{{
  "job_name": "新兴岗位名称",
  "core_responsibility": "核心职责",
  "required_skills": ["必备技能1", "必备技能2"],
  "bonus_skills": ["加分技能1"],
  "scenarios": ["典型应用场景1"],
  "why_emerging": "为什么这是新兴岗位"
}}"""
    messages = [
        {"role": "system", "content": "你是IT行业趋势分析师。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = _call_glm(messages, timeout=30)
        return _extract_json(content)
    except Exception as e:
        return {
            "job_name": "AI应用开发工程师",
            "core_responsibility": "将AI能力集成到业务系统中",
            "required_skills": ["Python", "LLM API调用", "Prompt Engineering"],
            "bonus_skills": ["前端开发", "数据工程"],
            "scenarios": ["企业智能化改造", "AI产品原型开发"],
            "why_emerging": "大模型普及催生大量AI应用需求",
            "fallback": True,
            "error": str(e)[:100]
        }
