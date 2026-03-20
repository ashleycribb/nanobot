import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from nanobot.providers.openai_codex_provider import OpenAICodexProvider

@pytest.mark.asyncio
async def test_codex_provider_ssl_error_no_retry():
    provider = OpenAICodexProvider()
    messages = [{"role": "user", "content": "hello"}]

    mock_token = MagicMock()
    mock_token.account_id = "test_account"
    mock_token.access = "test_token"

    with patch("nanobot.providers.openai_codex_provider.get_codex_token", return_value=mock_token):
        with patch("nanobot.providers.openai_codex_provider._request_codex", new_callable=AsyncMock) as mock_request:
            # Call fails with SSL error
            mock_request.side_effect = Exception("CERTIFICATE_VERIFY_FAILED")

            response = await provider.chat(messages)

            # Verify it was called only once
            assert mock_request.call_count == 1

            assert "CERTIFICATE_VERIFY_FAILED" in response.content
            assert response.finish_reason == "error"

@pytest.mark.asyncio
async def test_codex_provider_other_error_no_retry():
    provider = OpenAICodexProvider()
    messages = [{"role": "user", "content": "hello"}]

    mock_token = MagicMock()
    mock_token.account_id = "test_account"
    mock_token.access = "test_token"

    with patch("nanobot.providers.openai_codex_provider.get_codex_token", return_value=mock_token):
        with patch("nanobot.providers.openai_codex_provider._request_codex", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Some other error")

            response = await provider.chat(messages)

            # Verify it was called only once
            assert mock_request.call_count == 1
            assert "Some other error" in response.content
            assert response.finish_reason == "error"
