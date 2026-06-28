"""Tool gateway with retries and normalized tool results."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import sleep
from typing import Callable


ToolCallable = Callable[[dict], dict]


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    status: str
    output: dict
    attempts: int
    error: str | None = None


@dataclass
class ToolGateway:
    max_attempts: int = 2
    retry_delay_seconds: float = 0.0
    _tools: dict[str, ToolCallable] = field(default_factory=dict)

    def register(self, name: str, tool: ToolCallable) -> None:
        self._tools[name] = tool

    def call(self, name: str, payload: dict) -> ToolResult:
        if name not in self._tools:
            return ToolResult(
                tool_name=name,
                status="not_found",
                output={},
                attempts=0,
                error=f"Tool is not registered: {name}",
            )

        last_error: str | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return ToolResult(
                    tool_name=name,
                    status="ok",
                    output=self._tools[name](payload),
                    attempts=attempt,
                )
            except Exception as exc:  # pragma: no cover - tested through behavior
                last_error = str(exc)
                if self.retry_delay_seconds:
                    sleep(self.retry_delay_seconds)

        return ToolResult(
            tool_name=name,
            status="error",
            output={},
            attempts=self.max_attempts,
            error=last_error,
        )
