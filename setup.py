import asyncio
import os
from typing import TypedDict, Annotated

import langchain_google_genai
import requests
from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langgraph.constants import START,END
from langgraph.graph import StateGraph, add_messages, state
from pydantic import BaseModel, Field

from tavily import TavilyClient as AsyncTavilyClient
from dotenv import load_dotenv

from prompt import sys

load_dotenv()

client = AsyncTavilyClient(os.getenv("T1"))
fallback=AsyncTavilyClient(os.getenv("T2"))
llm = init_chat_model(model_provider="google-genai",model="gemini-3.5-flash-lite")
ai=init_chat_model(model="grok-4.7",model_provider="xAI")

class citation(BaseModel):
    output:str=Field(min_length=3,max_length=95)
    line_num:int = Field(gt=0,lt=99)
    quote:str=Field(min_length=3,max_length=95)

async def agentic_ai(query:str):
    try:
        answer= await llm.ainvoke(query)
        print(query)
    except langchain_google_genai.chat_models.GoogleAPIError:
        answer= await ai.ainvoke(query)
        print("grpl")
    except langchain_google_genai.chat_models.GoogleRateLimitError:
        print("rate")
        answer= await ai.ainvoke(query)
    return answer.content[0]["text"]


async def Tavily_AI(query:str,url:str):
    try:
        answer=  client.extract(url)
    except Exception:
        answer = fallback.crawl(url)

    return answer

class State(TypedDict):
    messages:Annotated[list[AnyMessage],add_messages]
    url:str
    result:str
    line_num:int
    quote:str


async def Sys_prompt(state:State):
    print("therer")
    return {"messages":[SystemMessage(content=sys)]}

async def Answer(state:State):
    print("there")
    instructions=await agentic_ai(f"{state['messages']} Based on this what should be my instructions for the agent to crawl to it should be short under 150 charecters including spaces ")
    print(instructions)
    try:
        content=await Tavily_AI(url=state['url'],query=instructions)

        print(f"seach : { content}")
        return {"result":content}
    except requests.exceptions.HTTPError as e:
        print("STATUS:", e.response.status_code)
        print("BODY:", e.response.text)
        raise


async def Conclusion(state:State):
    content=await llm.with_structured_output(citation).ainvoke(f"{state} based on this did we solve the users questions just directly give the answer in the least amount of words and provide the quote in quote sections and for line section give a rough number If its genuinely not there say I currently do not have that in my knowledge base is there anything else I could assist with and put the quote property as n/a and link as 1 ")
    print(f"main mesage:{content}")
    return {"messages":[content.output],"line_num":content.line_num,"quote":content.quote}

graph = StateGraph(State)
graph.add_node("sys",Sys_prompt)
graph.add_node("crawl",Answer)
graph.add_node("conclusion",Conclusion)
graph.add_edge(START,"sys")
graph.add_edge("sys","crawl")
graph.add_edge("crawl","conclusion")
graph.add_edge("conclusion",END)
agent=graph.compile()

async def Invokation(url:str,question:str):
    answer=await agent.ainvoke({"messages":HumanMessage(content=question),"url":url})
    print(answer)
    print(answer["messages"][-1].content)
    return {"line_num":answer["line_num"],"quote":answer["quote"],"messages":answer["messages"][-1].content}

