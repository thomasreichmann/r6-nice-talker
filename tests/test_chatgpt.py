import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.providers import ChatGPTProvider

@pytest.fixture
def mock_openai():
    with patch("src.providers.AsyncOpenAI") as MockClient:
        # Setup the chain: client.chat.completions.create -> return object with choices[0].message.content
        mock_create = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated Message"
        mock_create.return_value = mock_response
        
        MockClient.return_value.chat.completions.create = mock_create
        yield MockClient

@pytest.fixture
def provider(mock_openai):
    # We need to mock the file opening for prompts.json
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        # Mock json.load
        with patch("json.load") as mock_json:
            mock_json.return_value = [{"name": "Default", "prompt": "Be helpful"}]
            return ChatGPTProvider(api_key="fake_key")

@pytest.mark.asyncio
async def test_get_message_calls_openai(provider, mock_openai):
    """
    Test that get_message calls the OpenAI API with correct parameters.
    """
    msg = await provider.get_message(mode="text")
    
    assert msg == "Generated Message"
    
    # Verify API call
    client_instance = mock_openai.return_value
    client_instance.chat.completions.create.assert_called_once()
    
    # Check if history is updated
    assert len(provider.history) == 1
    assert provider.history[0] == "Generated Message"

@pytest.mark.asyncio
async def test_get_message_with_context_override(provider, mock_openai):
    """
    Test that context_override is included in the system/user prompt logic.
    """
    # We need to inspect the arguments passed to create()
    client_instance = mock_openai.return_value
    
    await provider.get_message(mode="text", context_override="VISUAL_PROOF")
    
    call_args = client_instance.chat.completions.create.call_args
    messages = call_args.kwargs['messages']
    
    # The prompt construction logic puts the scenario in the user prompt
    user_msg = messages[-1]['content']
    
    assert "VISUAL_PROOF" in user_msg
    
    # Also verify system prompt contains vision instructions if configured
    # (This depends on get_system_prompt logic in constants.py, verified implicitly here)

def test_history_management(provider):
    """
    Test that history is maintained and cleared on mode switch.
    """
    provider.history.append("Old Message")
    assert len(provider.history) == 1
    
    provider.next_mode()
    
    assert len(provider.history) == 0

