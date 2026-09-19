from tavily import TavilyClient
import os 
import streamlit as st
from  dotenv import load_dotenv
load_dotenv()

TAVILY_APIKEY=os.getenv("TAVILY_APIKEY")

if not TAVILY_APIKEY:
    TAVILY_APIKEY=st.secrets.get("TAVILY_APIKEY")

client = TavilyClient(api_key=TAVILY_APIKEY)

# response = tavily_client.search("Who is Leo Messi?")

def tavily_client(query):
    results=[]
    response=client.search(
        query=query,
        max_result=5
    )

    for i, data in enumerate(response['results'],1):
        title=data.get('title','unknown')
        url=data.get('url','')
        content=data.get('content','').strip()

        words = content.split()
        if len(words) > 300:
            content=" ".join(words[:300])+"..."
        results.append(f"{i}. **{title}**\n   {url}\n   {content}")

    return results
