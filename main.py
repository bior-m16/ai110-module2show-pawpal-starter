"""Temporary testing ground: run the PawPal+ logic in the terminal.

Run `python main.py`, or `python main.py --conflict` to add an overlapping task.
"""

import sys
from datetime import datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def at(hour: int, minute: int = 0) -> datetime:
    today = datetime.now()
    return today.replace(hour=hour, minute=minute, second=0, microsecond=0)


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5, notes="Needs medication with food")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "", 30, 3, at(7, 30), "daily"))
    mochi.add_task(Task("Grooming", "", 45, 1, at(15, 0), "weekly"))
    luna.add_task(Task("Breakfast and medication", "", 10, 3, at(8, 0), "daily"))
    luna.add_task(Task("Play session", "", 20, 2, at(18, 0)))

    if "--conflict" in sys.argv:
        luna.add_task(Task("Vet video call", "", 20, 3, at(7, 45)))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    print(f"Today's Schedule for {owner.name} ({owner.available_minutes} min available)")
    print("=" * 60)
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
