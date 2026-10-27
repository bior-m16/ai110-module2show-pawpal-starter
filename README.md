# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation Summary

The logic layer lives in `pawpal_system.py` and has four classes that mirror `diagrams/uml.mmd`:

- **`Task`** is one care activity: title, the pet it belongs to, duration, priority (higher number is more urgent), scheduled start time, frequency (once, daily, weekly), and a completed flag. Completing a recurring task returns a copy dated one day or week later.
- **`Pet`** holds a pet's details and its own list of tasks. It adds and removes tasks, lists the pending ones, and completes a task, adding the next occurrence if it recurs.
- **`Owner`** holds the owner's available minutes and a list of pets. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`** is the planner. It holds no data of its own and reads everything through `Owner.get_all_tasks()`, so one plan covers all pets.

How they work together: an `Owner` has many `Pet`s, and each `Pet` has many `Task`s. `Scheduler.generate_plan()` takes the pending tasks across all pets, picks them by priority (earliest time breaks ties) until the owner's available minutes run out, and returns them in time order. `detect_conflicts()` flags tasks whose times overlap, and `explain_plan()` writes out the plan, the tasks left out, and any conflicts. The plan respects each task's scheduled time and only flags overlaps; it never moves a task.

`main.py` is a terminal demo of this, and `tests/test_pawpal.py` holds the tests (run with `pytest`).

## 🖥️ Sample Output

Run the terminal demo with two pets (Mochi and Luna), 90 available minutes, and four tasks:

```bash
python main.py
```

```
Today's Schedule for Jordan (90 min available)
============================================================
07:30 - Morning walk (Mochi, 30 min, priority 3)
08:00 - Breakfast and medication (Luna, 10 min, priority 3)
18:00 - Play session (Luna, 20 min, priority 2)
Total 60 of 90 available minutes. Tasks were chosen by priority, then earliest time, and listed in time order.
Left out: Grooming (Mochi, 45 min) did not fit in the remaining time.
```

Add `--conflict` to include a task that overlaps two others, so the scheduler flags it:

```bash
python main.py --conflict
```

```
Today's Schedule for Jordan (90 min available)
============================================================
07:30 - Morning walk (Mochi, 30 min, priority 3)
07:45 - Vet video call (Luna, 20 min, priority 3)
08:00 - Breakfast and medication (Luna, 10 min, priority 3)
18:00 - Play session (Luna, 20 min, priority 2)
Total 80 of 90 available minutes. Tasks were chosen by priority, then earliest time, and listed in time order.
Left out: Grooming (Mochi, 45 min) did not fit in the remaining time.
Conflict: Morning walk (Mochi) overlaps Vet video call (Luna).
Conflict: Vet video call (Luna) overlaps Breakfast and medication (Luna).
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
