"""Async message queue for decoupled channel-agent communication."""

import asyncio
from typing import Callable, Awaitable

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """
    Async message bus that decouples chat channels from the agent core.
    
    Channels push messages to the inbound queue, and the agent processes
    them and pushes responses to the outbound queue.
    """
    
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        self._outbound_subscribers: dict[str, list[Callable[[OutboundMessage], Awaitable[None]]]] = {}
        # Map channel name -> Queue of messages for that channel
        self._channel_queues: dict[str, asyncio.Queue[OutboundMessage]] = {}
        # Map channel name -> Worker task processing that channel's queue
        self._channel_tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._dispatch_task: asyncio.Task | None = None
    
    async def publish_inbound(self, msg: InboundMessage) -> None:
        """Publish a message from a channel to the agent."""
        await self.inbound.put(msg)
    
    async def consume_inbound(self) -> InboundMessage:
        """Consume the next inbound message (blocks until available)."""
        return await self.inbound.get()
    
    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """Publish a response from the agent to channels."""
        await self.outbound.put(msg)
    
    async def consume_outbound(self) -> OutboundMessage:
        """Consume the next outbound message (blocks until available)."""
        return await self.outbound.get()
    
    def subscribe_outbound(
        self, 
        channel: str, 
        callback: Callable[[OutboundMessage], Awaitable[None]]
    ) -> None:
        """Subscribe to outbound messages for a specific channel."""
        if channel not in self._outbound_subscribers:
            self._outbound_subscribers[channel] = []
        self._outbound_subscribers[channel].append(callback)
    
    async def _process_channel_queue(self, channel: str) -> None:
        """
        Worker that processes messages for a single channel sequentially.
        This ensures ordering within a channel while allowing concurrency across channels.
        """
        queue = self._channel_queues.get(channel)
        if not queue:
            return

        while self._running:
            try:
                # Wait for next message
                # Use a small timeout or just get to allow cancellation check loop
                # Since get() is cancellable, simple await is fine.
                msg = await queue.get()

                # Process all subscribers for this channel
                subscribers = self._outbound_subscribers.get(msg.channel, [])
                for callback in subscribers:
                    try:
                        await callback(msg)
                    except Exception as e:
                        logger.error(f"Error dispatching to {msg.channel}: {e}")

                queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in channel worker {channel}: {e}")

    async def dispatch_outbound(self) -> None:
        """
        Dispatch outbound messages to subscribed channels.
        Run this as a background task.
        """
        self._running = True
        self._dispatch_task = asyncio.current_task()

        while self._running:
            try:
                # Get next message from main outbound queue
                msg = await asyncio.wait_for(self.outbound.get(), timeout=1.0)

                channel = msg.channel

                # Ensure we have a queue and worker for this channel
                if channel not in self._channel_queues:
                    self._channel_queues[channel] = asyncio.Queue()

                if channel not in self._channel_tasks or self._channel_tasks[channel].done():
                    self._channel_tasks[channel] = asyncio.create_task(
                        self._process_channel_queue(channel)
                    )

                # Push to specific channel queue
                await self._channel_queues[channel].put(msg)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main dispatcher: {e}")
                await asyncio.sleep(0.1) # Prevent tight loop on error
    
    def stop(self) -> None:
        """Stop the dispatcher loop."""
        self._running = False

        # Cancel main dispatcher if it's not the caller (to avoid self-cancellation issues if awaited)
        if self._dispatch_task and not self._dispatch_task.done():
            # If we are calling stop from within the task, don't cancel self
            if asyncio.current_task() != self._dispatch_task:
                self._dispatch_task.cancel()

        # Cancel all channel workers
        for task in self._channel_tasks.values():
            if not task.done():
                task.cancel()

        self._channel_tasks.clear()
        self._channel_queues.clear()
    
    @property
    def inbound_size(self) -> int:
        """Number of pending inbound messages."""
        return self.inbound.qsize()
    
    @property
    def outbound_size(self) -> int:
        """Number of pending outbound messages."""
        return self.outbound.qsize()
