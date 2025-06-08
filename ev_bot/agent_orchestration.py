from langgraph.graph import StateGraph, END
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ev_bot.flight_agent import FlightAgent
from ev_bot.hotel_agent import HotelAgent
from ev_bot.logger import setup_logger

logger = setup_logger("agent_orchestration")


# Define LangGraph state schema
class GraphState(BaseModel):
    user_prompt: str
    flight_ideas: Optional[List[dict]] = Field(default_factory=list)
    hotel_offers: Optional[List[dict]] = Field(default_factory=list)
    combined_suggestions: Optional[List[dict]] = Field(default_factory=list)


# Node: Run Flight Agent
async def flight_agent_node(state: GraphState) -> GraphState:
    logger.info("Running FlightAgent node")
    agent = FlightAgent()
    result = await agent.run_agent(state.user_prompt)
    state.flight_ideas = [idea.model_dump() for idea in result.ideas]
    logger.info(f"FlightAgent returned {len(state.flight_ideas)} ideas")
    return state


# Node: Run Hotel Agent for each destination
async def hotel_agent_node(state: GraphState) -> GraphState:
    logger.info("Running HotelAgent node")
    hotel_agent = HotelAgent()
    hotel_results = []

    for idea in state.flight_ideas:
        city_code = idea["travel_summary"]["destination_code"]
        check_in = idea["travel_summary"]["travel_start_date"]
        check_out = idea["travel_summary"]["travel_end_date"]

        # Ensure string format for Amadeus API
        if isinstance(check_in, datetime):
            check_in = check_in.date().isoformat()
        if isinstance(check_out, datetime):
            check_out = check_out.date().isoformat()

        hotel_prompt = f"Find 3 good hotels in {city_code} from {check_in} to {check_out}"
        logger.info(f"Querying hotels for {city_code} from {check_in} to {check_out}")

        try:
            result = await hotel_agent.run_agent(hotel_prompt)
            hotels = [h.model_dump() for h in result.hotels]

            if not hotels:
                logger.warning(f"No hotels found for {city_code} between {check_in} and {check_out}")

            hotel_results.append({
                "destination_code": city_code,
                "hotels": hotels
            })

        except Exception as e:
            logger.error(f"HotelAgent failed for {city_code}: {str(e)}")
            hotel_results.append({
                "destination_code": city_code,
                "hotels": []
            })

    state.hotel_offers = hotel_results
    logger.info("HotelAgent processing complete")
    return state


# Node: Merge flight + hotel results
def merge_output_node(state: GraphState) -> GraphState:
    logger.info("Merging flight and hotel ideas")
    merged = []

    for idea in state.flight_ideas:
        dest_code = idea["travel_summary"]["destination_code"]
        hotels = next(
            (h["hotels"] for h in state.hotel_offers if h["destination_code"] == dest_code),
            []
        )
        merged.append({
            "travel_idea": idea,
            "hotels": hotels
        })

    state.combined_suggestions = merged
    logger.info(f"Merged {len(merged)} travel suggestions with hotel data")
    return state


# Build LangGraph
builder = StateGraph(GraphState)
builder.add_node("FlightAgent", flight_agent_node)
builder.add_node("HotelAgent", hotel_agent_node)
builder.add_node("MergeOutput", merge_output_node)

builder.set_entry_point("FlightAgent")
builder.add_edge("FlightAgent", "HotelAgent")
builder.add_edge("HotelAgent", "MergeOutput")
builder.add_edge("MergeOutput", END)

graph = builder.compile()


# Public method: agent_orchestration
async def agent_orchestration(prompt: str) -> dict:
    logger.info("Starting travel agent orchestration")
    state = GraphState(user_prompt=prompt)
    result = await graph.ainvoke(state)
    logger.info("Orchestration completed successfully")
    return result.model_dump()