"""Gateway application entry point."""

import asyncio

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.config.loader import get_data_dir
from nanobot.config.schema import Config
from nanobot.providers.base import LLMProvider
from nanobot.agent.loop import AgentLoop
from nanobot.channels.manager import ChannelManager
from nanobot.session.manager import SessionManager
from nanobot.cron.service import CronService
from nanobot.cron.types import CronJob
from nanobot.heartbeat.service import HeartbeatService


class GatewayApp:
    """
    The main Gateway application.

    Initializes and manages all services:
    - AgentLoop
    - ChannelManager
    - CronService
    - HeartbeatService
    """

    def __init__(
        self,
        config: Config,
        provider: LLMProvider,
        bus: MessageBus | None = None,
    ):
        self.config = config
        self.provider = provider
        self.bus = bus or MessageBus()

        # Initialize components
        self.session_manager = SessionManager(config.workspace_path)

        cron_store_path = get_data_dir() / "cron" / "jobs.json"
        self.cron = CronService(cron_store_path)

        self.agent = AgentLoop(
            bus=self.bus,
            provider=self.provider,
            workspace=self.config.workspace_path,
            model=self.config.agents.defaults.model,
            temperature=self.config.agents.defaults.temperature,
            max_tokens=self.config.agents.defaults.max_tokens,
            max_iterations=self.config.agents.defaults.max_tool_iterations,
            memory_window=self.config.agents.defaults.memory_window,
            brave_api_key=self.config.tools.web.search.api_key or None,
            exec_config=self.config.tools.exec,
            cron_service=self.cron,
            restrict_to_workspace=self.config.tools.restrict_to_workspace,
            session_manager=self.session_manager,
            mcp_servers=self.config.tools.mcp_servers,
        )

        self._setup_cron()

        self.heartbeat = HeartbeatService(
            workspace=self.config.workspace_path,
            on_heartbeat=self._on_heartbeat,
            interval_s=30 * 60,  # 30 minutes
            enabled=True
        )

        self.channels = ChannelManager(self.config, self.bus)

    def _setup_cron(self) -> None:
        """Configure cron job callback."""
        async def on_cron_job(job: CronJob) -> str | None:
            """Execute a cron job through the agent."""
            response = await self.agent.process_direct(
                job.payload.message,
                session_key=f"cron:{job.id}",
                channel=job.payload.channel or "cli",
                chat_id=job.payload.to or "direct",
            )
            if job.payload.deliver and job.payload.to:
                await self.bus.publish_outbound(OutboundMessage(
                    channel=job.payload.channel or "cli",
                    chat_id=job.payload.to,
                    content=response or ""
                ))
            return response
        self.cron.on_job = on_cron_job

    async def _on_heartbeat(self, prompt: str) -> str:
        """Execute heartbeat through the agent."""
        return await self.agent.process_direct(prompt, session_key="heartbeat")

    async def run(self) -> None:
        """Start all services and run the main loop."""
        await self.cron.start()
        await self.heartbeat.start()

        # Run agent and channels concurrently
        await asyncio.gather(
            self.agent.run(),
            self.channels.start_all(),
        )

    async def stop(self) -> None:
        """Stop all services."""
        await self.agent.close_mcp()
        self.heartbeat.stop()
        self.cron.stop()
        self.agent.stop()
        await self.channels.stop_all()
