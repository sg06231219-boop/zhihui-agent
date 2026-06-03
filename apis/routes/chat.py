"""
API路由：智能对话（支持2-3轮追问，赛题要求）
POST /api/v1/chat - 多轮对话
AI生成 + fallback
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import os
import requests

router = APIRouter()

ZHIPUAI_API_KEY = os.environ.get(
    "ZHIPUAI_API_KEY",
    "a3a3123abff546999aeb4547885c4ae8.PocEri894pv9APeu"
)

class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[str] = None  # 可选：当前查看的岗位/图谱


# 预置问答知识库（AI失败时使用）
_FALLBACK_QA = {
    "html": "HTML5是前端开发的基础，重点掌握语义化标签（header/nav/main/article/footer）、表单增强、Canvas和多媒体API。建议参考MDN Web Docs系统学习。",
    "css": "CSS3核心包括：Flexbox/Grid布局、动画过渡、媒体查询响应式设计、CSS变量。推荐从Flexbox布局开始，逐步掌握Grid和动画。",
    "javascript": "JavaScript核心知识点：ES6+语法（解构/箭头函数/Promise/async-await）、DOM操作、事件机制、模块化。建议先打好基础再学框架。",
    "vue": "Vue3核心：组合式API（setup/ref/reactive）、组件通信（props/emit/provide）、Pinia状态管理、Vue Router路由。Vue3相比Vue2更轻量灵活。",
    "react": "React核心：函数组件+Hooks（useState/useEffect/useContext）、JSX语法、状态管理（Redux/Zustand）、React Router。React生态最丰富，就业需求大。",
    "工程化": "前端工程化包括：构建工具（Webpack/Vite）、代码规范（ESLint/Prettier）、Git工作流、CI/CD部署、性能监控。Vite开发体验最佳。",
    "面试": "前端面试高频考点：手写代码（防抖/节流/深拷贝）、算法（排序/链表/树）、框架原理（虚拟DOM/响应式）、网络（HTTP/HTTPS/缓存）、项目经验深挖。",
    "路径": "前端学习推荐路径：HTML/CSS基础 → JavaScript核心 → 一个框架（Vue/React）→ 工程化工具 → 性能优化 → 项目实战。一般6-12个月可达到初级前端水平。",
    "薪资": "前端开发薪资参考：初级6-10K、中级10-18K、高级18-30K、架构师30K+。一线城市薪资比二三线高30-50%。掌握Vue/React+TypeScript+工程化是高薪关键。",
}


@router.post("/chat")
async def chat(req: ChatRequest):
    """多轮对话（支持追问），AI失败时使用预置知识库"""
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
- 如果用户追问，给出更深入的解答"""

    if req.context:
        system_prompt += f"\n\n当前上下文：用户正在查看「{req.context}」相关内容。"

    messages = [{"role": "system", "content": system_prompt}]
    for msg in req.messages:
        messages.append({"role": msg.role, "content": msg.content})

    try:
        from core.utils.jwt_helper import generate_token
        token = generate_token(ZHIPUAI_API_KEY)
        resp = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json={
                "model": "glm-4-flash",
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 1000,
            },
            timeout=20,
        )
        resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return {"reply": reply}
    except Exception as e:
        # AI失败时，尝试从预置知识库匹配
        last_msg = req.messages[-1].content if req.messages else ""
        reply = _match_fallback(last_msg)
        return {"reply": reply, "fallback": True, "error": str(e)[:50]}


def _match_fallback(question: str) -> str:
    """从预置知识库中匹配回答"""
    q = question.lower()
    for keyword, answer in _FALLBACK_QA.items():
        if keyword in q:
            return answer
    return "我是职慧Agent，当前AI服务暂时不可用。您可以问我关于HTML/CSS/JavaScript/Vue/React/前端工程化/面试/学习路径/薪资等方面的问题，我会尽力回答。"
