import os
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq

from tools.searching_service import tavily_client
from tools.search_flight import search_flight
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_APIKEY"))

llm =ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=GROQ_API_KEY
)

class TravelState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add]
    user_query:str
    flight_results:str
    hotel_results:str
    itinerary:str
    llm_calls:str

# flight agent 

def flight_agent(state:TravelState):
    query=state["user_query"]    
    flight_data=search_flight(query)

    return {
        "flight_results":flight_data,
        "messages":[
            AIMessage(content=f"Flight Results fetched successfully")
        ]
    }

def hotel_agent(state:TravelState):
    query=state["user_query"]
    hotel_data=tavily_client(query)

    return {
      "hotel_results":hotel_data,
      "messages":[
          AIMessage(content=f"Hotel data information fetched")
      ]
    }

def itinerary_agent(state:TravelState):
    prompt=f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    response=llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"
        ),
 
        HumanMessage(content=prompt)
    ])

    return {
         "itinerary" : response.content,
         "messages":[response],
         "llm_calls":state.get("llm_calls",0)+1
    }

def final_agent(state:TravelState):

    final_prompt=f"""
    Generate final travel response.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """ 

    response = llm.invoke([
       HumanMessage(content=final_prompt)
    ])

    return {
       "messages":[response],
       "llm_calls":state.get("llm_calls",0)+1
    }   

graph=StateGraph(TravelState)

graph.add_node("flight_agent",flight_agent)
graph.add_node("hotel_agent",hotel_agent)
graph.add_node("itinerary_agent",itinerary_agent)
graph.add_node("final_agent",final_agent)


graph.add_edge(START,"flight_agent")
graph.add_edge("flight_agent","hotel_agent")
graph.add_edge("hotel_agent","itinerary_agent")
graph.add_edge("itinerary_agent","final_agent")
graph.add_edge("final_agent",END)

memory=MemorySaver()
app = graph.compile(checkpointer=memory)

if __name__ == '__main__':
    config={
        "configurable":{
            "thread_id":"aashish"
        }
    }

    user_input=input("Enter travel request:")

    result=app.invoke({
        "messages":[
            HumanMessage(content=user_input)
        ],
        "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
    },
    config
    )

    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)
