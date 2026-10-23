"""Isolated tests for the private sender-name backfill plugin."""

from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase

from nonebot.matcher import matchers

from nekro_plugin_private_sender_name.matcher import (
    _MATCHER_MARKER,
    backfill_private_sender,
    install_matcher,
    remove_matcher,
)
from nekro_plugin_private_sender_name.plugin import plugin


class FakeBot:
    def __init__(self, info=None, error=None):
        self.info = info or {}
        self.error = error
        self.calls = []

    async def get_stranger_info(self, *, user_id, no_cache):
        self.calls.append({"user_id": user_id, "no_cache": no_cache})
        if self.error:
            raise self.error
        return self.info


def private_event(nickname=None, card=None):
    return SimpleNamespace(
        message_type="private",
        user_id=3844905499,
        sender=SimpleNamespace(nickname=nickname, card=card),
    )


class BackfillTests(IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        if plugin.is_enabled:
            await plugin.disable()
        remove_matcher()

    async def test_missing_nickname_uses_stranger_info(self):
        event = private_event()
        bot = FakeBot(info={"nickname": "新好友"})

        changed = await backfill_private_sender(bot, event)

        self.assertTrue(changed)
        self.assertEqual(event.sender.nickname, "新好友")
        self.assertEqual(
            bot.calls,
            [{"user_id": 3844905499, "no_cache": False}],
        )

    async def test_lookup_failure_uses_user_id_fallback(self):
        event = private_event()
        bot = FakeBot(error=RuntimeError("gateway timeout"))

        changed = await backfill_private_sender(bot, event)

        self.assertTrue(changed)
        self.assertEqual(event.sender.nickname, "用户3844905499")

    async def test_existing_nickname_does_not_call_onebot(self):
        event = private_event(nickname="已有昵称")
        bot = FakeBot(info={"nickname": "不应使用"})

        changed = await backfill_private_sender(bot, event)

        self.assertFalse(changed)
        self.assertEqual(event.sender.nickname, "已有昵称")
        self.assertEqual(bot.calls, [])

    async def test_group_message_is_ignored(self):
        event = private_event()
        event.message_type = "group"
        bot = FakeBot(info={"nickname": "群成员"})

        changed = await backfill_private_sender(bot, event)

        self.assertFalse(changed)
        self.assertEqual(bot.calls, [])

    async def test_plugin_enable_disable_controls_matcher_lifecycle(self):
        await plugin.enable()
        enabled_matchers = [
            matcher
            for registered in matchers.values()
            for matcher in registered
            if getattr(matcher, _MATCHER_MARKER, False)
        ]
        self.assertEqual(len(enabled_matchers), 1)

        await plugin.disable()
        disabled_matchers = [
            matcher
            for registered in matchers.values()
            for matcher in registered
            if getattr(matcher, _MATCHER_MARKER, False)
        ]
        self.assertEqual(disabled_matchers, [])


class MatcherLifecycleTests(TestCase):
    def tearDown(self):
        remove_matcher()

    def test_install_is_idempotent_and_uses_priority_100(self):
        first = install_matcher()
        second = install_matcher()

        found = [
            matcher
            for registered in matchers.values()
            for matcher in registered
            if getattr(matcher, _MATCHER_MARKER, False)
        ]
        self.assertEqual(found, [second])
        self.assertEqual(second.priority, 100)
        self.assertFalse(second.block)
        self.assertIsNot(first, second)

    def test_remove_matcher(self):
        install_matcher()
        self.assertEqual(remove_matcher(), 1)
        self.assertEqual(remove_matcher(), 0)
