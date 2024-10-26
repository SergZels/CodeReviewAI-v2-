from fastapi import FastAPI, Request, Form, Depends
from pydantic import BaseModel, field_validator
import re
from enum import Enum
from businessLogic import logger, GitHubRepoManager, GITHUB_TOKEN, MODEL, get_prompt, \
    get_code_review, answer_parse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import redis
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")
origins = [
    "http://localhost:7777",
    "http://zelse.asuscomm.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = "localhost" #It works fine on the local machine, but there are some problems on the server. Look later
REDIS_PORT = 6379
redis_client = redis.Redis(host=REDIS_URL, port=REDIS_PORT, decode_responses=True)

def get_redis():
    return redis_client

class CandidateLevel(str, Enum):
    JUNIOR = 'Junior'
    MIDDLE = 'Middle'
    SENIOR = 'Senior'

class Review(BaseModel):
    assignment_description: str
    github_repo_url: str
    candidate_level: CandidateLevel

    @field_validator('github_repo_url')
    def validate_github_url(cls, value):
        github_pattern = re.compile(r'^https://github\.com/.+/.+$')
        if not github_pattern.match(value):
            raise ValueError('The URL must be a valid GitHub repository link.')
        return value

class Answer(BaseModel):
    file_paths: list[str]
    key_problems: str = None
    rating: str = None
    conclusion: str = None
    prompt: str
    GPTReview: str = None

@app.post('/review', response_model=Answer)
async def review(review_request: Review, redis=Depends(get_redis)):
    github_url = review_request.github_repo_url
    file_paths: list = []
    prompt: str = ""
    review_result: str = ""
    key_problems_text: str = ""
    rating_text: str = ""
    conclusion_text: str = ""

    cache_key = f"review:{github_url}"
    cached_data = redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    try:
        repo_manager = GitHubRepoManager(github_url, GITHUB_TOKEN)
        file_paths, all_content = await repo_manager.clone_repo()

        code_content = all_content
        candidate_level = review_request.candidate_level
        description = review_request.assignment_description
        prompt = get_prompt(code_content=code_content,
                            description=description,
                            candidate_level=candidate_level)
    except Exception as e:
        print(e)
        logger.error(f"Error in GitHib section {e}")
    else:
        try:
            review_result = await get_code_review(prompt=prompt, model=MODEL)
            key_problems_text, rating_text, conclusion_text = answer_parse(review_result)

        except Exception as e:
            review_result = f"Error in get_code_review {e}"
            logger.error(review_result)
            print(e)

    answer = Answer(file_paths=file_paths, prompt=prompt,
                    GPTReview=review_result, key_problems=key_problems_text,
                    rating=rating_text, conclusion=conclusion_text)

    redis.setex(cache_key, 60*5, json.dumps(answer.dict()))
    logger.info(f"Request received - {review_request}")
    return answer
'''
Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on th
is error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}

Unfortunately I don't have paid GPT due to financial problems this month, so I can't test everything properly
'''

@app.get('/')  # a simple frontend with reactivity
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
"""
I know that this was not in the technical task,
but I got excited about the project and decided to make a simple frontend :)
"""

@app.post('/reviewHTMX')
async def reviewHTMX(request: Request,
                     git_hub_repo_url: str = Form(...),
                     openai_api_key: str = Form(...),
                     description: str = Form(...),
                     level: str = Form(...),
                     ):
    file_paths = []
    reviewResult = ""
    prompt = ""

    try:
        repo_manager = GitHubRepoManager(git_hub_repo_url, GITHUB_TOKEN)
        file_paths, all_content = await repo_manager.clone_repo()

        prompt = get_prompt(code_content=all_content,
                            description=description,
                            candidate_level=level)

    except Exception as e:
        print(e)
        logger.error(f"Error in GitHib section {e}")

    else:
        try:
            reviewResult = await get_code_review(prompt=prompt, model=MODEL, TOKEN=openai_api_key)
        except Exception as e:

            reviewResult = f"Error in get_code_review {e}"
            logger.error(reviewResult)

    logger.info(
        f"Received a request from the site - Git Hub url {git_hub_repo_url}, description - {description}, level - {level}")
    return templates.TemplateResponse("reviewHTMX.html", {"request": request,
                                                          "file_paths": file_paths,
                                                          "review_result": f"{reviewResult} \n   -- Prompt-- {prompt}"})
