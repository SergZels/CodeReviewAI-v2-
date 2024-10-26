import pytest
from unittest import mock
from businessLogic import GitHubRepoManager


@pytest.fixture
def mock_github_manager():
    github_url = 'https://github.com/user/repo.git'
    github_token = 'fake_token'
    return GitHubRepoManager(github_url, github_token)


@pytest.mark.asyncio
async def test_extract_owner_repo_from_url(mock_github_manager):
    owner, repo = mock_github_manager.extract_owner_repo_from_url()
    assert owner == 'user'
    assert repo == 'repo'


@pytest.mark.asyncio
async def test_clone_repo(mock_github_manager):
    with mock.patch("git.Repo.clone_from") as mock_clone, \
            mock.patch("tempfile.TemporaryDirectory", mock.MagicMock(return_value=mock.MagicMock())):
        file_paths, all_content = await mock_github_manager.clone_repo()

        mock_clone.assert_called_once()

        assert file_paths == []
        assert all_content == ""


@pytest.mark.asyncio
async def test_list_files_and_content(mock_github_manager, tmp_path):

    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test content")

    file_paths, all_content = await mock_github_manager.list_files_and_content(str(tmp_path))

    assert file_paths == ["test_file.txt"]
    assert "--- test_file.txt ---" in all_content
    assert "test content" in all_content


@pytest.mark.asyncio
async def test_clone_repo_with_temp_dir(mock_github_manager):
    with mock.patch("git.Repo.clone_from") as mock_clone:
        with mock.patch("tempfile.TemporaryDirectory", mock.MagicMock()) as mock_temp_dir:
            await mock_github_manager.clone_repo()

            mock_clone.assert_called_once()
            mock_temp_dir.assert_called_once()
