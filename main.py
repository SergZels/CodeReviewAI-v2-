from fastapi import FastAPI, Depends
from businessLogic import logger, GitHubRepoManager, GITHUB_TOKEN, MODEL, get_prompt, \
    get_code_review, answer_parse
from schemes import Review, Answer, ReviewRequestReact, AnswerForFrontend
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis
import json
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static/dist"), name="static")

origins = [
    "http://localhost:7777",
    "http://127.0.0.1:7777",
    "http://localhost:5173",
    "http://zelse.asuscomm.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_redis():
    redis = await aioredis.from_url("redis://rediscoderewaiv2:6379")
    try:
        yield redis
    finally:
        await redis.close()


@app.post('/review', response_model=Answer)
async def review(review_request: Review, redis=Depends(get_redis)):
    github_url = review_request.github_repo_url
    file_paths: list = []
    key_problems_text: str = ""
    rating_text: str = ""
    conclusion_text: str = ""

    cache_key = f"review:{github_url}"
    cached_data = await redis.get(cache_key)
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

    answer = Answer(file_paths=file_paths, key_problems=key_problems_text,
                    rating=rating_text, conclusion=conclusion_text)

    await redis.setex(cache_key, 60, json.dumps(answer.dict()))
    logger.info(f"Request received - {review_request}")
    return answer


# --------------------------API for React frontend---------------------------

@app.get("/")
async def serve_index():
    return FileResponse("static/dist/index.html")


@app.post('/reviewFrontend', response_model=AnswerForFrontend)
async def review(review_request: ReviewRequestReact, redis=Depends(get_redis)):
    github_url = review_request.github_repo_url
    file_paths: list = []
    prompt: str = ""
    review_result: str = ""
    key_problems_text: str = ""
    rating_text: str = ""
    conclusion_text: str = ""

    cache_key = f"review:{github_url}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    try:
        repo_manager = GitHubRepoManager(github_url, review_request.gitHubApiKey)
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
            review_result = await get_code_review(prompt=prompt, model=MODEL, TOKEN=review_request.openAIApiKey)
            key_problems_text, rating_text, conclusion_text = answer_parse(review_result)

        except Exception as e:
            review_result = f"Error in get_code_review {e}"
            logger.error(review_result)
            print(e)

    answer = AnswerForFrontend(file_paths=file_paths, prompt=prompt,
                               GPTReview=review_result, key_problems=key_problems_text,
                               rating=rating_text, conclusion=conclusion_text)

    await redis.setex(cache_key, 60, json.dumps(answer.dict()))
    logger.info(f"Request received - {review_request} \nAnswer - {answer}")
    return answer


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7777)
