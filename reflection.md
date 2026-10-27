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

After the first implementation I reviewed `main.py` and the logic it calls, and made a second round of improvements:

- **Fixed a bug where tomorrow's recurring task appeared in today's plan.** `generate_plan()` now takes a day (today by default) and only plans tasks on that day.
- **Fixed recurrence for late completion.** A daily task now recurs one day after the completion date, so it can't land in the past. A weekly task keeps its weekday: the next one is the first same-weekday slot after today, so a Tuesday task finished on Thursday still recurs on a Tuesday.
- **Added `Scheduler.sort_by_time()` and `Owner.filter_tasks()`** so sorting and filtering by pet and status are reusable instead of being done by hand in each place.
- **Added `Scheduler.conflicts_for(task)`** so the UI can warn about an overlap when a task is added, not only after the plan is built.

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

The scheduler considers the owner's available minutes, each task's priority, and its scheduled time. I ranked priority first, because a missed medication matters more than a missed play session. Time available came next, as the hard limit on what fits. Scheduled time breaks ties and sets the order the plan is shown in.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler picks tasks greedily by priority and never moves a task; it only flags overlaps. That can leave out a low-priority task that a different combination would have fit, and it leaves conflicts for the owner to resolve. This is reasonable here because the owner chose those times, the logic stays simple to explain, and a pet care day has few tasks.

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

I accepted its design suggestions after reading them: adding `pet_name` to `Task`, the three skeleton fixes, and the `scheduled_time` rename. I did not reject any of them, but I revised the design before implementing it. I asked it to brainstorm and agree on the classes before it touched my files, reviewed the skeleton for missing relationships, and made those changes first, so the implementation started from a design I had already checked.

Two of its outputs needed correcting after I checked them. First, it wrote a nested generic return type for `detect_conflicts()` in the UML. When I pasted the diagram into the Mermaid Live Editor it rendered wrongly as `list<tuple>Task,Task<>`, so the type was simplified to `list~tuple~`. Second, its first tests passed with `python -m pytest` but the plain `pytest` command in my README failed to import `pawpal_system`, so a `pytest.ini` was added to fix that.

I verified the results by running them: rendering the diagram, running `main.py` with and without the overlapping `--conflict` task to see the conflict lines, and running pytest myself and getting the same two passing tests.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I wrote two pytest tests: completing a task changes its status, and adding a task to a pet increases its task count. They cover the basic building blocks the scheduler depends on. I also ran `main.py`, with and without an overlapping task, to see the plan, the left-out task, and the conflict lines.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident in the basics, but only moderately confident in the scheduler, because pytest doesn't cover it yet and I've only checked it by running one scenario. Next I would test recurring tasks (daily and weekly), a pet with no tasks, an owner with no pets, tasks that don't fit the available time, tasks that touch end-to-start without overlapping, and equal priorities.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied that the Scheduler plans across all pets through `Owner.get_all_tasks()`, and that the design held up well when I turned the UML into code.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would connect the logic to the Streamlit UI, add tests for the scheduler, and replace the `pet_name` string on `Task` with a real link to its `Pet` so a rename can't leave it stale.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Settling the design before writing code made the implementation much easier, and AI works best when I give it a clear design to build from and then check its output by running it.
