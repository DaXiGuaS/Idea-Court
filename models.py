"""
数据模型层。

职责：用 Pydantic 约束 LLM 的输出结构，减少"角色串味"和格式跑偏。
注意：这里只定义"数据长什么样"，不写任何业务逻辑。
"""

from typing import Literal

from pydantic import BaseModel, Field


# ============ LLM 输出：单个角色的发言 ============
class Speech(BaseModel):
    """一个 AI 评审的一次发言。"""

    role: str = Field(description="角色名，如：产品经理老周")
    focus: str = Field(description="本次质疑的角度，4-8 个字，如：用户痛点")
    content: str = Field(description="质疑正文，2-4 句，口语化，可以直接怼人")
    vote: Literal["approve", "reject", "conditional"] = Field(
        description="approve=支持立项 / reject=反对 / conditional=有条件通过"
    )
    reason: str = Field(description="投这一票的理由，一句话")
    round: int = Field(
        default=1,
        description="第几轮发言。单轮评审固定为 1；用户反驳后递增，留给多轮讨论用",
    )


# ============ LLM 输出：一整场评审 ============
class ReviewResult(BaseModel):
    """一次评审的完整结果（由 LLM 一次产出）。"""

    speeches: list[Speech] = Field(description="5 个角色各一条，顺序固定")
    killer_question: str = Field(description="整场最致命的那一个问题，一句话")


# ============ 请求 ============
class ReviewRequest(BaseModel):
    """前端提交的评审请求。"""

    idea: str = Field(min_length=1, max_length=500, description="用户提交的想法")
    history: list[Speech] = Field(
        default_factory=list,
        description="之前的发言记录。首轮为空；用户反驳后带上，让角色接着追问",
    )
    user_reply: str = Field(
        default="",
        max_length=500,
        description="用户对上一轮评审的反驳。首轮为空",
    )
    past_ideas: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="用户之前提交过的想法，用于让某个角色顺口损一句",
    )
    mode: Literal["product", "decision"] = Field(
        default="product",
        description="评审模式：product=做产品，decision=要不要做某个决定",
    )


# ============ 响应：判决书 ============
class Verdict(BaseModel):
    """判决书。票数由程序统计，不交给 LLM 算，避免它数错。"""

    decision: str = Field(description="判决文案，随评审模式变化")
    approve: int = Field(ge=0, description="赞成票数")
    reject: int = Field(ge=0, description="反对票数")
    conditional: int = Field(ge=0, description="有条件通过票数")
    killer_question: str
    summary: str = Field(description="判决理由，2-3 句，必须点名最致命的问题")


class ReviewResponse(BaseModel):
    """接口返回给前端的完整结果。"""

    idea: str
    speeches: list[Speech]
    verdict: Verdict


if __name__ == "__main__":
    # 自测：能构造 -> 能序列化 -> 非法值会被拒绝
    speech = Speech(
        role="产品经理老周",
        focus="用户痛点",
        content="这解决谁的痛？你自己会用吗？",
        vote="reject",
        reason="找不到明确用户",
    )
    verdict = Verdict(
        decision="驳回",
        approve=0,
        reject=1,
        conditional=0,
        killer_question="谁会用？",
        summary="没有人需要它。",
    )
    response = ReviewResponse(idea="一个帮你记账的 App", speeches=[speech], verdict=verdict)
    print(response.model_dump_json(indent=2))

    print("\n=== 非法 vote 应当被拒绝 ===")
    try:
        Speech(role="x", focus="x", content="x", vote="maybe", reason="x")
    except Exception as exc:
        print(f"OK，已按预期拒绝：{type(exc).__name__}")
