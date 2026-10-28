"""
Web 层：对外暴露评审接口。

- POST /api/review  提交想法，返回完整评审 + 判决书
- GET  /            前端页面（Step 6 实现）

LLM 超时在 config.py 里由 LLM_TIMEOUT 控制；
异常统一转成 502，避免把内部堆栈直接抛给前端。
"""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from graph import run_pipeline
from models import ReviewRequest, ReviewResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="想法法庭", description="让 5 个 AI 评审围攻你的想法")


@app.post("/api/review", response_model=ReviewResponse)
def review(payload: ReviewRequest) -> ReviewResponse:
    """跑一场完整评审。输入校验由 Pydantic 完成，这里只处理下游异常。"""
    try:
        return run_pipeline(
            payload.idea,
            payload.history,
            payload.user_reply,
            payload.past_ideas,
            payload.mode,
        )
    except Exception as exc:
        logger.exception("评审失败")
        raise HTTPException(status_code=502, detail=f"评审服务出错：{exc}") from exc


@app.get("/")
def index() -> FileResponse:
    """返回前端页面。"""
    return FileResponse(BASE_DIR / "static" / "index.html")
