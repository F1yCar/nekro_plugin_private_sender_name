"""NoneBot matcher that repairs private sender names before NA's core matcher."""

from collections.abc import Mapping
from typing import Any

from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.adapters.onebot.v11.event import Sender
from nonebot.matcher import matchers

from nekro_agent.api.core import logger

from .plugin import plugin

_MATCHER_MARKER = "_nekro_private_sender_name_backfill"


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


async def backfill_private_sender(bot: Bot, event: MessageEvent) -> bool:
    """Backfill a private event sender name and report whether it changed."""
    if _text(getattr(event, "message_type", "")) != "private":
        return False

    user_id = int(event.user_id)
    sender = getattr(event, "sender", None)
    if sender is None:
        sender = Sender(user_id=user_id)
        event.sender = sender

    if _text(getattr(sender, "nickname", None)) or _text(getattr(sender, "card", None)):
        return False

    nickname: str | None = None
    try:
        info = await bot.get_stranger_info(user_id=user_id, no_cache=False)
        if isinstance(info, Mapping):
            nickname = _text(info.get("nickname")) or None
        else:
            nickname = _text(getattr(info, "nickname", None)) or None
    except Exception as exc:
        logger.debug(f"私聊昵称回填查询失败，user_id={user_id}: {exc}")

    sender.nickname = nickname or f"用户{user_id}"
    return True


def remove_matcher() -> int:
    """Remove all backfill matchers, including stale hot-reload instances."""
    removed = 0
    for priority, registered in list(matchers.items()):
        kept = []
        for matcher in registered:
            if getattr(matcher, _MATCHER_MARKER, False):
                removed += 1
            else:
                kept.append(matcher)
        if kept:
            matchers[priority] = kept
        else:
            del matchers[priority]
    return removed


def install_matcher() -> type:
    """Install exactly one priority-100, non-blocking backfill matcher."""
    remove_matcher()

    matcher = on_message(priority=100, block=False)
    setattr(matcher, _MATCHER_MARKER, True)

    @matcher.handle()
    async def _(bot: Bot, event: MessageEvent) -> None:
        if not plugin.is_enabled:
            return
        await backfill_private_sender(bot, event)

    return matcher
