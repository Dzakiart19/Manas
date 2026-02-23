from typing import List, Dict, Any, Optional
import httpx
from app.domain.external.llm import LLM
from app.core.config import get_settings
import logging
import asyncio
import json


logger = logging.getLogger(__name__)

class OpenAILLM(LLM):
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.api_key
        self._api_base = settings.api_base
        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        logger.info(f"Initialized OpenAI-compatible LLM with model: {self._model_name}, base: {self._api_base}")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    async def ask(self, messages: List[Dict[str, str]],
                tools: Optional[List[Dict[str, Any]]] = None,
                response_format: Optional[Dict[str, Any]] = None,
                tool_choice: Optional[str] = None) -> Dict[str, Any]:
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying API request (attempt {attempt + 1}/{max_retries + 1}) after {delay}s delay")
                    await asyncio.sleep(delay)

                payload = {
                    "model": self._model_name,
                    "messages": messages,
                    "temperature": self._temperature,
                    "max_tokens": self._max_tokens,
                }

                if tools:
                    payload["tools"] = tools
                if tool_choice:
                    payload["tool_choice"] = tool_choice
                if response_format:
                    payload["response_format"] = response_format

                headers = {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }

                logger.debug(f"Sending request to {self._api_base}, model: {self._model_name}, has_tools: {bool(tools)}, tool_choice: {tool_choice}, attempt: {attempt + 1}")

                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        self._api_base,
                        headers=headers,
                        json=payload,
                    )

                if response.status_code != 200:
                    error_text = response.text
                    error_msg = f"API returned status {response.status_code}: {error_text}"
                    logger.error(error_msg)
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: {error_msg}")
                    continue

                data = response.json()
                logger.debug(f"Response from API: {json.dumps(data, ensure_ascii=False)[:500]}")

                choices = None
                if "choices" in data and len(data["choices"]) > 0:
                    choices = data["choices"]
                elif "openai_compatible" in data and "choices" in data["openai_compatible"] and len(data["openai_compatible"]["choices"]) > 0:
                    choices = data["openai_compatible"]["choices"]

                if not choices:
                    error_msg = f"API returned invalid response (no choices) on attempt {attempt + 1}: {json.dumps(data, ensure_ascii=False)[:300]}"
                    logger.error(error_msg)
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: {error_msg}")
                    continue

                message = choices[0].get("message", {})
                result = {
                    "role": "assistant",
                    "content": message.get("content") or "",
                }

                tool_calls = message.get("tool_calls")
                if tool_calls:
                    result["tool_calls"] = tool_calls
                    if not message.get("content"):
                        result["content"] = ""

                return result

            except httpx.HTTPError as e:
                error_msg = f"HTTP error on attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise e
                continue
            except Exception as e:
                error_msg = f"Error calling API on attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise e
                continue
