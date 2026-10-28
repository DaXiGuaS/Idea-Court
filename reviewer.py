"""
单次评审调用。

这是效果验证的核心：把想法喂给模型，拿回 5 条结构化发言。
如果这里的输出不好看，后面的 UI 都没有意义，先在这个文件里把角色调顺。
"""

import json
import logging

from langchain_openai import ChatOpenAI

from config import settings
from models import ReviewResult, Speech
from prompts import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    """从模型输出里截出 JSON 对象，容忍前后有解释文字或 ```json 包裹。"""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("模型输出里没有找到 JSON 对象")
    return json.loads(text[start : end + 1])


def build_llm() -> ChatOpenAI:
    """创建 LLM 客户端。超时由 .env 控制。"""
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=settings.llm_timeout,
        # 语气差异靠 prompt 里写死的人设保证，温度低一些让投票更稳定、可复现
        temperature=0.4,
    )


def run_review(
    idea: str,
    history: list[Speech] | None = None,
    user_reply: str = "",
    past_ideas: list[str] | None = None,
    mode: str = "product",
    max_attempts: int = 2,
) -> ReviewResult:
    """
    执行一次评审。

    用 JSON mode 而不是 function calling：DeepSeek 的 function calling
    是否触发不稳定，而 json_object 是它明确支持的。
    模型偶尔仍会输出不完整 JSON，所以做有限次重试。
    """
    history = history or []
    llm = build_llm().bind(response_format={"type": "json_object"})

    messages = [
        ("system", build_system_prompt(mode)),
        ("human", build_user_prompt(idea, history, user_reply, past_ideas, mode)),
    ]

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        message = llm.invoke(messages)

        # 采集 token 用量：不追求精准计费，只保留一条可观测链路
        usage = getattr(message, "usage_metadata", None)
        if usage:
            logger.info("LLM usage: %s", usage)

        content = message.content
        if isinstance(content, list):  # 少数情况下 content 是分块结构
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )

        try:
            data = _extract_json(content)
            result = ReviewResult.model_validate(data)

            # 轮次由程序决定，不信任模型自己填
            current_round = history[-1].round + 1 if history else 1
            for speech in result.speeches:
                speech.round = current_round
            return result
        except Exception as exc:
            last_error = exc
            logger.warning("第 %s 次解析失败：%s", attempt, exc)

    raise ValueError(f"连续 {max_attempts} 次没有得到结构化结果：{last_error}")


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    test_idea = "一个帮大学生记课表的小程序，能自动识别班级群里的课程通知"
    review = run_review(test_idea)

    for speech in review.speeches:
        print(f"\n{speech.role}｜{speech.focus}｜投票：{speech.vote}")
        print(f"  {speech.content}")
        print(f"  理由：{speech.reason}")

    print(f"\n最致命的问题：{review.killer_question}")
    print("\n=== 原始 JSON ===")
    print(json.dumps(review.model_dump(), ensure_ascii=False, indent=2))
