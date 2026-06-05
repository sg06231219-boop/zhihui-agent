"""职慧Agent 管理员后台API"""
import os, json, hashlib, time, secrets
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, HTTPException, Cookie
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin", tags=["管理后台"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Lys13579")
TOKENS_FILE = DATA_DIR / "admin_tokens.json"
SESSION_MAX_AGE = 3600 * 8  # 8小时

# ---- Token管理 ----
def _load_tokens():
    if TOKENS_FILE.exists():
        try:
            with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_tokens(tokens):
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False)

def _verify_token(token: str) -> bool:
    tokens = _load_tokens()
    if token not in tokens:
        return False
    info = tokens[token]
    if time.time() - info.get("created", 0) > SESSION_MAX_AGE:
        tokens.pop(token, None)
        _save_tokens(tokens)
        return False
    return True

def _cleanup_tokens():
    tokens = _load_tokens()
    now = time.time()
    changed = False
    for t in list(tokens):
        if now - tokens[t].get("created", 0) > SESSION_MAX_AGE:
            del tokens[t]
            changed = True
    if changed:
        _save_tokens(tokens)

# ---- 认证依赖 ----
class LoginReq(BaseModel):
    password: str

@router.post("/login")
async def login(body: LoginReq, response: Response):
    _cleanup_tokens()
    if body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="密码错误")
    token = secrets.token_hex(32)
    tokens = _load_tokens()
    tokens[token] = {"created": time.time(), "ip": "admin"}
    _save_tokens(tokens)
    response.set_cookie(
        key="admin_token", value=token, httponly=True,
        max_age=SESSION_MAX_AGE, samesite="lax"
    )
    return {"ok": True, "token": token}

@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("admin_token", "")
    tokens = _load_tokens()
    tokens.pop(token, None)
    _save_tokens(tokens)
    response.delete_cookie("admin_token")
    return {"ok": True}

def _check_auth(request: Request):
    token = request.cookies.get("admin_token", "")
    if not _verify_token(token):
        raise HTTPException(status_code=401, detail="未登录或会话过期")

# ---- 统计面板 ----
@router.get("/stats")
async def stats(request: Request):
    _check_auth(request)
    kb_path = DATA_DIR / "knowledge_base.json"
    kb_count = 0
    if kb_path.exists():
        try:
            with open(kb_path, 'r', encoding='utf-8') as f:
                kb_count = len(json.load(f))
        except:
            pass

    # 访客统计
    analytics_file = DATA_DIR / "analytics.json"
    today_pv = today_uv = total_pv = total_sessions = 0
    online_users = 0
    if analytics_file.exists():
        try:
            with open(analytics_file, 'r', encoding='utf-8') as f:
                adata = json.load(f)
            today = datetime.now().strftime("%Y-%m-%d")
            td = adata.get("daily", {}).get(today, {})
            today_pv = td.get("pv", 0)
            today_uv = len(td.get("uv_ips", []))
            total_pv = sum(d.get("pv", 0) for d in adata.get("daily", {}).values())
            total_sessions = sum(d.get("sessions", 0) for d in adata.get("daily", {}).values())
            cutoff = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
            online_users = len(set(r.get("ip", "") for r in adata.get("recent", []) if r.get("time", "") >= cutoff))
        except:
            pass

    # 生成历史
    history_path = DATA_DIR / "skill_map_history.json"
    history_count = 0
    if history_path.exists():
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_count = len(json.load(f))
        except:
            pass

    return {
        "version": "1.3.1",
        "knowledge_base_count": kb_count,
        "today_pv": today_pv,
        "today_uv": today_uv,
        "total_pv": total_pv,
        "total_sessions": total_sessions,
        "online_users": online_users,
        "history_count": history_count,
        "uptime": "running"
    }

# ---- 访客详情 ----
@router.get("/visitors")
async def visitors(request: Request, days: int = 7):
    _check_auth(request)
    analytics_file = DATA_DIR / "analytics.json"
    if not analytics_file.exists():
        return {"daily_trend": [], "top_pages": [], "devices": {}, "browsers": {}, "recent": []}
    try:
        with open(analytics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return {"daily_trend": [], "top_pages": [], "devices": {}, "browsers": {}, "recent": []}

    daily_trend = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        dd = data.get("daily", {}).get(d, {})
        daily_trend.append({
            "date": d, "pv": dd.get("pv", 0),
            "uv": len(dd.get("uv_ips", [])), "sessions": dd.get("sessions", 0)
        })
    pages_sorted = sorted(data.get("pages", {}).items(), key=lambda x: x[1].get("pv", 0), reverse=True)[:10]
    return {
        "daily_trend": daily_trend,
        "top_pages": [{"path": p, "pv": v.get("pv", 0), "title": v.get("title", p)} for p, v in pages_sorted],
        "devices": data.get("devices", {}),
        "browsers": data.get("browsers", {}),
        "referrers": data.get("referrers", {}),
        "recent": data.get("recent", [])[-30:]
    }

# ---- 知识库管理 ----
@router.get("/knowledge")
async def knowledge(request: Request):
    _check_auth(request)
    kb_path = DATA_DIR / "knowledge_base.json"
    if not kb_path.exists():
        return {"items": [], "total": 0}
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        return {"items": items[:20], "total": len(items)}
    except:
        return {"items": [], "total": 0}

# ---- 系统信息 ----
@router.get("/system")
async def system_info(request: Request):
    _check_auth(request)
    import platform
    return {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "env_vars": {
            "PORT": os.environ.get("PORT", "not set"),
            "ADMIN_PASSWORD": "***" if ADMIN_PASSWORD else "not set",
            "ZHIPUAI_API_KEY": "***" if os.environ.get("ZHIPUAI_API_KEY") else "not set"
        },
        "data_files": [f.name for f in DATA_DIR.iterdir()] if DATA_DIR.exists() else [],
        "routes": ["skill_map", "learn_path", "chat", "task_convert", "analytics", "admin"]
    }
