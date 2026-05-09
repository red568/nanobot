"""
对不活跃的session进行自动压缩归档，保留最近的消息以供继续对话，并在下次访问时提供上次对话的总结和闲置时间提示。
"""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from loguru import logger
from nanobot.session.manager import Session, SessionManager

if TYPE_CHECKING:
    from nanobot.agent.memory import Consolidator


class AutoCompact:
    _RECENT_SUFFIX_MESSAGES = 8

    def __init__(self, sessions: SessionManager, consolidator: Consolidator,
                 session_ttl_minutes: int = 0):
        self.sessions = sessions
        self.consolidator = consolidator # 用于生成总结的组件，必须提供一个 archive(messages: list[dict]) -> str 的异步方法
        self._ttl = session_ttl_minutes # 会话闲置多长时间（分钟）后被认为过期需要压缩，0或负数表示永不过期
        self._archiving: set[str] = set() # 当前正在归档的session keys，避免重复归档和访问时的竞争条件
        self._summaries: dict[str, tuple[str, datetime]] = {} # 内存中的总结缓存，key为session key，value为(summary, last_active)，避免频繁访问磁盘和调用consolidator

    def _is_expired(self, ts: datetime | str | None,
                    now: datetime | None = None) -> bool:
        if self._ttl <= 0 or not ts:
            return False
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return ((now or datetime.now()) - ts).total_seconds() >= self._ttl * 60

    @staticmethod
    def _format_summary(text: str, last_active: datetime) -> str:
        idle_min = int((datetime.now() - last_active).total_seconds() / 60)
        return f"Inactive for {idle_min} minutes.\nPrevious conversation summary: {text}"

    def _split_unconsolidated(
        self, session: Session,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        切割历史记录，决定哪些消息需要归档（过旧）哪些需要保留（最近的几条）以支持继续对话。
        """
        tail = list(session.messages[session.last_consolidated:])
        if not tail:
            return [], []

        probe = Session(
            key=session.key,
            messages=tail.copy(),
            created_at=session.created_at,
            updated_at=session.updated_at,
            metadata={},
            last_consolidated=0,
        )
        probe.retain_recent_legal_suffix(self._RECENT_SUFFIX_MESSAGES)
        kept = probe.messages
        cut = len(tail) - len(kept)
        return tail[:cut], kept

    def check_expired(self, schedule_background: Callable[[Coroutine], None],
                      active_session_keys: Collection[str] = ()) -> None:
        """
        对外暴露的入口:负责不活跃sessions压缩的定时任务。
        遍历当前所有的会话，跳过正在活跃的（active_session_keys）和正在处理中的（_archiving）。
        发现超时的会话后，通过 schedule_background 将其丢入后台执行异步归档，避免阻塞主线程。
        """
        now = datetime.now()
        for info in self.sessions.list_sessions():
            key = info.get("key", "")
            if not key or key in self._archiving:
                continue
            if key in active_session_keys:
                continue
            if self._is_expired(info.get("updated_at"), now):
                self._archiving.add(key)
                schedule_background(self._archive(key))
    
    
    async def _archive(self, key: str) -> None:
        '''
        真正的归档逻辑：加载会话，切割消息，调用 consolidator 生成总结，更新会话并保存。
        '''
        try:
            self.sessions.invalidate(key)
            session = self.sessions.get_or_create(key)
            archive_msgs, kept_msgs = self._split_unconsolidated(session)
            # 这段代码在问：“如果在刚才的切割中，既没有需要归档的旧消息，也没有需要保留的新消息，该怎么办？”
            # 解法：把会话的“最后活跃时间”强行刷新为当前时间。
            # 什么时候会出现这种情况？
                # 纯空会话：用户新建了一个聊天（生成了 session key），但一句话都没发就跑了。
                # 已完全归档且无新进展：这个会话之前已经被 AutoCompact 压缩过了，之后用户再也没发过任何新消息。此时会话的尾部（tail）是空的。
            # 为什么要这么做？因为如果不这么做，这个会话就会一直被认为过期，每次 check_expired 都会反复尝试归档，造成不必要的资源浪费和日志噪音。
            if not archive_msgs and not kept_msgs:
                session.updated_at = datetime.now()
                self.sessions.save(session)
                return

            # 归档旧消息，生成总结，并更新会话状态
            last_active = session.updated_at
            summary = ""
            if archive_msgs:
                summary = await self.consolidator.archive(archive_msgs) or ""
            if summary and summary != "(nothing)":
                self._summaries[key] = (summary, last_active)
                session.metadata["_last_summary"] = {"text": summary, "last_active": last_active.isoformat()}
            session.messages = kept_msgs
            session.last_consolidated = 0
            session.updated_at = datetime.now()
            self.sessions.save(session)
            if archive_msgs:
                logger.info(
                    "Auto-compact: archived {} (archived={}, kept={}, summary={})",
                    key,
                    len(archive_msgs),
                    len(kept_msgs),
                    bool(summary),
                )
        except Exception:
            logger.exception("Auto-compact: failed for {}", key)
        finally:
            self._archiving.discard(key)

    def prepare_session(self, session: Session, key: str) -> tuple[Session, str | None]:
        """"
        会话唤醒逻辑。当非活跃用户突然又发来消息时调用。
        """
        if key in self._archiving or self._is_expired(session.updated_at):
            logger.info("Auto-compact: reloading session {} (archiving={})", key, key in self._archiving)
            session = self.sessions.get_or_create(key)
        # 它会检查内存或数据库元数据中是否有刚才生成的 _last_summary。
        # 如果有，它会调用 _format_summary 格式化一段文本（例如：“距离上次活跃已过去 30 分钟。先前的对话摘要：[摘要内容]”），并返回给系统，
        # 以便系统将这段话作为系统提示（System Prompt）塞给 AI。
        # 同时它会清理掉这些一次性的元数据。
        entry = self._summaries.pop(key, None)
        if entry:
            session.metadata.pop("_last_summary", None)
            return session, self._format_summary(entry[0], entry[1])
        if "_last_summary" in session.metadata:
            meta = session.metadata.pop("_last_summary")
            self.sessions.save(session)
            return session, self._format_summary(meta["text"], datetime.fromisoformat(meta["last_active"]))
        return session, None
