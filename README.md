# SnowLuma + Nekro Agent 私聊拒收修复

这个插件主要解决 SnowLuma（SL）搭配 Nekro Agent（NA）时，SL 输出的 OneBot
私聊消息字段不标准、不完整，导致 NA 拒收的问题。

当前表现是新好友或陌生人的私聊事件缺少 `sender.nickname`，而私聊
`sender.card` 也为空，触发 NA 核心的 `assert sender_name`，消息在进入
`collect_message` 前被丢弃。插件不改 SnowLuma，而是在 NA 接收侧回填昵称。

插件注册一个 `priority=100`、`block=False` 的 `on_message` matcher。NA 核心消息
matcher 使用 `priority=99999`，因此昵称会在核心的 `assert sender_name` 和
`get_user_name` 之前写入事件。

回填顺序：

1. 事件已有 `nickname` 或 `card` 时保持原值。
2. 私聊昵称为空时调用 `get_stranger_info(no_cache=False)`。
3. 查询失败时使用 `用户<QQ号>`。

插件禁用、热重载和进程清理时会移除 matcher；带专属标记的旧 matcher 也会在重新
注册前清除，避免重复执行。

升级 Nekro Agent 后需复核核心 OneBot 消息 matcher 的优先级仍高于 `100`。
