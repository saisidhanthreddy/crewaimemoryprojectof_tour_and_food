from crewai import Task
from agents import travel_planner
from tools import tool
import json
from agents import load_memory, save_memory

collect_preferences_task = Task(
    description=(
        "Collect the user’s travel preferences via prompts:\n"
        "1. Starting location: {starting_location}\n"
        "2. Travel destination: {destination}\n"
        "3. Preferred activities (e.g., sightseeing, food, waterfalls): {activities}\n"
        "4. Restrictions (e.g., scared places, health issues): {restrictions}\n"
        "5. Food preference (veg, non-veg, both): {food_preference}\n"
        "Update memory with these inputs. Use existing memory if no new input is provided."
    ),
    expected_output='Updated memory with user preferences in JSON format',
    tools=[tool],
    agent=travel_planner,
    output_file='preferences.json'
)

itinerary_task = Task(
    description=(
        "Generate a 7-day travel itinerary from {starting_location} to {destination}, "
        "focusing on {activities} and avoiding restrictions: {restrictions}. "
        "Cater to food preference: {food_preference}. Each day should include morning, afternoon, "
        "and evening activities, ensuring variety and feasibility. Use internet search for details."
    ),
    expected_output='A 7-day travel itinerary in JSON format respecting all preferences',
    tools=[tool],
    agent=travel_planner,
    output_file='itinerary.json'
)

review_restrictions_task = Task(
    description=(
        "List all remembered restrictions from memory: {restrictions}. "
        "Review the itinerary: {itinerary} and justify why certain activities or foods "
        "were excluded based on user input (e.g., 'You restricted water places'). "
        "If the user asks about exclusions (e.g., 'Why no waterfalls?'), provide a clear answer "
        "in the justifications section."
    ),
    expected_output='A JSON object listing restrictions and justifications for exclusions',
    tools=[tool],
    agent=travel_planner,
    output_file='restrictions_review.json'
)