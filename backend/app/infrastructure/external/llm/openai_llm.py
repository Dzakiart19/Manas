from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.domain.external.llm import LLM
from app.core.config import get_settings
import logging
import asyncio
import time


logger = logging.getLogger(__name__)

class OpenAILLM(LLM):
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.api_base
        )
        
        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        logger.info(f"Initialized OpenAI LLM with model: {self._model_name}")
    
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
        """Send chat request to OpenAI API with retry mechanism"""
        max_retries = 3
        base_delay = 1.0  

        for attempt in range(max_retries + 1):
            response = None
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying OpenAI API request (attempt {attempt + 1}/{max_retries + 1}) after {delay}s delay")
                    await asyncio.sleep(delay)

                kwargs = {
                    "model": self._model_name,
                    "temperature": self._temperature,
                    "max_tokens": self._max_tokens,
                    "messages": messages,
                }

                if tools:
                    kwargs["tools"] = tools
                    kwargs["parallel_tool_calls"] = False
                    if tool_choice and isinstance(tool_choice, str):
                        kwargs["tool_choice"] = tool_choice
                
                if response_format and not tools:
                    kwargs["response_format"] = response_format

                logger.debug(f"Sending request to LLM, model: {self._model_name}, has_tools: {bool(tools)}, attempt: {attempt + 1}")
                response = await self.client.chat.completions.create(**kwargs)

                logger.debug(f"Response from LLM: {response.model_dump()}")

                
                if not response or not response.choices:
                    error_msg = f"LLM API returned invalid response (no choices) on attempt {attempt + 1}"
                    logger.error(error_msg)
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: {error_msg}")
                    continue

                return response.choices[0].message.model_dump()

            except Exception as e:
                error_msg = f"Error calling LLM API on attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise e
                continue

