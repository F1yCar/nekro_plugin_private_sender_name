"""Plugin metadata."""

from nekro_agent.api.plugin import NekroPlugin

plugin = NekroPlugin(
    name="OneBot 私聊昵称回填",
    module_name="nekro_plugin_private_sender_name",
    description="在 NA 核心消息 matcher 之前回填 OneBot 私聊缺失的发送者昵称。",
    version="0.1.0",
    author="F1yCar",
    url="https://github.com/F1yCar/nekro_plugin_private_sender_name",
    support_adapter=["onebot_v11"],
)
