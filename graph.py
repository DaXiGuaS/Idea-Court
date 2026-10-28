"""
编排层：把"评审"和"判决"串成一条流程。

为什么用 LangGraph 而不是直接两次函数调用？
因为状态流转是显式的：谁产出什么、下一步读什么，一眼能看清。
这个项目里图很简单，故意不加多余节点。

判决书里的票数由 Python 统计，不交给 LLM 算——模型数数是它的弱项。
"""

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from models import ReviewResponse, ReviewResult, Speech, Verdict
from reviewer import run_review

logger = logging.getLogger(__name__)


class ReviewState(TypedDict, total=False):
    """流经整条图的状态。total=False 允许节点只返回自己更新的字段。"""

    idea: str
    history: list[Speech]
    user_reply: str
    past_ideas: list[str]
    mode: str
    result: ReviewResult
    verdict: Verdict


def review_node(state: ReviewState) -> dict:
    """节点 1：让 5 个角色发言。"""
    result = run_review(
        state["idea"],
        state.get("history", []),
        state.get("user_reply", ""),
        state.get("past_ideas", []),
        state.get("mode", "product"),
    )
    return {"result": result}


# 不同模式用不同措辞：做产品说"通过/驳回"，做决定说"可以/别冲动"
VERDICT_TEXT = {
    "product": {"pass": "通过", "reject": "驳回", "conditional": "有条件通过"},
    "decision": {"pass": "可以这么做", "reject": "别冲动", "conditional": "再想想"},
}

VERDICT_PREFIX = {
    "product": {
        "pass": "方向站得住，可以开始做。",
        "reject": "目前不具备立项条件。",
        "conditional": "方向有戏，但有几个坑必须先填。",
    },
    "decision": {
        "pass": "这个决定可以下。",
        "reject": "现在还不是做这个决定的时候。",
        "conditional": "先别急着定，还有几件事没想清楚。",
    },
}


def build_verdict(
    speeches: list[Speech],
    killer_question: str,
    mode: str = "product",
) -> Verdict:
    """纯函数：统计票数并给出判决。方便单独测试。"""
    approve = sum(1 for s in speeches if s.vote == "approve")
    reject = sum(1 for s in speeches if s.vote == "reject")
    conditional = sum(1 for s in speeches if s.vote == "conditional")

    if approve >= 3:
        kind = "pass"
    elif reject >= 3:
        kind = "reject"
    else:
        kind = "conditional"

    decision = VERDICT_TEXT.get(mode, VERDICT_TEXT["product"])[kind]
    prefix = VERDICT_PREFIX.get(mode, VERDICT_PREFIX["product"])[kind]

    summary = (
        f"{prefix}5 位评审中，{reject} 位反对、"
        f"{approve} 位支持、{conditional} 位认为有条件可做。"
    )

    return Verdict(
        decision=decision,
        approve=approve,
        reject=reject,
        conditional=conditional,
        killer_question=killer_question,
        summary=summary,
    )


def verdict_node(state: ReviewState) -> dict:
    """节点 2：汇总发言，产出判决书。"""
    result = state["result"]
    return {
        "verdict": build_verdict(
            result.speeches,
            result.killer_question,
            state.get("mode", "product"),
        )
    }


def build_graph():
    """编译评审流程。这里只有两个节点，故意保持简单。"""
    graph = StateGraph(ReviewState)
    graph.add_node("review", review_node)
    graph.add_node("verdict", verdict_node)
    graph.add_edge(START, "review")
    graph.add_edge("review", "verdict")
    graph.add_edge("verdict", END)
    return graph.compile()


def run_pipeline(
    idea: str,
    history: list[Speech] | None = None,
    user_reply: str = "",
    past_ideas: list[str] | None = None,
    mode: str = "product",
) -> ReviewResponse:
    """对外入口：跑完整条流程，返回前端需要的结构。"""
    app = build_graph()
    final_state = app.invoke(
        {
            "idea": idea,
            "history": history or [],
            "user_reply": user_reply,
            "past_ideas": past_ideas or [],
            "mode": mode,
        }
    )
    return ReviewResponse(
        idea=idea,
        speeches=final_state["result"].speeches,
        verdict=final_state["verdict"],
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    response = run_pipeline("一个帮大学生自动整理课程通知的小程序")

    for speech in response.speeches:
        print(f"{speech.role}｜{speech.vote}")
    print()
    verdict = response.verdict
    print(f"判决：{verdict.decision}")
    print(f"票数：赞成 {verdict.approve} / 反对 {verdict.reject} / 有条件 {verdict.conditional}")
    print(f"致命问题：{verdict.killer_question}")
    print(f"说明：{verdict.summary}")
