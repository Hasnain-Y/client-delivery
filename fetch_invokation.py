import asyncio

import httpx

base_url = "http://127.0.0.1:8000/teaql-demo"
async def invokation(website_url:str,key:str,question:str):
    async with httpx.AsyncClient() as client:
        response = await client.post(url=base_url,json={"website_url":website_url,"key":key,"question":question})
        response.raise_for_status()
        print(response.json())
        return response.json()

asyncio.run(invokation(website_url="https://teaql.io/docs/core/intro/",question="what is teaql cofundernames",key="teaql-demo-987"))