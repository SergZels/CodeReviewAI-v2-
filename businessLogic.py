import os
import git
from dotenv import load_dotenv
import logging
import tempfile
import aiofiles
import asyncio
from openai import AsyncOpenAI
import re

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
MODEL = os.getenv("MODEL")


#------------------logger-----------------------------------------------------------------------
class AsyncFileHandler(logging.FileHandler):
    def emit(self, record):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, super().emit, record)


logger = logging.getLogger('async_logger')
logger.setLevel(logging.INFO)
handler = AsyncFileHandler('Logfile.txt')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# ----------------------------GitHub------------------------------------------------------------------
class GitHubRepoManager:
    """Class to manage operations on a GitHub repository, including cloning and listing file contents.

     Attributes:
         github_url (str): The URL of the GitHub repository.
         github_token (str): GitHub access token for authentication.
         owner (str): The owner of the GitHub repository.
         repo (str): The name of the repository.
     """
    def __init__(self, github_url, github_token):
        self.github_url = github_url
        self.github_token = github_token
        self.owner, self.repo = self.extract_owner_repo_from_url()

    def extract_owner_repo_from_url(self):
        parts = self.github_url.rstrip(".git").split('/')
        owner = parts[-2]
        repo = parts[-1]
        return owner, repo

    async def clone_repo(self):
        """Clones the GitHub repository to a temporary directory and retrieves file paths and content.

            The repository is cloned using the tokenized URL, and all files' relative paths and content
            are collected.

            Returns:
              Tuple[List[str], str]: A tuple containing:
                   - List of file paths (relative to the root of the repository).
                    - All content of the files as a single concatenated string.
        """
        tokenized_url = self.github_url.replace('https://', f'https://{self.github_token}@')

        with tempfile.TemporaryDirectory() as tmpdirname:
            print(f"Cloning to a temporary directory {tmpdirname}")

            git.Repo.clone_from(tokenized_url, tmpdirname)
            file_paths, all_content = await self.list_files_and_content(tmpdirname)

            return file_paths, all_content

    async def list_files_and_content(self, local_repo_path):
        """Recursively lists files and reads their content from the local repository.

             This method excludes the `.git` directory and reads the contents of each file
             asynchronously, appending the contents with headers for each file.

             Args:
                 local_repo_path (str): The path to the local cloned repository.

             Returns:
                 Tuple[List[str], str]: A tuple containing:
                     - List of file paths (relative to the root of the repository).
                     - All content of the files as a single concatenated string with headers.
        """
        file_paths = []
        all_content = ""

        for root, dirs, files in os.walk(local_repo_path):

            dirs[:] = [d for d in dirs if d != '.git']

            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_repo_path)
                file_paths.append(relative_path)

                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                    all_content += f"\n--- {relative_path} ---\n{content}"

        return file_paths, all_content


# ------------------------------OpenAI--------------------------------------------------------------------
def get_prompt(code_content: str, candidate_level: str, description: str):
    prompt = f"""
      You are an expert code reviewer. The code below is written by a {candidate_level} developer.
      Here is the task description:
      {description}

      Code:
      {code_content}

      Please provide:
      1. **Key Problems** - a list of the main issues, written in a single paragraph or bullet points, starting with "Key Problems:".
      2. **Rating** - a score out of 5 for the developer’s performance, starting with "Rating:".
      3. **Conclusion** - a summary of the overall quality and suggestions for improvement, starting with "Conclusion:".

      Please make sure to use these headings exactly as written (Key Problems, Rating, Conclusion) so the response remains consistent.
      """
    return prompt


async def get_code_review(prompt: str, model: str, TOKEN=None):
    if TOKEN:
        client = AsyncOpenAI(api_key=TOKEN)
    else:
        client = AsyncOpenAI(api_key=OPENAI_TOKEN)

    response = await client.chat.completions.create(
        model=model,  # "gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a senior software engineer tasked with reviewing code."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        temperature=0.7,
    )

    return response['choices'][0]['message']['content']

def answer_parse(response: str):
    key_problems = re.search(r"(?<=Key Problems:\n)(.*?)(?=\n\nRating:)", response, re.DOTALL)
    rating = re.search(r"(?<=Rating:\s)(\d+(\.\d+)?/\d+)", response)
    conclusion = re.search(r"(?<=Conclusion:\n)(.*)", response, re.DOTALL)

    key_problems_text = key_problems.group(0).strip() if key_problems else None
    rating_text = rating.group(0).strip() if rating else None
    conclusion_text = conclusion.group(0).strip() if conclusion else None

    return key_problems_text, rating_text, conclusion_text