from pydantic import BaseModel,Field,ConfigDict
from typing import Optional, Union


class ChatRequest(BaseModel):
    question:str =Field(min_length=1,max_length=250)


class ChatResponseBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    answer:str



class ChatResponse(ChatResponseBase):
    model_config = ConfigDict(from_attributes=True)
    sql_query: Optional[str] = None
    reasoning_steps: Optional[str] = None
    status: Optional[str] = "success"


