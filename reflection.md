# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial design is built around what a pet owner needs: to add one or more pets, give each pet its own tasks, and track those tasks so they don't have to keep everything in their head. Each pet is its own instance with its own task list, so "walk Max" and "walk Luna" stay separate. I used four classes:

- **Owner**: Holds the owner's name and daily available time, and keeps the list of pets. It can add and remove pets and gather tasks across all of them.
- **Pet**: Holds the pet's details (name, species, age, notes) and owns its own list of tasks. It can add and remove tasks and report which are still pending.
- **Task**: Represents one care activity, with a title, the name of the pet it belongs to, duration, priority, scheduled time (a datetime so start times can be compared for overlaps), frequency (once, daily, weekly), and a completed flag. It can mark itself complete, which is how progress is tracked; for a recurring task this returns the next occurrence, and for a one-time task it returns nothing.
- **Scheduler**: Takes an owner and builds the daily plan from all pets' tasks. It orders them by priority and time, fits them into the available time, flags conflicts as pairs of overlapping tasks, and explains why the plan looks the way it does. It doesn't store data itself; it only reads from the owner.

Relationships: an Owner owns many Pets and a Pet owns many Tasks (composition, since neither exists without its parent), and the Scheduler works on an Owner. Tasks carry their pet's name so the plan can still tell which pet each task is for after the tasks are gathered into one list.



**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

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

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
