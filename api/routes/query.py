# api/routes/query.py
from fastapi import APIRouter
from pydantic import BaseModel
from agent.query_llm import run_agent

router = APIRouter()


class QueryIn(BaseModel):
    question: str
    session_id: str | None = None
    max_iterations: int = 5


@router.post("/query")
async def query(in_: QueryIn):
    res = run_agent(in_.question, in_.max_iterations)
    return res
