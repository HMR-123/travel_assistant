import asyncio
import json
import logging
import re
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


# 创建一个基类
class OpenAIBaseAgent:
    def __init__(
        self,
        api_key: str,
        model_name: str = "openai:gpt-3.5-turbo",
        temperature: float = 0.2,
        timeout: int = 30,
        max_retries: int = 2,
    ) -> None:
        # LLM 交互抽象层
        self.model = init_chat_model(
            model_name,
            openai_api_key=api_key,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )

    # 2.创建一个异步方法
    async def _chat(self, system_instructions: str, user_instructions: str) -> str:
        messages = [
            SystemMessage(content=system_instructions),
            HumanMessage(content=user_instructions),
        ]
        if hasattr(self.model, "ainvoke"):
            response = await self.model.ainvoke(messages)
        else:
            response = await asyncio.to_thread(self.model.invoke, messages)

        content = getattr(response, "content", None)
        if content is None:
            content = str(response)
        return content

    # 3.创建一个同步方法
    def _parse_json(self, raw_text: str) -> Any:
        text = raw_text.strip()
        if not text:
            raise ValueError("Empty response from model")

        for pattern in (r"\{.*\}", r"\[.*\]"):
            match = re.search(pattern, text, re.S)
            if match:
                candidate = match.group()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.debug("JSON parse failed for raw_text: %s", text)
            raise ValueError(f"Invalid JSON response: {exc}") from exc
