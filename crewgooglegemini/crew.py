from crewai import Crew, Process
from tasks import collect_preferences_task, itinerary_task, review_restrictions_task
from agents import save_memory, travel_planner, load_memory, update_memory
import json
import os
import re

# Load current memory
memory = load_memory()

# Collect user input dynamically via terminal
print("Where are you traveling from?")
starting_location = input("> ").strip()

print("What is your travel destination?")
destination = input("> ").strip()

print("What do you want to do at the destination? (e.g., sightseeing, food, waterfalls, hillclimbing, beaches)")
activities = input("> ").strip()

print("Any restrictions? (e.g., scared places, health issues, no water activities)")
restrictions = input("> ").strip()

print("Food preference? (veg, non-veg, both)")
food_preference = input("> ").strip()

# Update memory with user inputs
memory = update_memory(
    starting_location=starting_location,
    destination=destination,
    activities=activities,
    restrictions=restrictions if restrictions else None,
    food_preference=food_preference if food_preference else None
)

# Form the crew with sequential process
crew = Crew(
    agents=[travel_planner],
    tasks=[
        collect_preferences_task,
        itinerary_task
    ],
    process=Process.sequential,
    verbose=True
)

# Execute the crew for preferences and itinerary
result = crew.kickoff(inputs={
    'topic': 'travel planning',
    'starting_location': starting_location,
    'destination': destination,
    'activities': activities,
    'restrictions': json.dumps(memory["restrictions"]) if memory["restrictions"] else "None",
    'food_preference': memory["food_preference"],
    'itinerary': '{}'
})

print("Initial Result:", result)

# Extract and save the itinerary from the task output
itinerary_file = 'itinerary.json'
try:
    itinerary_output = result.tasks_output[1].raw  # itinerary_task is the second task
    itinerary_json_str = re.search(r'```json\s*(.*?)\s*```', itinerary_output, re.DOTALL)
    if itinerary_json_str:
        final_itinerary = json.loads(itinerary_json_str.group(1))
    else:
        final_itinerary = json.loads(itinerary_output)  # Fallback if no ```json``` markers
    with open(itinerary_file, 'w') as f:
        json.dump(final_itinerary, f, indent=4)
    print(f"Successfully saved itinerary to {itinerary_file}")
except (IndexError, json.JSONDecodeError, AttributeError) as e:
    print(f"Error extracting itinerary: {e}")
    final_itinerary = {}
    with open(itinerary_file, 'w') as f:
        json.dump(final_itinerary, f, indent=4)

# Update memory with the itinerary if valid
if final_itinerary:
    memory["previous_itineraries"].append(final_itinerary)
    save_memory(memory)
else:
    print("Warning: No valid itinerary to save to memory.")

# Run the review task separately with the itinerary
if final_itinerary:
    review_crew = Crew(
        agents=[travel_planner],
        tasks=[review_restrictions_task],
        process=Process.sequential,
        verbose=True
    )
    review_result = review_crew.kickoff(inputs={
        'topic': 'travel planning',
        'starting_location': starting_location,
        'destination': destination,
        'activities': activities,
        'restrictions': json.dumps(memory["restrictions"]) if memory["restrictions"] else "None",
        'food_preference': memory["food_preference"],
        'itinerary': json.dumps(final_itinerary)
    })
    print("Review Result:", review_result)

    # Extract and save the review output
    review_file = 'restrictions_review.json'
    try:
        review_output = review_result.tasks_output[0].raw  # review_restrictions_task is the only task
        review_json_str = re.search(r'```json\s*(.*?)\s*```', review_output, re.DOTALL)
        if review_json_str:
            review_data = json.loads(review_json_str.group(1))
        else:
            review_data = json.loads(review_output)  # Fallback if no ```json``` markers
        with open(review_file, 'w') as f:
            json.dump(review_data, f, indent=4)
        print(f"Successfully saved review to {review_file}")
    except (IndexError, json.JSONDecodeError, AttributeError) as e:
        print(f"Error extracting review: {e}")
        review_data = {}
        with open(review_file, 'w') as f:
            json.dump(review_data, f, indent=4)
else:
    review_data = {}
    with open('restrictions_review.json', 'w') as f:
        json.dump(review_data, f, indent=4)

# Simulate a follow-up question
print("\nAsk a question about the itinerary (e.g., 'Why didn’t you include waterfalls?'):")
question = input("> ").strip()
if question and review_data:
    justifications = review_data.get("justifications", {})
    responses = []
    
    # Split the question into parts if it contains multiple queries
    question_parts = question.lower().replace("why didn’t you include", "").split(" and ")
    
    if isinstance(justifications, dict):
        # Handle dictionary format
        for part in question_parts:
            part = part.strip().rstrip("?")
            for key, value in justifications.items():
                if part in key.lower() or key.lower() in part:
                    responses.append(f"{key}: {value}")
                    break
            else:
                responses.append(f"{part}: No specific justification found.")
    
    elif isinstance(justifications, list):
        # Handle list format
        for part in question_parts:
            part = part.strip().rstrip("?")
            for item in justifications:
                activity = item.get("activity", "").lower()
                reason = item.get("reason", "No specific reason provided.")
                if part in activity or activity in part:
                    responses.append(f"{activity}: {reason}")
                    break
            else:
                responses.append(f"{part}: No specific justification found.")
    
    if responses:
        print("Agent Response:", " ".join(responses))
    else:
        print("Agent Response: No specific justification found.")
elif question:
    print("Agent Response: Unable to provide justification due to missing review data.")