"""Backfill missing OneBot private-message sender names before NA collects them."""

from nekro_agent.api.core import logger

from .matcher import install_matcher, remove_matcher
from .plugin import plugin

__all__ = ["plugin"]


@plugin.on_enabled()
async def register_private_sender_backfill() -> None:
    """Register the pre-core matcher when the plugin is enabled."""
    install_matcher()
    logger.info("OneBot 私聊昵称回填插件已注册")


@plugin.on_disabled()
async def unregister_private_sender_backfill() -> None:
    """Remove the matcher when the plugin is disabled."""
    remove_matcher()


@plugin.mount_cleanup_method()
async def cleanup_private_sender_backfill() -> None:
    """Remove the matcher when the plugin or process is unloaded."""
    remove_matcher()
