# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial design is built around what a pet owner needs: to add one or more pets, give each pet its own tasks, and track those tasks so they don't have to keep everything in their head. Each pet is its own instance with its own task list, so "walk Max" and "walk Luna" stay separate. I used four classes:

- **Owner**: Holds the owner's name and daily available time, and keeps the list of pets. It can add and remove pets and gather tasks across all of them.
- **Pet**: Holds the pet's details (name, species, age, notes) and owns its own list of tasks. It can add and remove tasks, report which are still pending, and complete a task (adding the next occurrence if it recurs).
- **Task**: Represents one care activity, with a title, the name of the pet it belongs to, duration, priority, scheduled time (a datetime so start times can be compared for overlaps), frequency (once, daily, weekly), and a completed flag. It can mark itself complete, which is how progress is tracked; for a recurring task this returns the next occurrence, and for a one-time task it returns nothing.
- **Scheduler**: Takes an owner and builds the daily plan from all pets' tasks. It orders them by priority and time, fits them into the available time, flags conflicts as pairs of overlapping tasks, and explains why the plan looks the way it does. It doesn't store data itself; it only reads from the owner.

Relationships: an Owner owns many Pets and a Pet owns many Tasks (composition, since neither exists without its parent), and the Scheduler works on an Owner. Tasks carry their pet's name so the plan can still tell which pet each task is for after the tasks are gathered into one list.



**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

After writing the class skeleton in `pawpal_system.py`, I reviewed it for missing relationships and logic bottlenecks and made three changes:

1. **Added `Pet.complete_task(task)`.** `Task.mark_complete()` returns the next occurrence of a recurring task, but a `Task` has no link back to its `Pet`, so nothing would have added that new task to the pet's list. `Pet` now owns that step: it marks the task done and adds the next occurrence.
2. **`Scheduler.detect_conflicts()` now takes a list of tasks.** With no argument it was unclear which tasks it checked (all of them, or only the final plan). Passing the tasks in makes it reusable on either.
3. **`Scheduler.explain_plan()` now takes the plan.** The Scheduler is meant to hold no data, so it can't remember the plan it last built. Passing the plan in keeps it stateless and lets the explanation be rebuilt from each task's priority and time.

Issues I noticed during that review and how I settled them when implementing the classes:
- **`pet_name` duplicates the pet's name.** `Pet.add_task()` now sets it, and `Owner.add_pet()` sets it on any tasks a pet already has. It can still go stale if a pet is renamed later.
- **`priority` meaning.** It is an `int` where a higher number is more urgent (1 = low, 2 = medium, 3 = high). The Streamlit UI uses low/medium/high, so it will need to map those to numbers.
- **`scheduled_time` role.** It is the task's start time. The plan respects it and only flags overlaps; the Scheduler never moves a task.
- **Conflict checking cost.** `detect_conflicts()` sorts by time and compares neighbors instead of checking every pair, which avoids O(n²) comparisons in the common case.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI for design brainstorming first, then for writing code and tests. Before any code, I asked it to brainstorm which classes and responsibilities fit best, and it proposed Owner, Pet, Task, and Scheduler, with the Scheduler holding no data of its own. It later reviewed my class skeleton and suggested three changes: a `Pet.complete_task()` method so the next occurrence of a recurring task gets added to the right pet, passing a task list into `detect_conflicts()`, and passing the plan into `explain_plan()`. It also suggested renaming `due_time` to `scheduled_time`, because the field is a start time used to find overlaps, not a deadline. Finally it implemented the four classes, wrote `main.py`, and drafted the first two tests.

The most helpful prompts asked it to brainstorm before executing, and to review something I already had ("any missing relationships or logic bottlenecks?"). Giving it a specific requirement, such as the Scheduler reading from the Owner's all-tasks method, kept it from taking a shortcut.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I accepted most of its design suggestions after reading them: adding `pet_name` to `Task`, the three skeleton fixes, and the `scheduled_time` rename. I did not take everything as written. I asked it to brainstorm and agree on the classes before it touched my files, and I held off on committing and pushing until I had checked its work.

Two of its outputs needed correcting after I checked them. First, it wrote a nested generic return type for `detect_conflicts()` in the UML. When I pasted the diagram into the Mermaid Live Editor it rendered wrongly as `list<tuple>Task,Task<>`, so the type was simplified to `list~tuple~`. Second, its first tests passed with `python -m pytest` but the plain `pytest` command in my README failed to import `pawpal_system`, so a `pytest.ini` was added to fix that.

I verified the results by running them: rendering the diagram, running `main.py` with and without the overlapping `--conflict` task to see the conflict lines, and running pytest myself and getting the same two passing tests.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
