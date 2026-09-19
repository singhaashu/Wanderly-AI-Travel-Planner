import requests
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from schema.flight_schema import FlightDetails

load_dotenv()

api_key=os.getenv("AVIATIONSTACK_APIKEY")

if not  api_key:
    api_key=st.secrets.get("AVIATIONSTACK_APIKEY")

    
def search_flight(origin,destination,date,return_date):

    url="http://api.aviationstack.com/v1/flights"

    params={
        "access_key":api_key,
        "dep_iata": origin,
        "arr_iata": destination,
        "flight_date": date,
        "return_date":return_date,
        "limit":5
    }
    response = requests.get(url, params=params)
    
    data=response.json()
    flight_data=[]
    if "data" in data:
        for flight in data["data"][:5]:
            airline=flight.get("airline",{}).get("name",'unknown')
            departure=flight.get("departure",{}).get("airport",'unknown')
            arrival=flight.get("arrival",{}).get("airport",'unknown')
            flight_status=flight.get("flight_status",'unknown')

            flight_data.append(f"""
            Airline: {airline}
            Departure: {departure}
            Arrival: {arrival}
            Status: {flight_status}
            """)
        
        return "\n".join(flight_data)
