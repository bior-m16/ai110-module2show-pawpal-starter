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

- **`Task`** is one care activity: title, the pet it belongs to, duration, priority (higher number is more urgent), scheduled start time, frequency (once, daily, weekly), and a completed flag. Completing a task creates the next occurrence: a daily task recurs one day after the completion date, and a weekly task keeps its weekday (the next same-weekday slot after today), so a task finished late or early never recurs in the past or drifts to another day.
- **`Pet`** holds a pet's details and its own list of tasks. It adds and removes tasks, lists the pending ones, and completes a task, adding the next occurrence if it recurs.
- **`Owner`** holds the owner's available minutes and a list of pets. `get_all_tasks()` returns every pet's tasks in one list, and `filter_tasks()` narrows that list by pet and/or completion status.
- **`Scheduler`** is the planner. It holds no data of its own and reads everything through the owner's methods, so one plan covers all pets.

How they work together: an `Owner` has many `Pet`s, and each `Pet` has many `Task`s. `Scheduler.generate_plan()` takes one day's pending tasks across all pets (today by default), picks them by priority (earliest time breaks ties) until the owner's available minutes run out, and returns them in time order. `sort_by_time()` orders any list of tasks. `detect_conflicts()` flags tasks whose times overlap, `conflicts_for()` warns about a new task before it is added, and `explain_plan()` writes out the plan, the tasks left out, and any conflicts. The plan respects each task's scheduled time and only flags overlaps; it never moves a task.

`main.py` is a terminal demo of this, and `tests/test_pawpal.py` holds the tests (run with `pytest`).

## 🖥️ Sample Output

Run the terminal demo with two pets (Mochi and Luna), 90 available minutes, and four tasks that are added in reverse time order:

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

Tasks in the order they were added (grouped by pet):
  Tue 15:00 Grooming (Mochi, pending)
  Tue 07:30 Morning walk (Mochi, pending)
  Tue 18:00 Play session (Luna, pending)
  Tue 08:00 Breakfast and medication (Luna, pending)

Sorted by time:
  Tue 07:30 Morning walk (Mochi, pending)
  Tue 08:00 Breakfast and medication (Luna, pending)
  Tue 15:00 Grooming (Mochi, pending)
  Tue 18:00 Play session (Luna, pending)

Completed 'Morning walk'; its next occurrence was added.

Filter: Mochi's tasks
  Tue 07:30 Morning walk (Mochi, done)
  Tue 15:00 Grooming (Mochi, pending)
  Wed 07:30 Morning walk (Mochi, pending)

Filter: pending tasks
  Tue 08:00 Breakfast and medication (Luna, pending)
  Tue 15:00 Grooming (Mochi, pending)
  Tue 18:00 Play session (Luna, pending)
  Wed 07:30 Morning walk (Mochi, pending)

Filter: done tasks
  Tue 07:30 Morning walk (Mochi, done)

Filter: Luna's pending tasks
  Tue 08:00 Breakfast and medication (Luna, pending)
  Tue 18:00 Play session (Luna, pending)

Conflict check: no tasks yet
  no conflicts

Conflict check: two pairs of tasks at the same time
  Warning: Grooming (Mochi, 15:00-15:45) overlaps Vet checkup (Mochi, 15:00-15:30) [same pet]
  Warning: Training class (Mochi, 18:00-18:30) overlaps Play session (Luna, 18:00-18:20) [different pets]
```

The demo shows `sort_by_time()` (tasks added out of order come back in time order), `filter_tasks()` by pet and by status, and a recurring task: completing the daily walk adds the next one. The last section shows conflict warnings for two tasks scheduled at the same time, once for the same pet (Grooming and Vet checkup, both Mochi) and once for different pets (Training class for Mochi and Play session for Luna). The scheduler returns these as warning messages and the program keeps running. The weekdays depend on the day you run it.

Add `--conflict` to include a task that overlaps two others. The scheduler warns about it when the task is added and flags it in the plan (the rest of the output matches the run above):

```bash
python main.py --conflict
```

```
Warning: Vet video call overlaps Morning walk (Mochi).
Warning: Vet video call overlaps Breakfast and medication (Luna).
Today's Schedule for Jordan (90 min available)
============================================================
07:30 - Morning walk (Mochi, 30 min, priority 3)
07:45 - Vet video call (Luna, 20 min, priority 3)
08:00 - Breakfast and medication (Luna, 10 min, priority 3)
18:00 - Play session (Luna, 20 min, priority 2)
Total 80 of 90 available minutes. Tasks were chosen by priority, then earliest time, and listed in time order.
Left out: Grooming (Mochi, 45 min) did not fit in the remaining time.
Conflict: Morning walk (Mochi, 07:30-08:00) overlaps Vet video call (Luna, 07:45-08:05) [different pets]
...
```

## 🧪 Testing PawPal+

Run the test suite from the project folder:

```bash
python -m pytest
```

Add `-v` to list every test by name.

### What the tests cover

The 45 tests in `tests/test_pawpal.py` check the logic layer (`pawpal_system.py`), covering the normal cases and the edge cases:

- **Sorting:** tasks come back in time order, including tasks on different days, an empty list, and tasks at the same time (original order kept, original list unchanged).
- **Recurring tasks:** a daily task creates the next one for the following day; a weekly task keeps its weekday whether it is completed on time, late, or early; month and year rollover works; a one-time task creates nothing; completing a task twice does not create duplicates.
- **Conflict detection:** overlapping tasks are flagged as warnings, including tasks at the exact same time (same pet or different pets), overlaps across midnight, and one long task overlapping two short ones. Back-to-back tasks, completed tasks, and tasks on other days are not flagged.
- **Filtering:** by pet, by completion status, and by both; an unknown pet returns an empty list.
- **Planning:** the plan combines every pet's tasks for one day, picks by priority within the available minutes, breaks ties by earliest time, leaves out what doesn't fit and explains why.
- **Empty cases:** a pet with no tasks, an owner with no pets, and zero available minutes do not crash.

### Sample test output

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\biora\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 45 items

tests\test_pawpal.py .............................................       [100%]

============================= 45 passed in 0.06s ==============================
```

### Confidence level: ★★★★☆ (4 out of 5)

I'm fairly confident the scheduling logic is reliable: all 45 tests pass, and they cover the main behaviors and the edge cases that were most likely to break, including one real bug the tests found (duplicate recurring tasks). I stopped short of five stars because:

- The Streamlit UI is not covered by pytest; I only checked it by clicking through the app.
- Some inputs are not tested, such as zero-length tasks, leap-day weekly tasks, and time zones.
- The planner is greedy: it picks by priority and flags overlaps but never moves tasks, so it is not guaranteed to find the best possible plan.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | `Scheduler.sort_by_time()` | Orders any list of tasks by start time; returns a new list |
| Filtering | `Owner.filter_tasks()` | By pet name, completion status, or both, across all pets |
| Conflict detection | `Scheduler.detect_conflicts()`, `conflict_warnings()`, `conflicts_for()` | Finds overlapping tasks and reports them as warnings, never errors |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task()` | Daily and weekly tasks create their next occurrence when completed |

### Sorting

`Scheduler.sort_by_time(tasks)` returns the tasks ordered by `scheduled_time`, earliest first. It uses `sorted()` with a lambda key, so the original list is unchanged and tasks with the same time keep their relative order. The UI's task table and the "Sorted by time" view in `main.py` both use it, and `generate_plan()` uses it to return the final plan in time order.

### Filtering

`Owner.filter_tasks(pet_name=None, completed=None)` returns tasks across all of the owner's pets. Pass `pet_name` to keep one pet's tasks, `completed=False` for pending tasks, `completed=True` for finished ones, or both to combine them. Leaving an argument as `None` means "don't filter on this". `Scheduler.generate_plan()` calls it with `completed=False`, so the planner reads every pet's tasks through the owner and then keeps only the requested day's.

### Conflict detection

Two tasks conflict when their time ranges (start time to start time plus duration) overlap. A task that ends exactly when the next one starts does not conflict. Conflicts are found for the same pet or for different pets, since the owner can only do one thing at a time.

- `Scheduler.detect_conflicts(tasks)` sorts the tasks by start time and compares each one only with the tasks that start before it ends, so it costs O(n log n) plus the number of conflicts. It returns the overlapping pairs.
- `Scheduler.conflict_warnings(tasks=None)` turns those pairs into plain warning strings such as `Warning: Grooming (Mochi, 15:00-15:45) overlaps Vet checkup (Mochi, 15:00-15:30) [same pet]`. It checks the owner's pending tasks by default and returns an empty list when there are no conflicts, so it never crashes the program. The UI shows these warnings under the task table.
- `Scheduler.conflicts_for(task)` returns the pending tasks a single task overlaps, for checking a task before it is added.

The scheduler only flags conflicts. It never moves or drops a task to resolve one.

### Recurring tasks

When a daily or weekly task is completed, a new `Task` is created for its next occurrence and added to the same pet:

- `Task.mark_complete(now=None)` marks the task done and returns the next occurrence, or `None` for a one-time task. The date logic lives in the private `Task._next_time()`.
- `Pet.complete_task(task)` calls it and adds the new task to the pet's list.
- **Daily** tasks recur one day after the completion date, at the same time of day.
- **Weekly** tasks keep their weekday: the next one is the first slot on the same weekday after today, however late or early the task was completed. A Tuesday task finished on Thursday still recurs on a Tuesday.
- **Once** tasks do not recur.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. Start the app with `streamlit run app.py`. Set the owner's name and how many minutes they have available today.
2. In **Add a Pet**, enter a name, species, and age, and click **Add pet**. Add as many pets as you like; each one keeps its own tasks. A duplicate or empty name shows an error.
3. In **Add a Task**, pick a pet, then enter the task's title, duration, priority, start time, and whether it repeats (once, daily, weekly), and click **Add task**.
4. The **All tasks** table lists every pet's tasks sorted by time. Use the pet and status filters to narrow it. If two tasks overlap, a warning appears under the table until the overlap is fixed.
5. Click **Generate schedule** to see today's plan. Tasks are chosen by priority until the available minutes run out, listed in time order, and **Why this plan?** explains what was included, what was left out, and any conflicts.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
