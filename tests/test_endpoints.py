import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_review_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        review_request = {
            "github_repo_url": "https://github.com/SergZels/MidjourneyFlaskProject.git",
            "candidate_level": "Junior",
            "assignment_description": "Implement a simple feature.",
        }

        response = await client.post("/review", json=review_request)

        assert response.status_code == 200
        response_data = response.json()
        assert "file_paths" in response_data
        assert "GPTReview" in response_data
        assert isinstance(response_data["file_paths"], list)
        assert isinstance(response_data["GPTReview"], str)

