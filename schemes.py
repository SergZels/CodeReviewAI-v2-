from pydantic import BaseModel, field_validator
import re
from enum import Enum

class CandidateLevel(str, Enum):
    JUNIOR = 'Junior'
    MIDDLE = 'Middle'
    SENIOR = 'Senior'


class Review(BaseModel):
    assignment_description: str
    github_repo_url: str
    candidate_level: CandidateLevel

    @field_validator('assignment_description')
    def non_empty_assignment_description(cls, value):
        if not value.strip():
            raise ValueError('Assignment description cannot be an empty string')
        return value

    @field_validator('github_repo_url')
    def validate_github_url(cls, value):
        github_pattern = re.compile(r'^https://github\.com/.+/.+$')
        if not github_pattern.match(value):
            raise ValueError('The URL must be a valid GitHub repository link.')
        return value

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


class ReviewRequestReact(BaseModel):
    assignment_description: str
    github_repo_url: str
    candidate_level: CandidateLevel
    gitHubApiKey: str
    openAIApiKey: str

    @field_validator('assignment_description')
    def non_empty_assignment_description(cls, value):
        if not value.strip():
            raise ValueError('Assignment description cannot be an empty string')
        return value
    @field_validator('github_repo_url')
    def validate_github_url(cls, value):
        github_pattern = re.compile(r'^https://github\.com/.+/.+$')
        if not github_pattern.match(value):
            raise ValueError('The URL must be a valid GitHub repository link.')
        return value

    @field_validator('gitHubApiKey', 'openAIApiKey')
    def non_empty_string(cls, value):
        if not value.strip():
            raise ValueError('API key cannot be an empty string')
        return value

class AnswerForFrontend(BaseModel):
    file_paths: list[str]
    key_problems: str = None
    rating: str = None
    conclusion: str = None
    prompt: str
    GPTReview: str = None