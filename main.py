"""Temporary testing ground: run the PawPal+ logic in the terminal.

Run `python main.py`. Options:
  --minutes N   how many minutes the owner has today (default 90); a small number shows
                high-priority tasks winning when time is short
  --conflict    add a task that overlaps two others
"""

import argparse
import sys
from datetime import datetime

from formatting import tasks_table
from pawpal_system import Owner, Pet, Scheduler, Task


def at(hour: int, minute: int = 0) -> datetime:
    today = datetime.now()
    return today.replace(hour=hour, minute=minute, second=0, microsecond=0)


def show(heading: str, tasks: list[Task], **table_options) -> None:
    print(f"\n{heading}")
    print(tasks_table(tasks, **table_options))


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
    sys.stdout.reconfigure(encoding="utf-8")  # so emojis print on any terminal, even when redirected
    parser = argparse.ArgumentParser(description="PawPal+ terminal demo")
    parser.add_argument("--minutes", type=int, default=90, help="minutes available today")
    parser.add_argument("--conflict", action="store_true", help="add a task that overlaps two others")
    args = parser.parse_args()

    owner = Owner(name="Jordan", available_minutes=args.minutes)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5, notes="Needs medication with food")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)

    # Added on purpose in reverse time order, mixed across pets and priorities.
    luna.add_task(Task("Play session", "", 20, 2, at(18, 0)))
    mochi.add_task(Task("Grooming", "", 45, 1, at(15, 0), "weekly"))
    luna.add_task(Task("Breakfast and medication", "", 10, 3, at(8, 0), "daily"))
    walk = Task("Morning walk", "", 30, 3, at(7, 30), "daily")
    mochi.add_task(walk)

    if args.conflict:
        vet_call = Task("Vet video call", "", 20, 3, at(7, 45))
        for clash in scheduler.conflicts_for(vet_call):
            print(f"Warning: Vet video call overlaps {clash.title} ({clash.pet_name}).")
        luna.add_task(vet_call)

    plan = scheduler.generate_plan()

    print(f"Today's Schedule for {owner.name} ({owner.available_minutes} min available)")
    print("=" * 60)
    print(tasks_table(plan, show_status=False))
    for note in scheduler.plan_notes(plan):
        print(note)

    everything = owner.get_all_tasks()
    show("All tasks in the order they were added (grouped by pet)", everything, show_date=True)
    show("Sorted by time", scheduler.sort_by_time(everything), show_date=True)
    show("Sorted by priority, then time", scheduler.sort_by_priority(everything), show_date=True)

    mochi.complete_task(walk)
    print(f"\nCompleted '{walk.title}'; its next occurrence was added.")

    for heading, tasks in [
        ("Filter: Mochi's tasks", owner.filter_tasks(pet_name="Mochi")),
        ("Filter: pending tasks", owner.filter_tasks(completed=False)),
        ("Filter: done tasks", owner.filter_tasks(completed=True)),
        ("Filter: Luna's pending tasks", owner.filter_tasks(pet_name="Luna", completed=False)),
    ]:
        show(heading, scheduler.sort_by_time(tasks), show_date=True)

    demo_same_time_warnings()


if __name__ == "__main__":
    main()
