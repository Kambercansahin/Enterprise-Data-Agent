from fastapi import FastAPI,Request,HTTPException,status
from fastapi.templating import Jinja2Templates
from src.graphs.workflow import graph
from src.api.schemas import ChatResponse, ChatRequest, ChatResponseBase

app = FastAPI()

templates = Jinja2Templates(directory="src/api/templates")

@app.post("/api/chat/",response_model=ChatResponse)
def request(req:ChatRequest):
    result=graph.invoke({"question": req.question})
    all_result = {
        "answer":result.get("generation"),
        "sql_query":result.get("sql_query"),
        "reasoning_steps":result.get("reasoning_steps"),
        "status":"success"
    }
    return all_result

