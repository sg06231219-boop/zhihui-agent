# 职慧Agent — 职业教育岗位技能智能体
# XA-202603 挑战杯揭榜挂帅参赛项目

"""
FastAPI主入口
专业群：软件技术
岗位：前端开发工程师
核心功能：
1. 岗位能力图谱 — 输入岗位名称，输出结构化能力图谱（技能树+可视化）
2. 个性化自适应学习 — 学情诊断+学习路径推荐+成长轨迹可视化
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apis.routes import skill_map, learn_path, chat, task_convert, analytics, admin
import uvicorn

BASE_DIR = Path(__file__).parent

app = FastAPI(title="职慧Agent", version="1.3.2")

# 静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 路由
app.include_router(skill_map.router, prefix="/api/v1", tags=["能力图谱"])
app.include_router(learn_path.router, prefix="/api/v1", tags=["学习路径"])
app.include_router(chat.router, prefix="/api/v1", tags=["智能对话"])
app.include_router(task_convert.router, prefix="/api/v1", tags=["任务转化"])
app.include_router(analytics.router, prefix="/api/v1", tags=["访问统计"])
app.include_router(admin.router, prefix="/api/v1", tags=["管理后台"])

@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))

@app.get("/api/v1/health")
async def health():
    api_key = bool(os.environ.get("ZHIPUAI_API_KEY"))
    return {"status": "ok" if api_key else "degraded", "service": "zhihui-agent", "version": "1.3.2", "api_key_configured": api_key}

@app.get("/api/v1/stats")
async def get_stats():
    """返回服务统计信息"""
    import json as _json
    kb_path = BASE_DIR / "data" / "knowledge_base.json"
    history_path = BASE_DIR / "data" / "skill_map_history.json"
    kb_count = 0
    history_count = 0
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb_count = len(_json.load(f))
    except:
        pass
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history_count = len(_json.load(f))
    except:
        pass
    return {
        "service": "zhihui-agent",
        "version": "1.3.2",
        "knowledge_base_entries": kb_count,
        "skill_map_history_count": history_count,
        "api_key_configured": bool(os.environ.get("ZHIPUAI_API_KEY"))
    }

@app.get("/robots.txt")
async def robots():
    return FileResponse(str(BASE_DIR / "static" / "robots.txt"), media_type="text/plain")

@app.get("/admin")
async def admin_page():
    return FileResponse(str(BASE_DIR / "static" / "admin.html"))

@app.get("/api/v1/knowledge-base")
async def knowledge_base():
    """返回知识库数据（前端直调智谱API时需要）"""
    import json
    kb_path = BASE_DIR / "data" / "knowledge_base.json"
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 8000)))
