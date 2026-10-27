"""Temporary testing ground: run the PawPal+ logic in the terminal.

Run `python main.py`, or `python main.py --conflict` to add an overlapping task.
"""

import sys
from datetime import datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def at(hour: int, minute: int = 0) -> datetime:
    today = datetime.now()
    return today.replace(hour=hour, minute=minute, second=0, microsecond=0)


def show(heading: str, tasks: list[Task]) -> None:
    print(f"\n{heading}")
    if not tasks:
        print("  (none)")
    for task in tasks:
        status = "done" if task.completed else "pending"
        print(f"  {task.scheduled_time:%a %H:%M} {task.title} ({task.pet_name}, {status})")


def demo_same_time_warnings() -> None:
    """Show conflict warnings for two tasks at the same time, same pet and different pets."""
    owner = Owner(name="Jordan", available_minutes=120)
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    scheduler = Scheduler(owner)

    print("\nConflict check: no tasks yet")
    print(f"  {scheduler.conflict_warnings() or 'no conflicts'}")

    mochi.add_task(Task("Grooming", "", 45, 1, at(15, 0)))
    mochi.add_task(Task("Vet checkup", "", 30, 3, at(15, 0)))  # same pet, same time
    mochi.add_task(Task("Training class", "", 30, 2, at(18, 0)))
    luna.add_task(Task("Play session", "", 20, 2, at(18, 0)))  # different pet, same time
    luna.add_task(Task("Breakfast", "", 10, 3, at(8, 0)))  # no clash

    print("\nConflict check: two pairs of tasks at the same time")
    for warning in scheduler.conflict_warnings():
        print(f"  {warning}")


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5, notes="Needs medication with food")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)

    # Added on purpose in reverse time order, mixed across pets.
    luna.add_task(Task("Play session", "", 20, 2, at(18, 0)))
    mochi.add_task(Task("Grooming", "", 45, 1, at(15, 0), "weekly"))
    luna.add_task(Task("Breakfast and medication", "", 10, 3, at(8, 0), "daily"))
    walk = Task("Morning walk", "", 30, 3, at(7, 30), "daily")
    mochi.add_task(walk)

    if "--conflict" in sys.argv:
        vet_call = Task("Vet video call", "", 20, 3, at(7, 45))
        for clash in scheduler.conflicts_for(vet_call):
            print(f"Warning: Vet video call overlaps {clash.title} ({clash.pet_name}).")
        luna.add_task(vet_call)

    plan = scheduler.generate_plan()

    print(f"Today's Schedule for {owner.name} ({owner.available_minutes} min available)")
    print("=" * 60)
    print(scheduler.explain_plan(plan))

    show("Tasks in the order they were added (grouped by pet):", owner.get_all_tasks())
    show("Sorted by time:", scheduler.sort_by_time(owner.get_all_tasks()))

    mochi.complete_task(walk)
    print(f"\nCompleted '{walk.title}'; its next occurrence was added.")

    show("Filter: Mochi's tasks", scheduler.sort_by_time(owner.filter_tasks(pet_name="Mochi")))
    show("Filter: pending tasks", scheduler.sort_by_time(owner.filter_tasks(completed=False)))
    show("Filter: done tasks", scheduler.sort_by_time(owner.filter_tasks(completed=True)))
    show(
        "Filter: Luna's pending tasks",
        scheduler.sort_by_time(owner.filter_tasks(pet_name="Luna", completed=False)),
    )

    demo_same_time_warnings()


if __name__ == "__main__":
    main()
