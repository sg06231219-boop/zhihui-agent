"""
API路由：智能对话（支持2-3轮追问，赛题要求）
POST /api/v1/chat - 多轮对话
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[str] = None  # 可选：当前查看的岗位/图谱


@router.post("/chat")
async def chat(req: ChatRequest):
    """多轮对话（支持追问）"""
    import os
    import requests
    
    api_key = os.environ.get(
        "ZHIPUAI_API_KEY",
        "a3a3123abff546999aeb4547885c4ae8.PocEri894pv9APeu"
    )
    
    system_prompt = """你是「职慧Agent」，一位专业的职业教育顾问。
你的职责是：
1. 帮助用户了解岗位能力要求
2. 解答关于前端开发、软件技术相关的问题
3. 提供职业规划建议
4. 解释岗位能力图谱中各技能的含义和学习方法

回答要求：
- 专业准确，引用行业标准
- 通俗易懂，适合职校学生理解
- 提供具体可操作的建议
- 如果用户追问，给出更深入的解答
"""
    
    if req.context:
        system_prompt += f"\n\n当前上下文：用户正在查看「{req.context}」相关内容。"
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in req.messages:
        messages.append({"role": msg.role, "content": msg.content})
    
    resp = requests.post(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "glm-4-flash",
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 1000,
        },
        timeout=30,
    )
    resp.raise_for_status()
    reply = resp.json()["choices"][0]["message"]["content"]
    
    return {"reply": reply}