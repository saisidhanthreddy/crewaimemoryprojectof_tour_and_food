from crewai import Agent, LLM
from tools import tool
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Get the Google API key
google_api_key = os.getenv("GEMINI_API_KEY")
os.environ["GEMINI_API_KEY"] = google_api_key

# Define the LLM using CrewAI's LLM class
llm = LLM(
    model="gemini/gemini-1.5-pro-latest",
    api_key=google_api_key,
    temperature=0.5
)

# Memory persistence file
MEMORY_FILE = "travel_memory.json"

# Load existing memory or initialize an empty one
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {
        "starting_location": "",
        "destinations": [],
        "activities": [],
        "restrictions": [],
        "food_preference": "both",  # Default: veg and non-veg
        "previous_itineraries": []
    }

# Save memory to file
def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)

# Creating a travel planner agent with memory
travel_planner = Agent(
    role="Travel Planner",
    goal='Generate a personalized 7-day travel itinerary based on user preferences, respecting all restrictions',
    verbose=True,
    memory=True,
    backstory=(
        "You are a seasoned travel expert with a sharp memory for client preferences. "
        "You craft detailed, enjoyable itineraries while strictly adhering to restrictions "
        "like disliked activities, health concerns, and food choices."
    ),
    tools=[tool],  # SerperDevTool for research
    llm=llm,
    allow_delegation=False
)

# Update memory with user preferences
def update_memory(starting_location=None, destination=None, activities=None, restrictions=None, food_preference=None):
    memory = load_memory()
    if starting_location:
        memory["starting_location"] = starting_location
    if destination and destination not in memory["destinations"]:
        memory["destinations"].append(destination)
    if activities:
        memory["activities"] = list(set(memory["activities"] + activities.split(", ")))
    if restrictions:
        memory["restrictions"] = list(set(memory["restrictions"] + restrictions.split(", ")))
    if food_preference:
        memory["food_preference"] = food_preference.lower()
    save_memory(memory)
    return memory