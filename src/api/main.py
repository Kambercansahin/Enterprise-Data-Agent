import uvicorn
from fastapi import FastAPI,Request,HTTPException,status
from fastapi.templating import Jinja2Templates
from src.graphs.workflow import graph
from src.api.schemas import ChatResponse, ChatRequest, ChatResponseBase
from src.tools.cache import get_cached_response, set_cached_response
import uuid
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from fastapi.responses import JSONResponse

REDIS_URL = os.getenv("REDIS_URL")
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL if REDIS_URL else "memory://",
    default_limits=["60/minute"]
)
app = FastAPI()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many request."}
    )
templates = Jinja2Templates(directory="src/api/templates")

@app.post("/api/chat/",response_model=ChatResponse)
@limiter.limit("10/minute")
async def get_chat(request:Request,req:ChatRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The question field cannot be left blank"
        )

    thread_id = request.headers.get("X-Thread-ID") or request.cookies.get("session_thread_id") or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    cached_data = get_cached_response(question)
    if cached_data:
        return {
            "answer": cached_data.get("answer"),
            "sql_query": cached_data.get("sql_query"),
            "reasoning_steps": cached_data.get("reasoning_steps"),
            "status": "success"
        }
    result = await graph.ainvoke({"question": question,"retry_count":0},config=config)

    all_result = {
        "answer":  (result.get("generation") or "").strip(),
        "sql_query": result.get("sql_query"),
        "reasoning_steps": result.get("reasoning_steps"),
        "status": "success"
    }

    set_cached_response(question, all_result, ttl_seconds=600)

    return all_result

@app.get("/", include_in_schema=False)
@app.get("/chat/", include_in_schema=False)
def get_chat_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"chat": {}}
    )


@app.post("/chat/", include_in_schema=False)
@limiter.limit("10/minute")
async def post_chat_page(request: Request):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        question = (body.get("question") or "").strip()
    else:
        form = await request.form()
        question = (form.get("question") or "").strip()

    if not question:
        return templates.TemplateResponse(
            request=request,
            name="chat.html",
            context={"chat": {"answer": "Lütfen geçerli bir soru girin."}}
        )

    cached_data = get_cached_response(question)
    if cached_data:
        return templates.TemplateResponse(
            request=request,
            name="chat.html",
            context={"chat": cached_data, "from_cache": True}
        )

    thread_id = request.cookies.get("session_thread_id") or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke({"question": question,"retry_count": 0}, config=config)

    all_result = {
        "question": question,
        "answer": (result.get("generation") or "").strip(),
        "sql_query": result.get("sql_query"),
    }
    set_cached_response(question, all_result, ttl_seconds=600)
    response = templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"chat": all_result, "from_cache": False}
    )
    response.set_cookie(key="session_thread_id", value=thread_id, httponly=True)
    return response

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8080, reload=True)
