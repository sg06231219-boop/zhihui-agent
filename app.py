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
from apis.routes import skill_map, learn_path, chat
import uvicorn

BASE_DIR = Path(__file__).parent

app = FastAPI(title="职慧Agent", version="1.0.0")

# 静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 路由
app.include_router(skill_map.router, prefix="/api/v1", tags=["能力图谱"])
app.include_router(learn_path.router, prefix="/api/v1", tags=["学习路径"])
app.include_router(chat.router, prefix="/api/v1", tags=["智能对话"])

@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "zhihui-agent", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 8000)))
