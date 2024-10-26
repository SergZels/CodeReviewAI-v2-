import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from businessLogic import get_prompt, get_code_review


@pytest_asyncio.fixture
async def mock_openai_response():
    return {
        'choices': [{
            'message': {
                'content': "Key problems: ... Rating: 4/5. Conclusion: ..."
            }
        }]
    }


@pytest.mark.asyncio
async def test_get_code_review(mock_openai_response):
    prompt = "Sample prompt text"
    model = "gpt-4-turbo"
    TOKEN = "fake_token"

    with patch('businessLogic.AsyncOpenAI') as MockAsyncOpenAI:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        MockAsyncOpenAI.return_value = mock_client

        response = await get_code_review(prompt, model, TOKEN=TOKEN)

        MockAsyncOpenAI.assert_called_once_with(api_key=TOKEN)
        mock_client.chat.completions.create.assert_awaited_once_with(
            model=model,
            messages=[
                {"role": "system", "content": "You are a senior software engineer tasked with reviewing code."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        assert response == "Key problems: ... Rating: 4/5. Conclusion: ..."

