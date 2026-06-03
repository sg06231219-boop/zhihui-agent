"""
岗位典型工作任务→学习型任务 API路由
赛题核心方向3：岗位典型工作任务转化成学习型任务
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.agents.task_convert_agent import convert_task_to_learning, get_fallback_tasks
from core.agents.skill_map_agent import _call_glm, _extract_json
import os, json, traceback

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


class TaskConvertRequest(BaseModel):
    job_name: str = "前端开发工程师"
    task_name: str
    task_description: Optional[str] = ""


class PresetTasksRequest(BaseModel):
    job_name: str = "前端开发工程师"


@router.post("/task-convert")
async def task_convert(req: TaskConvertRequest):
    """
    将岗位典型工作任务转化为学习型任务
    实现「以岗定教」：典型工作任务 → 学习型工作任务
    """
    try:
        result = convert_task_to_learning(
            job_name=req.job_name,
            task_name=req.task_name,
            task_description=req.task_description or ""
        )
        return {"success": True, "data": result, "source": "ai"}
    except Exception as e:
        # Fallback: 返回预置数据
        try:
            fallback = get_fallback_tasks(req.job_name)
            return {
                "success": True,
                "data": fallback,
                "source": "fallback",
                "warning": f"AI服务暂不可用，已使用预置数据。原因: {str(e)[:50]}"
            }
        except Exception as fe:
            raise HTTPException(status_code=500, detail=f"服务异常: {str(fe)[:80]}")


@router.get("/preset-tasks")
async def preset_tasks(job_name: str = "前端开发工程师"):
    """
    获取预置的典型工作任务列表
    用于前端展示可选的典型工作任务
    """
    try:
        data = get_fallback_tasks(job_name)
        tasks = data.get("typical_tasks", [])
        # 只返回摘要信息，不返回完整学习任务
        summary = []
        for t in tasks:
            summary.append({
                "task_id": t.get("task_id"),
                "task_name": t.get("task_name"),
                "description": t.get("description", "")[:80],
                "total_hours": t.get("total_hours"),
                "learning_task_count": len(t.get("learning_tasks", [])),
                "mapped_courses": t.get("mapped_courses", [])
            })
        return {"success": True, "data": summary, "job_name": job_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:80])


@router.get("/preset-tasks/{task_id}")
async def preset_task_detail(task_id: str, job_name: str = "前端开发工程师"):
    """
    获取某个预置典型工作任务的完整学习型任务详情
    """
    try:
        data = get_fallback_tasks(job_name)
        tasks = data.get("typical_tasks", [])
        for t in tasks:
            if t.get("task_id") == task_id:
                return {"success": True, "data": t}
        raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:80])
