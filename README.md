# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## Features

- **Multiple pets, separate task lists.** An owner can add any number of pets, and each pet keeps its own tasks.
- **Rich tasks.** Every task has a title, duration, priority (low, medium, high), start time, and a repeat setting (once, daily, weekly).
- **Sorting by time.** Tasks are always shown earliest first (`Scheduler.sort_by_time()`), including tasks on different days.
- **Priority levels.** Every task is Low, Medium, or High (`Priority`), and `Scheduler.sort_by_priority()` orders tasks by priority first (High first), then by time.
- **Filtering.** Narrow the task list by pet, by status (pending or done), or both (`Owner.filter_tasks()`).
- **Priority-based daily plan.** `Scheduler.generate_plan()` takes one day's pending tasks across all pets and picks the highest priority first (earliest time breaks ties) until the owner's available minutes run out. A task that doesn't fit is skipped so a shorter one can still use the remaining time.
- **Conflict warnings.** Tasks whose times overlap are flagged, whether they belong to the same pet or different pets, and reported as readable warnings instead of errors (`detect_conflicts()`, `conflict_warnings()`). Back-to-back tasks are not conflicts. A new task can also be checked against existing ones before it is added (`conflicts_for()`).
- **Edit and remove tasks.** Change a task's title, duration, priority, date, start time, or repeat setting, or remove it, so a conflict can actually be fixed.
- **Daily recurrence.** Completing a daily task creates a new one for the following day (`Task.mark_complete()`, `Pet.complete_task()`).
- **Weekly recurrence that keeps its weekday.** A weekly task always comes back on the same day of the week, even if it was completed late or early. Completing a task twice never creates a duplicate.
- **Plan explanation.** `Scheduler.explain_plan()` lists what was planned and when, how many minutes were used, which tasks were left out and why, and any conflicts.
- **Next available slot.** `Scheduler.find_next_free_slot()` finds the earliest gap in the day (06:00 to 22:00) long enough for a task, so a conflict comes with a concrete place to move to.
- **Saved between runs.** Pets and tasks are written to `data.json` and loaded again the next time the app starts (see [Data persistence](#-data-persistence)).
- **Readable output.** Color-coded priority and status badges, an emoji for each kind of task, and boxed tables built with `tabulate` (see [Output formatting](#-output-formatting)).
- **Safe with empty data.** A pet with no tasks, an owner with no pets, or zero available minutes produce an empty plan, not an error.
- **Tested.** 78 automated tests cover the scheduling logic (see [Testing PawPal+](#-testing-pawpal)).

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

- **`Task`** is one care activity: title, the pet it belongs to, duration, priority (Low, Medium, or High; a higher number is more urgent), scheduled start time, frequency (once, daily, weekly), and a completed flag. Completing a task creates the next occurrence: a daily task recurs one day after the completion date, and a weekly task keeps its weekday (the next same-weekday slot after today), so a task finished late or early never recurs in the past or drifts to another day.
- **`Pet`** holds a pet's details and its own list of tasks. It adds and removes tasks, lists the pending ones, and completes a task, adding the next occurrence if it recurs.
- **`Owner`** holds the owner's available minutes and a list of pets. `get_all_tasks()` returns every pet's tasks in one list, and `filter_tasks()` narrows that list by pet and/or completion status.
- **`Scheduler`** is the planner. It holds no data of its own and reads everything through the owner's methods, so one plan covers all pets.

How they work together: an `Owner` has many `Pet`s, and each `Pet` has many `Task`s. `Scheduler.generate_plan()` takes one day's pending tasks across all pets (today by default), picks them by priority (earliest time breaks ties) until the owner's available minutes run out, and returns them in time order. `sort_by_time()` orders any list of tasks. `detect_conflicts()` flags tasks whose times overlap, `conflicts_for()` warns about a new task before it is added, and `explain_plan()` writes out the plan, the tasks left out, and any conflicts. The plan respects each task's scheduled time and only flags overlaps; it never moves a task.

`main.py` is a terminal demo of this, and `tests/test_pawpal.py` holds the tests (run with `pytest`).

## 🖥️ Sample Output

The full terminal demo output is shown in the [Demo Walkthrough](#-demo-walkthrough) below. Priority examples are in [Priority-based scheduling](#priority-based-scheduling). Add `--conflict` to include a task that overlaps two others. The scheduler warns about it when the task is added and flags it in the plan (the rest of the output matches the default run):

```bash
python main.py --conflict
```

```
Warning: Vet video call overlaps Morning walk (Mochi).
Warning: Vet video call overlaps Breakfast and medication (Luna).
Today's Schedule for Jordan (90 min available)
============================================================
╭────────┬─────────────────────────────┬───────┬───────┬────────────╮
│ Time   │ Task                        │ Pet   │   Min │ Priority   │
├────────┼─────────────────────────────┼───────┼───────┼────────────┤
│ 07:30  │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │
│ 07:45  │ 🩺 Vet video call           │ Luna  │    20 │ 🔴 High    │
│ 08:00  │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │
│ 18:00  │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │
╰────────┴─────────────────────────────┴───────┴───────┴────────────╯
Total 80 of 90 available minutes. Tasks were chosen by priority (High first), then earliest time, and listed in time order.
Left out: Grooming (Mochi, Low priority, 45 min) did not fit in the remaining time.
Conflict: Morning walk (Mochi, 07:30-08:00) overlaps Vet video call (Luna, 07:45-08:05) [different pets]
Conflict: Vet video call (Luna, 07:45-08:05) overlaps Breakfast and medication (Luna, 08:00-08:10) [same pet]
...
```

## 🧪 Testing PawPal+

Run the test suite from the project folder:

```bash
python -m pytest
```

Add `-v` to list every test by name.

### What the tests cover

The 78 tests in `tests/test_pawpal.py` and `tests/test_formatting.py` check the logic layer (`pawpal_system.py`), covering the normal cases and the edge cases:

- **Sorting:** tasks come back in time order, including tasks on different days, an empty list, and tasks at the same time (original order kept, original list unchanged).
- **Recurring tasks:** a daily task creates the next one for the following day; a weekly task keeps its weekday whether it is completed on time, late, or early; month and year rollover works; a one-time task creates nothing; completing a task twice does not create duplicates; weekly tasks are also checked when completed exactly a week late and 100,000 weeks late.
- **Editing and removing:** a removed task leaves the pet's list and the owner's view, removing a task that isn't there raises an error, and retiming, moving to another day, or removing a task clears its conflict.
- **Conflict detection:** overlapping tasks are flagged as warnings, including tasks at the exact same time (same pet or different pets), overlaps across midnight, and one long task overlapping two short ones. Back-to-back tasks, completed tasks, and tasks on other days are not flagged.
- **Filtering:** by pet, by completion status, and by both; an unknown pet returns an empty list.
- **Planning:** the plan combines every pet's tasks for one day, picks by priority within the available minutes, breaks ties by earliest time, leaves out what doesn't fit and explains why.
- **Priority scheduling:** the three levels and their labels, priority-first then time ordering, high priority winning when time is short, and priority names in the plan explanation.
- **Output formatting:** priority and status badges, emojis chosen from title keywords, table rows, and the boxed table (including the empty case).
- **Next available slot:** the first free gap, skipping busy time, tasks that touch, completed tasks, and the ignored task; no slot when the day is full or the task is too long.
- **Saving and loading:** a save and reload keeps everything (including times and completed flags), loaded data plans the same as the original, a missing file returns nothing, and damaged files raise a clear error.
- **Empty cases:** a pet with no tasks, an owner with no pets, and zero available minutes do not crash.

### Sample test output

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\biora\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 78 items

tests\test_formatting.py ......                                          [  7%]
tests\test_pawpal.py ................................................... [ 73%]
.....................                                                    [100%]

============================= 78 passed in 0.40s ==============================
```

### Confidence level: ★★★★☆ (4 out of 5)

I'm fairly confident the scheduling logic is reliable: all 78 tests pass, and they cover the main behaviors and the edge cases that were most likely to break, including one real bug the tests found (duplicate recurring tasks). I stopped short of five stars because:

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
| Priority scheduling | `Priority`, `Scheduler.sort_by_priority()`, `generate_plan()` | High priority first, then earliest time; wins when time is short |
| Next available slot | `Scheduler.find_next_free_slot()` | Earliest gap in the day that fits a task of a given length |

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

### Priority-based scheduling

Every task has a priority level: `Priority.LOW` (1), `Priority.MEDIUM` (2), or `Priority.HIGH` (3). The levels are plain integers, so a higher number is more urgent, and `Task.priority_label` turns a number back into the word.

`Scheduler.sort_by_priority(tasks)` returns a new list ordered by priority first (High, then Medium, then Low) and by start time second, so two High tasks are ordered by time. `generate_plan()` uses it: it works down that list, adding each task that still fits in the owner's available minutes, and then shows the chosen tasks in time order. That means priority decides **what gets planned**, and time decides **the order it is shown in**.

CLI example, the default run with 90 minutes. Grooming (Low, 15:00) is left out because it doesn't fit, and in the priority sort Play session (Medium, 18:00) comes before Grooming (Low, 15:00) even though Grooming is earlier:

```bash
python main.py
```

```
Today's Schedule for Jordan (90 min available)
============================================================
╭────────┬─────────────────────────────┬───────┬───────┬────────────╮
│ Time   │ Task                        │ Pet   │   Min │ Priority   │
├────────┼─────────────────────────────┼───────┼───────┼────────────┤
│ 07:30  │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │
│ 08:00  │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │
│ 18:00  │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │
╰────────┴─────────────────────────────┴───────┴───────┴────────────╯
Total 60 of 90 available minutes. Tasks were chosen by priority (High first), then earliest time, and listed in time order.
Left out: Grooming (Mochi, Low priority, 45 min) did not fit in the remaining time.

Sorted by priority, then time
╭───────────┬─────────────────────────────┬───────┬───────┬────────────┬────────────╮
│ Time      │ Task                        │ Pet   │   Min │ Priority   │ Status     │
├───────────┼─────────────────────────────┼───────┼───────┼────────────┼────────────┤
│ Tue 07:30 │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │ ⏳ Pending │
│ Tue 08:00 │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │ ⏳ Pending │
│ Tue 18:00 │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │ ⏳ Pending │
│ Tue 15:00 │ 🧼 Grooming                 │ Mochi │    45 │ 🟢 Low     │ ⏳ Pending │
╰───────────┴─────────────────────────────┴───────┴───────┴────────────┴────────────╯
```

CLI example with only 40 minutes (`--minutes 40`). Priority now decides which tasks make the plan: both High tasks fit, and the Medium and Low tasks are left out:

```bash
python main.py --minutes 40
```

```
Today's Schedule for Jordan (40 min available)
============================================================
╭────────┬─────────────────────────────┬───────┬───────┬────────────╮
│ Time   │ Task                        │ Pet   │   Min │ Priority   │
├────────┼─────────────────────────────┼───────┼───────┼────────────┤
│ 07:30  │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │
│ 08:00  │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │
╰────────┴─────────────────────────────┴───────┴───────┴────────────╯
Total 40 of 40 available minutes. Tasks were chosen by priority (High first), then earliest time, and listed in time order.
Left out: Grooming (Mochi, Low priority, 45 min) did not fit in the remaining time.
Left out: Play session (Luna, Medium priority, 20 min) did not fit in the remaining time.
```

### Next available slot

`Scheduler.find_next_free_slot(duration_minutes, day=None, after=None, ignore=None)` returns the earliest start time on a day with enough free time for a task, or `None` if there is no room. It looks between 06:00 and 22:00 (`DAY_START` and `DAY_END`), and not before `after` if given.

How it works: it sorts the day's pending tasks by start time and keeps a cursor at the end of everything seen so far. The first gap before the next task (or before the end of the day) that is long enough is the answer, and tasks that touch leave no gap. `ignore` leaves one task out, so an existing task can ask where it could move to. It costs O(n log n) for the sort plus one pass.

The app uses it in the conflict box: for each clashing task it suggests, for example, "Move 'Vet video call' (Luna) to 08:20, the next free 20 minutes."

## 🎨 Output formatting

The terminal demo (`main.py`) and the Streamlit app share one small presentation module, `formatting.py`, so tasks look the same everywhere. It only changes how tasks are displayed, not how they are scheduled.

| Feature | Function | Example |
|---------|----------|---------|
| Color-coded priority | `priority_badge()` | 🟢 Low, 🟡 Medium, 🔴 High |
| Status indicator | `status_badge()` | ✅ Done, ⏳ Pending |
| Emoji for the kind of task | `task_emoji()` | 🦮 walk, 🍖 feeding, 💊 medication, 🩺 vet, 🧼 grooming, 🎾 play, 🎓 training, 🐾 anything else |
| Table rows with badges applied | `task_rows()` | one row per task |
| Boxed CLI table | `tasks_table()` | the tables in the sample output |

- **Library:** [`tabulate`](https://pypi.org/project/tabulate/) draws the tables (`tablefmt="rounded_outline"`). It is installed as `tabulate[widechars]`, which adds `wcwidth` so emojis line up correctly in the columns. It is listed in `requirements.txt`.
- **Task emojis are guessed from the title.** Tasks have no "type" field, so `task_emoji()` looks for keywords such as "walk", "feed", or "vet" in the title (not case sensitive) and falls back to 🐾.
- **Scheduler notes:** `Scheduler.plan_notes()` returns the summary lines under a plan (minutes used, tasks left out, conflicts) so the demo can print them below a table.
- **In the app:** the task and plan tables use the same badges and emojis, there is a **Sort by** dropdown (time, or priority then time), overlapping rows are marked "⚠️ overlap", and messages use `st.success`, `st.warning`, `st.info`, and `st.metric`.
- **Terminal output:** `main.py` switches standard output to UTF-8, so the emojis print correctly even when the output is redirected to a file.

Files modified: `formatting.py` (new), `main.py`, `app.py`, `pawpal_system.py` (`Priority`, `plan_notes`), `requirements.txt`, and `tests/test_formatting.py` (new).

## 💾 Data persistence

PawPal+ remembers your pets and tasks between runs by saving them to a `data.json` file next to `app.py`.

### Workflow

1. **Start:** the app calls `Owner.load_from_json("data.json")`. If the file doesn't exist yet (first run), it starts with an empty owner.
2. **Use the app:** add pets, add or edit tasks, mark tasks complete. These changes happen in memory on the `Owner` object.
3. **Save:** at the end of every interaction the app calls `owner.save_to_json("data.json")`, so the file always matches what you see.
4. **Next run:** the app loads the file again and everything is back, including task times, repeat settings, and which tasks are done.

Safety details:
- **Safe writes:** the file is written to `data.json.tmp` first and then swapped in, so a crash mid-save can't leave a half-written file.
- **Unreadable file:** if `data.json` is damaged, `load_from_json` raises a clear `ValueError`. The app keeps the bad file as `data.json.bak`, shows a warning, and starts fresh instead of crashing.
- **Not in git:** `data.json`, `data.json.bak`, and `data.json.tmp` are in `.gitignore`, because they are your personal data.
- **Other location:** set the `PAWPAL_DATA_FILE` environment variable to use a different file.

### How objects become JSON

JSON only holds plain values (text, numbers, true/false, lists, dictionaries), so each class converts itself with a small custom dictionary conversion instead of an extra library:

- `Task.to_dict()`, `Pet.to_dict()`, and `Owner.to_dict()` return plain dictionaries. A `datetime` becomes an ISO string such as `"2026-10-27T07:30:00"`, and an owner's dictionary contains its pets, each of which contains its tasks.
- `Task.from_dict()`, `Pet.from_dict()`, and `Owner.from_dict()` rebuild the objects, turning the ISO string back into a `datetime` and checking each field's type.
- `Owner.save_to_json()` and `Owner.load_from_json()` add the file handling on top.

A saved `data.json` looks like this (the real file puts each field on its own line):

```json
{
  "name": "Jordan",
  "available_minutes": 90,
  "pets": [
    {
      "name": "Mochi", "species": "dog", "age": 3, "notes": "",
      "tasks": [
        {"title": "Morning walk", "pet_name": "Mochi", "duration_minutes": 30,
         "priority": 3, "scheduled_time": "2026-10-27T07:30:00",
         "frequency": "daily", "completed": false}
      ]
    }
  ]
}
```

For a project this size, hand-written `to_dict` and `from_dict` methods are short and easy to follow. A library such as marshmallow becomes worthwhile when there are many classes or the validation rules get complicated.

### Files modified for persistence

| File | Change |
|------|--------|
| `pawpal_system.py` | Added `to_dict` and `from_dict` to `Task`, `Pet`, and `Owner`, plus `Owner.save_to_json()` and `Owner.load_from_json()` |
| `app.py` | Loads the saved owner at startup, saves after every interaction, backs up an unreadable file, supports `PAWPAL_DATA_FILE` |
| `tests/test_pawpal.py` | Round-trip, missing-file, overwrite, and invalid-data tests |
| `.gitignore` | Ignores the saved data files |
| `diagrams/uml.mmd`, `diagrams/uml_final.mmd` | Show the new methods |

## 📸 Demo Walkthrough

PawPal+ has a Streamlit app for everyday use and a terminal demo (`main.py`) that exercises the same logic. Start the app with `streamlit run app.py`.

### What you can do in the app

- **Owner:** set the owner's name and how many minutes are available today.
- **Add a Pet:** enter a name, species, and age. A duplicate or empty name shows an error, and the pet list updates immediately.
- **Add a Task:** choose a pet, then set the title, duration, priority, start time, and whether it repeats (once, daily, weekly).
- **Your Tasks:** see every pet's tasks sorted by time or by priority (the **Sort by** dropdown), with colored priorities and a pending or done status. Filter by pet and by status. Overlapping tasks are marked "⚠️ overlap", and a single warning box above the table names each conflicting pair and points you to **Edit or remove a task** to fix it. It also suggests the next free time slot for the clashing task.
- **Edit or remove a task:** pick any task, change its title, duration, priority, date, start time, or repeat setting and save, or remove it. Moving a task to another day takes it out of today's plan. Conflict warnings update right away.
- **Mark a task complete:** pick a task and complete it. Daily and weekly tasks create their next occurrence, and the app tells you the day it lands on.
- **Generate schedule:** see today's plan with the number of tasks planned and minutes used, plus a **Why this plan?** explanation.

- **Everything is saved:** close the app and open it again, and your pets and tasks are still there.

### Example workflow

1. Jordan has 90 minutes available today. In **Add a Pet**, Jordan adds Mochi (dog) and Luna (cat).
2. In **Add a Task**, Jordan adds a daily "Morning walk" for Mochi at 07:30 (high priority, 30 min), a daily "Breakfast and medication" for Luna at 08:00 (high, 10 min), a weekly "Grooming" for Mochi at 15:00 (low, 45 min), and a one-time "Play session" for Luna at 18:00 (medium, 20 min).
3. **Your Tasks** lists all four sorted by time. Filtering by Luna shows only her two tasks.
4. Jordan clicks **Generate schedule**. The plan has three tasks (60 of 90 minutes) in time order, and **Why this plan?** says Grooming was left out because it didn't fit.
5. Jordan adds a "Vet video call" for Luna at 07:45. A warning appears saying it overlaps the Morning walk and the Breakfast task, and those rows are marked "⚠️ overlap". Jordan opens **Edit or remove a task**, moves the vet call to 09:00, and the warning and the "⚠️ overlap" marks disappear.
6. After the walk, Jordan completes "Morning walk" under **Mark a task complete**. The app confirms that tomorrow's walk was created.

### Scheduler behaviors shown

- **Sorting:** tasks added in any order always display in time order.
- **Filtering:** by pet, by status, or both.
- **Priority planning within a time budget:** high-priority tasks are planned first, and what doesn't fit is reported.
- **Conflict warnings:** same-time and partly overlapping tasks are flagged for the same pet or different pets, and the program keeps running.
- **Recurrence:** completing a daily task schedules the next day's; a weekly task stays on its weekday.

### Sample CLI output

The terminal demo adds tasks in reverse time order on purpose, then shows the plan, the views sorted by time and by priority, the filtered views, a recurring task being completed, and conflict warnings for two tasks at the same time (one pair for the same pet, one pair for different pets):

```bash
python main.py
```

```
Today's Schedule for Jordan (90 min available)
============================================================
╭────────┬─────────────────────────────┬───────┬───────┬────────────╮
│ Time   │ Task                        │ Pet   │   Min │ Priority   │
├────────┼─────────────────────────────┼───────┼───────┼────────────┤
│ 07:30  │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │
│ 08:00  │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │
│ 18:00  │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │
╰────────┴─────────────────────────────┴───────┴───────┴────────────╯
Total 60 of 90 available minutes. Tasks were chosen by priority (High first), then earliest time, and listed in time order.
Left out: Grooming (Mochi, Low priority, 45 min) did not fit in the remaining time.

All tasks in the order they were added (grouped by pet)
╭───────────┬─────────────────────────────┬───────┬───────┬────────────┬────────────╮
│ Time      │ Task                        │ Pet   │   Min │ Priority   │ Status     │
├───────────┼─────────────────────────────┼───────┼───────┼────────────┼────────────┤
│ Tue 15:00 │ 🧼 Grooming                 │ Mochi │    45 │ 🟢 Low     │ ⏳ Pending │
│ Tue 07:30 │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │ ⏳ Pending │
│ Tue 18:00 │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │ ⏳ Pending │
│ Tue 08:00 │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │ ⏳ Pending │
╰───────────┴─────────────────────────────┴───────┴───────┴────────────┴────────────╯

Sorted by time
╭───────────┬─────────────────────────────┬───────┬───────┬────────────┬────────────╮
│ Time      │ Task                        │ Pet   │   Min │ Priority   │ Status     │
├───────────┼─────────────────────────────┼───────┼───────┼────────────┼────────────┤
│ Tue 07:30 │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │ ⏳ Pending │
│ Tue 08:00 │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │ ⏳ Pending │
│ Tue 15:00 │ 🧼 Grooming                 │ Mochi │    45 │ 🟢 Low     │ ⏳ Pending │
│ Tue 18:00 │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │ ⏳ Pending │
╰───────────┴─────────────────────────────┴───────┴───────┴────────────┴────────────╯

Sorted by priority, then time
╭───────────┬─────────────────────────────┬───────┬───────┬────────────┬────────────╮
│ Time      │ Task                        │ Pet   │   Min │ Priority   │ Status     │
├───────────┼─────────────────────────────┼───────┼───────┼────────────┼────────────┤
│ Tue 07:30 │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │ ⏳ Pending │
│ Tue 08:00 │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │ ⏳ Pending │
│ Tue 18:00 │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │ ⏳ Pending │
│ Tue 15:00 │ 🧼 Grooming                 │ Mochi │    45 │ 🟢 Low     │ ⏳ Pending │
╰───────────┴─────────────────────────────┴───────┴───────┴────────────┴────────────╯

Completed 'Morning walk'; its next occurrence was added.

Filter: Mochi's tasks
╭───────────┬─────────────────┬───────┬───────┬────────────┬────────────╮
│ Time      │ Task            │ Pet   │   Min │ Priority   │ Status     │
├───────────┼─────────────────┼───────┼───────┼────────────┼────────────┤
│ Tue 07:30 │ 🦮 Morning walk │ Mochi │    30 │ 🔴 High    │ ✅ Done    │
│ Tue 15:00 │ 🧼 Grooming     │ Mochi │    45 │ 🟢 Low     │ ⏳ Pending │
│ Wed 07:30 │ 🦮 Morning walk │ Mochi │    30 │ 🔴 High    │ ⏳ Pending │
╰───────────┴─────────────────┴───────┴───────┴────────────┴────────────╯

Filter: pending tasks
╭───────────┬─────────────────────────────┬───────┬───────┬────────────┬────────────╮
│ Time      │ Task                        │ Pet   │   Min │ Priority   │ Status     │
├───────────┼─────────────────────────────┼───────┼───────┼────────────┼────────────┤
│ Tue 08:00 │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │ ⏳ Pending │
│ Tue 15:00 │ 🧼 Grooming                 │ Mochi │    45 │ 🟢 Low     │ ⏳ Pending │
│ Tue 18:00 │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │ ⏳ Pending │
│ Wed 07:30 │ 🦮 Morning walk             │ Mochi │    30 │ 🔴 High    │ ⏳ Pending │
╰───────────┴─────────────────────────────┴───────┴───────┴────────────┴────────────╯

Filter: done tasks
╭───────────┬─────────────────┬───────┬───────┬────────────┬──────────╮
│ Time      │ Task            │ Pet   │   Min │ Priority   │ Status   │
├───────────┼─────────────────┼───────┼───────┼────────────┼──────────┤
│ Tue 07:30 │ 🦮 Morning walk │ Mochi │    30 │ 🔴 High    │ ✅ Done  │
╰───────────┴─────────────────┴───────┴───────┴────────────┴──────────╯

Filter: Luna's pending tasks
╭───────────┬─────────────────────────────┬───────┬───────┬────────────┬────────────╮
│ Time      │ Task                        │ Pet   │   Min │ Priority   │ Status     │
├───────────┼─────────────────────────────┼───────┼───────┼────────────┼────────────┤
│ Tue 08:00 │ 🍖 Breakfast and medication │ Luna  │    10 │ 🔴 High    │ ⏳ Pending │
│ Tue 18:00 │ 🎾 Play session             │ Luna  │    20 │ 🟡 Medium  │ ⏳ Pending │
╰───────────┴─────────────────────────────┴───────┴───────┴────────────┴────────────╯

Conflict check: no tasks yet
  no conflicts

Conflict check: two pairs of tasks at the same time
  Warning: Grooming (Mochi, 15:00-15:45) overlaps Vet checkup (Mochi, 15:00-15:30) [same pet]
  Warning: Training class (Mochi, 18:00-18:30) overlaps Play session (Luna, 18:00-18:20) [different pets]
```

The weekdays depend on the day you run it.
