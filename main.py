import os

import fastapi
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from tavily import TavilyClient
from dotenv import load_dotenv

from setup import Invokation

load_dotenv()
app = FastAPI()

class Variables(BaseModel):
    key:str
    question:str
    website_url:str

@app.post("/teaql-demo")
async def teaql_demo(variables: Variables):
    if variables.key != "teaql-demo-987":
        raise fastapi.HTTPException(status_code=400, detail="Invalid key")
    else:
        teaql=await Invokation(variables.website_url,question=variables.question)
    return teaql


