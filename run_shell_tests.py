import sys
import asyncio
import importlib.util

# We want to load `nanobot.agent.tools.shell` directly without triggering `nanobot.agent.__init__.py`
# which imports all the broken files.

spec = importlib.util.spec_from_file_location("nanobot.agent.tools.shell", "nanobot/agent/tools/shell.py")
shell_module = importlib.util.module_from_spec(spec)
sys.modules["nanobot.agent.tools.shell"] = shell_module

# We also need to mock `nanobot.agent.tools.base` so it doesn't try to import it
class MockTool:
    pass

class MockBaseModule:
    Tool = MockTool

sys.modules["nanobot.agent.tools.base"] = MockBaseModule()

spec.loader.exec_module(shell_module)

from tests.test_shell_injection import test_shell_injection_vulnerability, test_shell_redirection

async def main():
    print("Running tests...")
    print("Testing injection...")
    await test_shell_injection_vulnerability()
    print("Testing redirection...")
    await test_shell_redirection()
    print("All tests passed!")

asyncio.run(main())
