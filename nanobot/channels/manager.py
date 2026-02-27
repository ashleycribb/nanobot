"""Channel manager for coordinating chat channels."""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import Config


class ChannelManager:
    """
    Manages chat channels and coordinates message routing.
    
    Responsibilities:
    - Initialize enabled channels (Telegram, WhatsApp, etc.)
    - Start/stop channels
    - Route outbound messages
    """
    
    def __init__(self, config: Config, bus: MessageBus):
        self.config = config
        self.bus = bus
        self.channels: dict[str, BaseChannel] = {}
        self._dispatch_task: asyncio.Task | None = None
        self._active_tasks: dict[str, asyncio.Task] = {}
        
        self._init_channels()
    
    def _init_channels(self) -> None:
        """Initialize channels based on config."""
        
        # Helper to register channel
        def _register(name: str, channel: BaseChannel):
            self.channels[name] = channel
            self.bus.subscribe_outbound(name, channel.send)
            logger.info(f"{name.capitalize()} channel enabled")

        # Telegram channel
        if self.config.channels.telegram.enabled:
            try:
                from nanobot.channels.telegram import TelegramChannel
                channel = TelegramChannel(
                    self.config.channels.telegram,
                    self.bus,
                    groq_api_key=self.config.providers.groq.api_key,
                )
                _register("telegram", channel)
            except ImportError as e:
                logger.warning(f"Telegram channel not available: {e}")
        
        # WhatsApp channel
        if self.config.channels.whatsapp.enabled:
            try:
                from nanobot.channels.whatsapp import WhatsAppChannel
                channel = WhatsAppChannel(
                    self.config.channels.whatsapp, self.bus
                )
                _register("whatsapp", channel)
            except ImportError as e:
                logger.warning(f"WhatsApp channel not available: {e}")

        # Discord channel
        if self.config.channels.discord.enabled:
            try:
                from nanobot.channels.discord import DiscordChannel
                channel = DiscordChannel(
                    self.config.channels.discord, self.bus
                )
                _register("discord", channel)
            except ImportError as e:
                logger.warning(f"Discord channel not available: {e}")
        
        # Feishu channel
        if self.config.channels.feishu.enabled:
            try:
                from nanobot.channels.feishu import FeishuChannel
                channel = FeishuChannel(
                    self.config.channels.feishu, self.bus
                )
                _register("feishu", channel)
            except ImportError as e:
                logger.warning(f"Feishu channel not available: {e}")

        # Mochat channel
        if self.config.channels.mochat.enabled:
            try:
                from nanobot.channels.mochat import MochatChannel
                channel = MochatChannel(
                    self.config.channels.mochat, self.bus
                )
                _register("mochat", channel)
            except ImportError as e:
                logger.warning(f"Mochat channel not available: {e}")

        # DingTalk channel
        if self.config.channels.dingtalk.enabled:
            try:
                from nanobot.channels.dingtalk import DingTalkChannel
                channel = DingTalkChannel(
                    self.config.channels.dingtalk, self.bus
                )
                _register("dingtalk", channel)
            except ImportError as e:
                logger.warning(f"DingTalk channel not available: {e}")

        # Email channel
        if self.config.channels.email.enabled:
            try:
                from nanobot.channels.email import EmailChannel
                channel = EmailChannel(
                    self.config.channels.email, self.bus
                )
                _register("email", channel)
            except ImportError as e:
                logger.warning(f"Email channel not available: {e}")

        # Slack channel
        if self.config.channels.slack.enabled:
            try:
                from nanobot.channels.slack import SlackChannel
                channel = SlackChannel(
                    self.config.channels.slack, self.bus
                )
                _register("slack", channel)
            except ImportError as e:
                logger.warning(f"Slack channel not available: {e}")

        # QQ channel
        if self.config.channels.qq.enabled:
            try:
                from nanobot.channels.qq import QQChannel
                channel = QQChannel(
                    self.config.channels.qq,
                    self.bus,
                )
                _register("qq", channel)
            except ImportError as e:
                logger.warning(f"QQ channel not available: {e}")
    
    async def _start_channel(self, name: str, channel: BaseChannel) -> None:
        """Start a channel and log any exceptions."""
        try:
            await channel.start()
        except Exception as e:
            logger.error(f"Failed to start channel {name}: {e}")

    async def start_all(self) -> None:
        """Start all channels and the outbound dispatcher."""
        if not self.channels:
            logger.warning("No channels enabled")
            return
        
        # Start outbound dispatcher
        self._dispatch_task = asyncio.create_task(self.bus.dispatch_outbound())
        logger.info("Outbound dispatcher started")
        
        # Start channels
        tasks = []
        for name, channel in self.channels.items():
            logger.info(f"Starting {name} channel...")
            tasks.append(asyncio.create_task(self._start_channel(name, channel)))
        
        # Wait for all to complete (they should run forever)
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_all(self) -> None:
        """Stop all channels and the dispatcher."""
        logger.info("Stopping all channels...")
        
        # Stop dispatcher
        self.bus.stop()
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active message tasks
        for task in self._active_tasks.values():
            task.cancel()
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks.values(), return_exceptions=True)
        self._active_tasks.clear()

        # Stop all channels
        for name, channel in self.channels.items():
            try:
                await channel.stop()
                logger.info(f"Stopped {name} channel")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")


    async def _process_message(
        self,
        previous_task: asyncio.Task | None,
        channel: BaseChannel,
        msg: OutboundMessage
    ) -> None:
        """Process message sequentially for a specific chat."""
        if previous_task:
            try:
                await previous_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Previous message task failed: {e}")

        try:
            await channel.send(msg)
        except Exception as e:
            logger.error(f"Error sending to {msg.channel}: {e}")

    async def _dispatch_outbound(self) -> None:
        """Dispatch outbound messages to the appropriate channel."""
        logger.info("Outbound dispatcher started")
        
        while True:
            try:
                msg = await asyncio.wait_for(
                    self.bus.consume_outbound(),
                    timeout=1.0
                )
                
                channel = self.channels.get(msg.channel)
                if channel:
                    # Create a unique key for channel+chat
                    key = f"{msg.channel}:{msg.chat_id}"
                    previous_task = self._active_tasks.get(key)

                    # Create new task chaining off previous one
                    task = asyncio.create_task(
                        self._process_message(previous_task, channel, msg)
                    )

                    self._active_tasks[key] = task

                    def done_callback(t: asyncio.Task, k: str = key) -> None:
                        # Only cleanup if this is still the active task for the key
                        if self._active_tasks.get(k) == t:
                            del self._active_tasks[k]

                    task.add_done_callback(done_callback)

                else:
                    logger.warning(f"Unknown channel: {msg.channel}")
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    def get_channel(self, name: str) -> BaseChannel | None:
        """Get a channel by name."""
        return self.channels.get(name)
    
    def get_status(self) -> dict[str, Any]:
        """Get status of all channels."""
        return {
            name: {
                "enabled": True,
                "running": channel.is_running
            }
            for name, channel in self.channels.items()
        }
    
    @property
    def enabled_channels(self) -> list[str]:
        """Get list of enabled channel names."""
        return list(self.channels.keys())
