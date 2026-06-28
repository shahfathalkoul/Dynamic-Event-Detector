"""Provider-agnostic LLM gateway.

Supports OpenAI, Anthropic, and local models behind a unified interface
with structured output enforcement, token counting, and cost tracking.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""
    content: str = ""
    structured_output: dict | None = None
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0


# Token costs per 1M tokens (input/output)
MODEL_COSTS = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-haiku-3": (0.25, 1.25),
}


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = api_key
        self._client = None

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        response_model: Type[BaseModel] | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Parameters
        ----------
        prompt:
            The user prompt / task description.
        system_prompt:
            System-level instructions.
        response_model:
            If provided, enforce structured JSON output matching this
            Pydantic model schema.
        """
        start = time.perf_counter()

        try:
            if self.model.startswith("claude"):
                result = self._call_anthropic(prompt, system_prompt, response_model)
            else:
                result = self._call_openai(prompt, system_prompt, response_model)
        except Exception as exc:
            logger.error("LLM call failed (%s): %s", self.model, exc)
            return LLMResponse(
                content=f"Error: {exc}",
                model=self.model,
                latency_ms=int((time.perf_counter() - start) * 1000),
            )

        result.latency_ms = int((time.perf_counter() - start) * 1000)
        result.estimated_cost_usd = self._estimate_cost(
            result.prompt_tokens, result.completion_tokens
        )
        return result

    def _call_openai(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Type[BaseModel] | None,
    ) -> LLMResponse:
        """Call OpenAI-compatible API."""
        from openai import OpenAI

        api_key = self._api_key or os.environ.get("OPENAI_API_KEY", "")
        client = OpenAI(api_key=api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if response_model:
            # Use JSON mode with schema
            kwargs["response_format"] = {"type": "json_object"}
            schema_hint = json.dumps(response_model.model_json_schema(), indent=2)
            messages[-1]["content"] += f"\n\nRespond with valid JSON matching this schema:\n{schema_hint}"

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        content = choice.message.content or ""

        structured = None
        if response_model and content:
            try:
                structured = json.loads(content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse structured output from OpenAI")

        return LLMResponse(
            content=content,
            structured_output=structured,
            model=self.model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

    def _call_anthropic(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Type[BaseModel] | None,
    ) -> LLMResponse:
        """Call Anthropic Claude API."""
        import anthropic

        api_key = self._api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=api_key)

        user_content = prompt
        if response_model:
            schema_hint = json.dumps(response_model.model_json_schema(), indent=2)
            user_content += f"\n\nRespond with valid JSON matching this schema:\n{schema_hint}"

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or "You are a helpful assistant.",
            messages=[{"role": "user", "content": user_content}],
            temperature=self.temperature,
        )

        content = response.content[0].text if response.content else ""
        structured = None
        if response_model and content:
            try:
                # Extract JSON from possible markdown fences
                json_str = content
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                structured = json.loads(json_str.strip())
            except (json.JSONDecodeError, IndexError):
                logger.warning("Failed to parse structured output from Anthropic")

        return LLMResponse(
            content=content,
            structured_output=structured,
            model=self.model,
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            total_tokens=(
                (response.usage.input_tokens + response.usage.output_tokens)
                if response.usage else 0
            ),
        )

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost in USD based on token counts."""
        costs = MODEL_COSTS.get(self.model, (0.0, 0.0))
        input_cost = (prompt_tokens / 1_000_000) * costs[0]
        output_cost = (completion_tokens / 1_000_000) * costs[1]
        return round(input_cost + output_cost, 6)
