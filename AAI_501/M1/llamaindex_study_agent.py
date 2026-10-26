"""Study-planner agent example. No API call occurs unless main() is run.

Install if you want to run it later:
python -m pip install llama-index-core llama-index-llms-google-genai python-dotenv

Sensors: assignment deadlines, calendar availability, course notes.
Actuators: create a task, reserve a study block, save a study plan.
The small input dataset is simulated; the output actions write real local files.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.google_genai import GoogleGenAI


OUTPUT_DIR = Path(__file__).resolve().parent / "study_agent_output"


# SENSORS: observe three different kinds of information.
def read_assignments() -> str:
    """Read the simulated assignment tracker, including deadlines and work estimates."""
    return json.dumps([
        {"course": "AAI 501", "assignment": "AI agent", "due": "2026-11-02",
         "estimated_hours": 3, "status": "not started"},
        {"course": "AAI 500", "assignment": "Statistics review", "due": "2026-11-04",
         "estimated_hours": 2, "status": "not started"},
    ])


def read_calendar() -> str:
    """Read simulated free study windows; returned times are America/Los_Angeles."""
    return json.dumps([
        {"start": "2026-10-30T18:00:00", "end": "2026-10-30T20:00:00"},
        {"start": "2026-10-31T10:00:00", "end": "2026-10-31T13:00:00"},
    ])


def read_course_notes() -> str:
    """Read simulated course notes describing the AI-agent assignment requirements."""
    return (
        "AAI 501: use LlamaIndex and Google's Gemini API. Include sensors "
        "that observe information and actuators that change the environment. "
        "Submit actual code; execution is not required."
    )


def append_record(filename: str, record: dict) -> str:
    """Persist a record to a local JSON Lines file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / filename).open("a", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    return f"Saved to {OUTPUT_DIR / filename}"


# ACTUATORS: perform three distinct changes to local planning resources.
def create_task(title: str, due_date: str) -> str:
    """Create a local to-do task. due_date must use YYYY-MM-DD format."""
    datetime.strptime(due_date, "%Y-%m-%d")
    return append_record("tasks.jsonl", {"title": title, "due_date": due_date})


def reserve_study_block(topic: str, start: str, end: str) -> str:
    """Record a local study reservation in an available window; use ISO datetimes.

    This writes a local planner entry, not an event in an external calendar.
    """
    block_start, block_end = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if block_end <= block_start:
        raise ValueError("The study block must end after it starts.")
    windows = json.loads(read_calendar())
    if not any(datetime.fromisoformat(w["start"]) <= block_start
               and block_end <= datetime.fromisoformat(w["end"]) for w in windows):
        raise ValueError("The study block must fit inside an available window.")
    return append_record("study_blocks.jsonl", {"topic": topic, "start": start, "end": end})


def save_study_plan(markdown: str) -> str:
    """Save the final study plan as a local Markdown document."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plan_path = OUTPUT_DIR / "study_plan.md"
    plan_path.write_text(markdown, encoding="utf-8")
    return f"Study plan saved to {plan_path}"


async def main() -> None:
    # This file is under USD/AAI_501/M1; the .env is in USD.
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    llm = GoogleGenAI(
        model="gemini-3.8-flash",
        api_key=os.environ["AAI_SECRET"],
    )
    tools = [FunctionTool.from_defaults(fn=fn) for fn in (
        read_assignments, read_calendar, read_course_notes,
        create_task, reserve_study_block, save_study_plan,
    )]
    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=(
            "You are a study-planning agent working with a simulated dataset. "
            "Read assignments, calendar availability, and course notes first. "
            "Prioritize the earliest deadline. Use tools to create a task, "
            "reserve one available study block, and save a Markdown study plan. "
            "Only report actions as completed after the corresponding tool succeeds. "
            "Calendar reservations and tasks are local files. Explain any errors."
        ),
    )
    response = await agent.run(
        user_msg="Using the sample October 30–31 availability, plan work on my earliest assignment."
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
