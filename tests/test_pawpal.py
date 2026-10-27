from datetime import datetime

from pawpal_system import Pet, Task


def make_task(title: str = "Morning walk") -> Task:
    return Task(
        title=title,
        pet_name="Mochi",
        duration_minutes=30,
        priority=3,
        scheduled_time=datetime(2026, 10, 27, 7, 30),
    )


def test_mark_complete_changes_task_status():
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(make_task("Morning walk"))
    assert len(pet.tasks) == 1

    pet.add_task(make_task("Evening walk"))
    assert len(pet.tasks) == 2
