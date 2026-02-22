from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic
from app.domain.external.llm import LLM
from app.core.config import get_settings
import logging
import asyncio
import json


logger = logging.getLogger(__name__)

class OpenAILLM(LLM):
    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(
            api_key=settings.api_key,
        )
        
        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        logger.info(f"Initialized Anthropic LLM with model: {self._model_name}")
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def temperature(self) -> float:
        return self._temperature
    
    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    def _convert_tools_to_anthropic(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function" and "function" in tool:
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}})
                })
            else:
                anthropic_tools.append(tool)
        return anthropic_tools

    def _convert_messages_to_anthropic(self, messages: List[Dict[str, Any]]) -> tuple:
        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role")
            
            if role == "system":
                system_prompt = msg.get("content", "")
                continue
            
            if role == "assistant":
                content_blocks = []
                text_content = msg.get("content")
                if text_content:
                    content_blocks.append({"type": "text", "text": text_content})
                
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    for tc in tool_calls:
                        func = tc.get("function", {})
                        args = func.get("arguments", "{}")
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except (json.JSONDecodeError, TypeError):
                                args = {}
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": func.get("name", ""),
                            "input": args
                        })
                
                if not content_blocks:
                    content_blocks.append({"type": "text", "text": ""})
                
                anthropic_messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })
                continue
            
            if role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                content = msg.get("content", "")
                
                if anthropic_messages and anthropic_messages[-1]["role"] == "user":
                    last_content = anthropic_messages[-1]["content"]
                    if isinstance(last_content, list):
                        last_content.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call_id,
                            "content": content
                        })
                    else:
                        anthropic_messages[-1]["content"] = [
                            {"type": "text", "text": last_content} if last_content else {"type": "text", "text": ""},
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call_id,
                                "content": content
                            }
                        ]
                else:
                    anthropic_messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_call_id,
                            "content": content
                        }]
                    })
                continue
            
            if role == "user":
                content = msg.get("content", "")
                anthropic_messages.append({
                    "role": "user",
                    "content": content
                })
                continue

        merged = []
        for msg in anthropic_messages:
            if merged and merged[-1]["role"] == msg["role"]:
                prev_content = merged[-1]["content"]
                curr_content = msg["content"]
                
                if isinstance(prev_content, str):
                    prev_content = [{"type": "text", "text": prev_content}]
                if isinstance(curr_content, str):
                    curr_content = [{"type": "text", "text": curr_content}]
                if not isinstance(prev_content, list):
                    prev_content = [prev_content]
                if not isinstance(curr_content, list):
                    curr_content = [curr_content]
                
                merged[-1]["content"] = prev_content + curr_content
            else:
                merged.append(msg)
        
        return system_prompt, merged

    def _convert_response_to_openai(self, response) -> Dict[str, Any]:
        text_parts = []
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input) if isinstance(block.input, dict) else str(block.input)
                    }
                })
        
        result = {
            "role": "assistant",
            "content": None,
        }
        
        if tool_calls:
            result["tool_calls"] = tool_calls
            result["content"] = ""
        else:
            result["content"] = "\n".join(text_parts) if text_parts else ""
        
        return result
    
    async def ask(self, messages: List[Dict[str, str]],
                tools: Optional[List[Dict[str, Any]]] = None,
                response_format: Optional[Dict[str, Any]] = None,
                tool_choice: Optional[str] = None) -> Dict[str, Any]:
        max_retries = 3
        base_delay = 1.0  

        for attempt in range(max_retries + 1):
            response = None
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying Anthropic API request (attempt {attempt + 1}/{max_retries + 1}) after {delay}s delay")
                    await asyncio.sleep(delay)

                system_prompt, anthropic_messages = self._convert_messages_to_anthropic(messages)

                kwargs = {
                    "model": self._model_name,
                    "temperature": self._temperature,
                    "max_tokens": self._max_tokens,
                    "messages": anthropic_messages,
                }

                if system_prompt:
                    kwargs["system"] = system_prompt

                if tools:
                    anthropic_tools = self._convert_tools_to_anthropic(tools)
                    kwargs["tools"] = anthropic_tools
                    
                    if tool_choice:
                        if tool_choice == "none":
                            kwargs["tool_choice"] = {"type": "none"}
                        elif tool_choice == "auto":
                            kwargs["tool_choice"] = {"type": "auto"}
                        elif tool_choice == "required":
                            kwargs["tool_choice"] = {"type": "any"}
                        else:
                            kwargs["tool_choice"] = {"type": "tool", "name": tool_choice}

                logger.debug(f"Sending request to Anthropic, model: {self._model_name}, has_tools: {bool(tools)}, tool_choice: {tool_choice}, attempt: {attempt + 1}")
                response = await self.client.messages.create(**kwargs)

                logger.debug(f"Response from Anthropic: stop_reason={response.stop_reason}, content_blocks={len(response.content)}")

                if not response or not response.content:
                    error_msg = f"Anthropic API returned invalid response (no content) on attempt {attempt + 1}"
                    logger.error(error_msg)
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: {error_msg}")
                    continue

                return self._convert_response_to_openai(response)

            except Exception as e:
                error_msg = f"Error calling Anthropic API on attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise e
                continue
