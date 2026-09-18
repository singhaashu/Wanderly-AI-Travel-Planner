import requests
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
# api_key=os.getenv('AVIATIONSTACK_APIKEY')

api_key = st.secrets.get(
    "AVIATIONSTACK_APIKEY",
    os.getenv("AVIATIONSTACK_APIKEY")
)

def search_flight(query):
    url="http://api.aviationstack.com/v1/flights"

    params={
        "access_key":api_key,
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

    


