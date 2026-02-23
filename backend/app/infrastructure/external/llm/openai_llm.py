from typing import List, Dict, Any, Optional
import httpx
from app.domain.external.llm import LLM
from app.core.config import get_settings
import logging
import asyncio
import json


logger = logging.getLogger(__name__)

RATE_LIMIT_KEYWORDS = ["限流", "rate limit", "too many requests", "请求过多"]

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

    def _is_rate_limited(self, data: dict) -> bool:
        content = ""
        if "openai_compatible" in data:
            choices = data["openai_compatible"].get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
        elif "choices" in data:
            choices = data["choices"]
            if choices:
                content = choices[0].get("message", {}).get("content", "")
        if not content:
            text_blocks = data.get("content", [])
            if isinstance(text_blocks, list):
                for block in text_blocks:
                    if isinstance(block, dict) and block.get("type") == "text":
                        content += block.get("text", "")
        
        for kw in RATE_LIMIT_KEYWORDS:
            if kw in content:
                return True
        return False

    async def ask(self, messages: List[Dict[str, str]],
                tools: Optional[List[Dict[str, Any]]] = None,
                response_format: Optional[Dict[str, Any]] = None,
                tool_choice: Optional[str] = None) -> Dict[str, Any]:
        max_retries = 5
        base_delay = 30.0

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    if delay > 120:
                        delay = 120
                    logger.info(f"Retrying API request (attempt {attempt + 1}/{max_retries + 1}) after {delay}s delay")
                    await asyncio.sleep(delay)

                payload = {
                    "model": self._model_name,
                    "messages": messages,
                    "temperature": self._temperature,
                    "max_tokens": self._max_tokens,
                    "stream": False,
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
                    if response.status_code == 429:
                        logger.warning("Rate limited by API (HTTP 429), waiting before retry...")
                        if attempt < max_retries:
                            continue
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: {error_msg}")
                    continue

                raw_text = response.text
                if not raw_text or not raw_text.strip():
                    logger.warning(f"API returned empty body on attempt {attempt + 1}")
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: empty response body")
                    continue

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.warning(f"API returned non-JSON on attempt {attempt + 1}: {raw_text[:200]}")
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: non-JSON response")
                    continue

                logger.debug(f"Response from API: {json.dumps(data, ensure_ascii=False)[:500]}")

                if self._is_rate_limited(data):
                    logger.warning(f"Rate limited by API on attempt {attempt + 1}, waiting before retry...")
                    if attempt == max_retries:
                        raise ValueError("API rate limit exceeded. Please try again later.")
                    continue

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
