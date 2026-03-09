import pytest
from pathlib import Path
from nanobot.agent.tools.shell import ExecTool

@pytest.mark.asyncio
async def test_shell_injection_vulnerability():
    tool = ExecTool()

    # Use a command that attempts to create a file via shell chaining
    file_path = Path("vulnerable.txt")
    if file_path.exists():
        file_path.unlink()

    result = await tool.execute(command="echo hello; touch vulnerable.txt")

    # If vulnerable, the file 'vulnerable.txt' will be created.
    # We assert that it does NOT exist (this test will fail on vulnerable code).
    print(f"Result: {result}")

    exists = file_path.exists()
    if exists:
        file_path.unlink()

    assert not exists, "Command chaining succeeded, vulnerability present"


@pytest.mark.asyncio
async def test_shell_redirection():
    tool = ExecTool()

    # Use a command that attempts redirection
    file_path = Path("output.txt")
    if file_path.exists():
        file_path.unlink()

    result = await tool.execute(command="echo hello > output.txt")

    # If vulnerable (supports shell), 'output.txt' will be created.
    # We assert that it does NOT exist (this test will fail on vulnerable code).

    exists = file_path.exists()
    if exists:
        file_path.unlink()

    assert not exists, "Shell redirection succeeded, vulnerability present"
