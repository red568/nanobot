"""Shared lifecycle hook primitives for agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from nanobot.providers.base import LLMResponse, ToolCallRequest


@dataclass(slots=True)
class AgentHookContext:
    """钩子函数的上下文，包含当前迭代的信息和状态"""

    iteration: int
    messages: list[dict[str, Any]]
    response: LLMResponse | None = None
    usage: dict[str, int] = field(default_factory=dict)
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    tool_results: list[Any] = field(default_factory=list)
    tool_events: list[dict[str, str]] = field(default_factory=list)
    streamed_content: bool = False
    final_content: str | None = None
    stop_reason: str | None = None
    error: str | None = None


class AgentHook:
    """定义钩子函数的接口，允许用户在代理运行的不同阶段插入自定义逻辑，全生命周期的函数调用"""

    def __init__(self, reraise: bool = False) -> None:
        # 如果 reraise 为 True，则在钩子函数中发生的异常会被重新抛出，可能会导致代理循环崩溃；
        # 如果为 False（默认），则会捕获并记录异常，允许代理继续运行。
        # 保证了健壮性：用户自定义的钩子函数可能会有错误，但不应该影响整个代理的运行。
        self._reraise = reraise

    def wants_streaming(self) -> bool:
        return False

    # 在每一轮大模型调用（LLM Call）开始前触发，可用于注入 Context 或清除旧状态。
    async def before_iteration(self, context: AgentHookContext) -> None:
        pass

    # 仅当 wants_streaming 返回 True 时有效，用于实时获取大模型输出的片段。
    # delta 是增量内容，context 中的 streamed_content 标志会被设置为 True。
    async def on_stream(self, context: AgentHookContext, delta: str) -> None:
        pass

    # 在流式输出结束时触发，resuming 表示是否因为工具调用而暂停后续流式输出。
    async def on_stream_end(self, context: AgentHookContext, *, resuming: bool) -> None:
        pass

    # 在执行工具调用前触发，此时 context 中的 tool_calls 已经准备就绪，但工具结果尚未返回。
    # 可以用于UI上显示即将执行的工具调用，或修改工具调用请求（比如正在进行工具调用）。
    # 或者人工干预（比如正在进行工具调用）以决定是否继续执行工具调用。
    async def before_execute_tools(self, context: AgentHookContext) -> None:
        pass

    # 在每一轮大模型调用结束后触发，此时 context 中的 response、usage、tool_results 等信息已经准备就绪。
    async def after_iteration(self, context: AgentHookContext) -> None:
        pass

    # 在最终内容确定前触发，可用于修改或增强最终输出内容。
    # 可以进行敏感词的过滤，或者根据工具调用结果动态生成最终内容。
    def finalize_content(self, context: AgentHookContext, content: str | None) -> str | None:
        return content


class CompositeHook(AgentHook):
    """
    允许将多个 AgentHook 组合成一个整体，依次调用每个子钩子函数，确保每个钩子函数的异常不会影响其他钩子函数的执行。 
    核心作用：将多个独立的 Hook（钩子/拦截器）打包成一个统一的 Hook。 
    当 Agent 触发某个事件时，只需要调用这个 CompositeHook，它就会自动将事件分发（扇出/Fan-out）给它所包含的所有子 Hook。

    """

    __slots__ = ("_hooks",)

    # hooks 参数是一个 AgentHook 实例的列表，CompositeHook 会在其生命周期内依次调用这些实例的钩子函数。
    def __init__(self, hooks: list[AgentHook]) -> None:
        super().__init__()
        self._hooks = list(hooks)

    def wants_streaming(self) -> bool:
        return any(h.wants_streaming() for h in self._hooks)

    # 这里通过判断_reraise的属性来进行安全的方法调用
    async def _for_each_hook_safe(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        for h in self._hooks:
            if getattr(h, "_reraise", False):
                await getattr(h, method_name)(*args, **kwargs)
                continue

            try:
                await getattr(h, method_name)(*args, **kwargs)
            except Exception:
                logger.exception("AgentHook.{} error in {}", method_name, type(h).__name__)

    async def before_iteration(self, context: AgentHookContext) -> None:
        await self._for_each_hook_safe("before_iteration", context)

    async def on_stream(self, context: AgentHookContext, delta: str) -> None:
        await self._for_each_hook_safe("on_stream", context, delta)

    async def on_stream_end(self, context: AgentHookContext, *, resuming: bool) -> None:
        await self._for_each_hook_safe("on_stream_end", context, resuming=resuming)

    async def before_execute_tools(self, context: AgentHookContext) -> None:
        await self._for_each_hook_safe("before_execute_tools", context)

    async def after_iteration(self, context: AgentHookContext) -> None:
        await self._for_each_hook_safe("after_iteration", context)

    def finalize_content(self, context: AgentHookContext, content: str | None) -> str | None:
        for h in self._hooks:
            content = h.finalize_content(context, content)
        return content


class SDKCaptureHook(AgentHook):
    """Record tool names and the final message list for ``RunResult``.

    The runner mutates ``context.messages`` in place across iterations, so the
    snapshot is refreshed on every ``after_iteration`` call; the last call
    reflects the end-of-turn state the SDK caller cares about.
    """

    def __init__(self) -> None:
        super().__init__()
        self.tools_used: list[str] = []
        self.messages: list[dict[str, Any]] = []

    async def after_iteration(self, context: AgentHookContext) -> None:
        for call in context.tool_calls:
            self.tools_used.append(call.name)
        self.messages = list(context.messages)
