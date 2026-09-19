from pydantic import BaseModel,Field

class FlightDetails(BaseModel):

    origin:str=Field(
        description="Departure airport IATA code, e.g. DEL"
    )

    destination:str=Field(
        description="Arrival airport IATA code, e.g. GOI"
    )

    departure_date: str | None= Field(
        default=None,
        description="Outbound travel date in YYYY-MM-DD format"
    )

    return_date: str | None = Field(
        default=None,
        description="Return date in YYYY-MM-DD format. None for one-way travel."
    )
