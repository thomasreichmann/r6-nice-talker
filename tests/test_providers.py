import pytest
import asyncio
from src.providers import RandomMessageProvider, FixedMessageProvider

@pytest.mark.asyncio
async def test_random_message_provider():
    """
    Test that RandomMessageProvider returns a message from the list.
    """
    messages = ["Hello", "World", "Test"]
    provider = RandomMessageProvider(messages)
    
    msg = await provider.get_message()
    assert msg in messages

@pytest.mark.asyncio
async def test_fixed_message_provider():
    """
    Test that FixedMessageProvider always returns the same message.
    """
    expected = "Good Luck"
    provider = FixedMessageProvider(expected)
    
    msg = await provider.get_message()
    assert msg == expected

@pytest.mark.asyncio
async def test_random_provider_empty_list():
    """
    Test that RandomMessageProvider handles empty lists gracefully.
    """
    provider = RandomMessageProvider([])
    msg = await provider.get_message()
    assert msg == ""

