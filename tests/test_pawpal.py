from datetime import date, datetime

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2026, 10, 27)


def at(hour: int, minute: int = 0, day: date = DAY) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute)


def make_task(title: str = "Morning walk", hour: int = 7, minute: int = 30,
              minutes: int = 30, priority: int = 3, frequency: str = "once") -> Task:
    return Task(title, "Mochi", minutes, priority, at(hour, minute), frequency)


def make_owner(available: int = 120) -> tuple[Owner, Pet, Pet]:
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner = Owner("Jordan", available)
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


# --- basics -----------------------------------------------------------------

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


# --- sorting ----------------------------------------------------------------

def test_sort_by_time_orders_earliest_first():
    owner, _, _ = make_owner()
    late, early, mid = make_task("late", 18), make_task("early", 7), make_task("mid", 12)

    ordered = Scheduler(owner).sort_by_time([late, early, mid])

    assert [t.title for t in ordered] == ["early", "mid", "late"]


# --- filtering --------------------------------------------------------------

def test_filter_tasks_by_pet_and_status():
    owner, mochi, luna = make_owner()
    walk, feed = make_task("walk"), make_task("feed", 8)
    mochi.add_task(walk)
    luna.add_task(feed)
    feed.completed = True

    assert owner.filter_tasks() == [walk, feed]
    assert owner.filter_tasks(pet_name="Luna") == [feed]
    assert owner.filter_tasks(completed=False) == [walk]
    assert owner.filter_tasks(pet_name="Luna", completed=False) == []


# --- recurring tasks --------------------------------------------------------

def test_once_task_has_no_next_occurrence():
    assert make_task(frequency="once").mark_complete(now=at(8)) is None


def test_daily_task_recurs_next_day():
    task = make_task(frequency="daily")

    nxt = task.mark_complete(now=at(8))

    assert nxt.scheduled_time == at(7, 30, date(2026, 10, 28))
    assert nxt.completed is False


def test_weekly_task_recurs_next_week():
    nxt = make_task(frequency="weekly").mark_complete(now=at(8))

    assert nxt.scheduled_time == at(7, 30, date(2026, 11, 3))


def test_late_completion_rolls_next_occurrence_into_the_future():
    task = make_task(frequency="daily")  # due Oct 27, completed Oct 30

    nxt = task.mark_complete(now=at(9, 0, date(2026, 10, 30)))

    assert nxt.scheduled_time == at(7, 30, date(2026, 10, 31))


def test_pet_complete_task_adds_next_occurrence():
    pet = Pet("Mochi", "dog")
    walk = make_task(frequency="daily")
    pet.add_task(walk)

    pet.complete_task(walk, now=at(8))

    assert len(pet.tasks) == 2
    assert [t.completed for t in pet.tasks] == [True, False]


def test_complete_task_rejects_task_from_another_pet():
    owner, mochi, luna = make_owner()
    walk = make_task()
    mochi.add_task(walk)

    with pytest.raises(ValueError):
        luna.complete_task(walk)


# --- planning ---------------------------------------------------------------

def test_plan_includes_tasks_from_every_pet_in_time_order():
    owner, mochi, luna = make_owner()
    mochi.add_task(make_task("walk", 9))
    luna.add_task(make_task("feed", 8))

    plan = Scheduler(owner).generate_plan(DAY)

    assert [(t.pet_name, t.title) for t in plan] == [("Luna", "feed"), ("Mochi", "walk")]


def test_plan_only_includes_the_requested_day():
    owner, mochi, _ = make_owner()
    walk = make_task(frequency="daily")
    mochi.add_task(walk)
    mochi.complete_task(walk, now=at(8))  # tomorrow's walk is now pending

    plan = Scheduler(owner).generate_plan(DAY)

    assert plan == []
    assert len(Scheduler(owner).generate_plan(date(2026, 10, 28))) == 1


def test_plan_drops_lowest_priority_task_that_does_not_fit():
    owner, mochi, _ = make_owner(available=40)
    mochi.add_task(make_task("meds", 8, minutes=10, priority=3))
    mochi.add_task(make_task("walk", 9, minutes=30, priority=2))
    mochi.add_task(make_task("groom", 10, minutes=30, priority=1))

    plan = Scheduler(owner).generate_plan(DAY)

    assert [t.title for t in plan] == ["meds", "walk"]


def test_plan_skips_completed_tasks():
    owner, mochi, _ = make_owner()
    done = make_task("done")
    mochi.add_task(done)
    done.completed = True

    assert Scheduler(owner).generate_plan(DAY) == []


def test_empty_owner_has_empty_plan_and_explanation():
    scheduler = Scheduler(Owner("Jordan", 60))

    assert scheduler.generate_plan(DAY) == []
    assert scheduler.explain_plan([]) == "No tasks were scheduled."


# --- conflicts --------------------------------------------------------------

def test_detect_conflicts_finds_overlapping_pair():
    owner, mochi, luna = make_owner()
    walk, vet = make_task("walk", 7, 30, 30), make_task("vet", 7, 45, 20)

    assert Scheduler(owner).detect_conflicts([vet, walk]) == [(walk, vet)]


def test_back_to_back_tasks_do_not_conflict():
    owner, _, _ = make_owner()
    first, second = make_task("a", 8, 0, 30), make_task("b", 8, 30, 30)

    assert Scheduler(owner).detect_conflicts([first, second]) == []


def test_conflicts_for_warns_before_a_task_is_added():
    owner, mochi, _ = make_owner()
    walk = make_task("walk", 7, 30, 30)
    mochi.add_task(walk)
    vet = make_task("vet", 7, 45, 20)

    assert Scheduler(owner).conflicts_for(vet) == [walk]
    assert Scheduler(owner).conflicts_for(make_task("later", 12)) == []
