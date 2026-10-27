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


def test_weekly_task_completed_late_keeps_its_weekday():
    task = make_task(frequency="weekly")  # due Tue Oct 27

    nxt = task.mark_complete(now=at(9, 0, date(2026, 10, 29)))  # completed Thursday

    assert nxt.scheduled_time == at(7, 30, date(2026, 11, 3))
    assert nxt.scheduled_time.weekday() == task.scheduled_time.weekday()


def test_weekly_task_many_weeks_late_lands_on_the_next_same_weekday():
    task = make_task(frequency="weekly")  # due Tue Oct 27, completed Wed Nov 18

    nxt = task.mark_complete(now=at(9, 0, date(2026, 11, 18)))

    assert nxt.scheduled_time == at(7, 30, date(2026, 11, 24))
    assert nxt.scheduled_time.weekday() == task.scheduled_time.weekday()


def test_weekly_task_completed_early_waits_for_next_weeks_slot():
    task = make_task(frequency="weekly")  # due Tue Oct 27, done on Sat Oct 24

    nxt = task.mark_complete(now=at(9, 0, date(2026, 10, 24)))

    assert nxt.scheduled_time == at(7, 30, date(2026, 11, 3))


def test_next_occurrence_is_one_period_after_the_completion_date():
    task = make_task(frequency="daily")  # due Oct 27, completed Oct 30

    nxt = task.mark_complete(now=at(9, 0, date(2026, 10, 30)))

    assert nxt.scheduled_time == at(7, 30, date(2026, 10, 31))


def test_early_completion_is_also_counted_from_today():
    task = make_task(frequency="daily")  # due Oct 27, completed a week early

    nxt = task.mark_complete(now=at(9, 0, date(2026, 10, 20)))

    assert nxt.scheduled_time == at(7, 30, date(2026, 10, 21))


def test_recurrence_crosses_month_and_year_boundaries():
    task = Task("Meds", "Mochi", 5, 3, datetime(2026, 12, 31, 8, 0), "daily")

    nxt = task.mark_complete(now=datetime(2026, 12, 31, 9, 0))

    assert nxt.scheduled_time == datetime(2027, 1, 1, 8, 0)


def test_next_occurrence_is_a_new_task_and_keeps_the_details():
    task = make_task(frequency="daily")

    nxt = task.mark_complete(now=at(8))

    assert nxt is not task
    assert (nxt.title, nxt.pet_name, nxt.duration_minutes, nxt.priority, nxt.frequency) == (
        task.title, task.pet_name, task.duration_minutes, task.priority, task.frequency
    )


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


def test_warning_for_two_tasks_at_the_same_time_for_the_same_pet():
    owner, mochi, _ = make_owner()
    mochi.add_task(make_task("Grooming", 15, 0, 45))
    mochi.add_task(make_task("Vet checkup", 15, 0, 30))

    warnings = Scheduler(owner).conflict_warnings()

    assert len(warnings) == 1
    assert warnings[0].startswith("Warning:")
    assert "Grooming" in warnings[0] and "Vet checkup" in warnings[0]
    assert "[same pet]" in warnings[0]


def test_warning_for_two_tasks_at_the_same_time_for_different_pets():
    owner, mochi, luna = make_owner()
    mochi.add_task(make_task("Training", 18, 0, 30))
    luna.add_task(make_task("Play", 18, 0, 20))

    warnings = Scheduler(owner).conflict_warnings()

    assert len(warnings) == 1
    assert "[different pets]" in warnings[0]


def test_no_warnings_when_nothing_overlaps_or_nothing_exists():
    owner, mochi, _ = make_owner()
    scheduler = Scheduler(owner)
    assert scheduler.conflict_warnings() == []  # no tasks at all, must not raise

    mochi.add_task(make_task("a", 8, 0, 30))
    mochi.add_task(make_task("b", 8, 30, 30))  # back to back
    assert scheduler.conflict_warnings() == []


def test_warnings_ignore_completed_tasks_and_other_days():
    owner, mochi, _ = make_owner()
    done = make_task("done", 9, 0, 30)
    mochi.add_task(done)
    done.completed = True
    mochi.add_task(make_task("live", 9, 0, 30))
    mochi.add_task(Task("tomorrow", "Mochi", 30, 3, at(9, 0, date(2026, 10, 28))))

    assert Scheduler(owner).conflict_warnings() == []


def test_conflicts_for_warns_before_a_task_is_added():
    owner, mochi, _ = make_owner()
    walk = make_task("walk", 7, 30, 30)
    mochi.add_task(walk)
    vet = make_task("vet", 7, 45, 20)

    assert Scheduler(owner).conflicts_for(vet) == [walk]
    assert Scheduler(owner).conflicts_for(make_task("later", 12)) == []


# --- edge cases: sorting ----------------------------------------------------

def test_sort_by_time_handles_an_empty_list():
    assert Scheduler.sort_by_time([]) == []


def test_sort_by_time_keeps_order_of_same_time_tasks_and_does_not_mutate():
    first, second = make_task("first", 8), make_task("second", 8)
    original = [second, first]

    ordered = Scheduler.sort_by_time(original)

    assert [t.title for t in ordered] == ["second", "first"]
    assert ordered is not original


def test_sort_by_time_orders_by_date_before_time_of_day():
    tomorrow_early = Task("tomorrow", "Mochi", 10, 1, at(6, 0, date(2026, 10, 28)))

    ordered = Scheduler.sort_by_time([tomorrow_early, make_task("today", 20)])

    assert [t.title for t in ordered] == ["today", "tomorrow"]


# --- edge cases: nothing to schedule ---------------------------------------

def test_pet_with_no_tasks_is_handled_everywhere():
    pet = Pet("Mochi", "dog")
    owner = Owner("Jordan", 60, [pet])
    scheduler = Scheduler(owner)

    assert pet.get_pending_tasks() == []
    assert owner.get_all_tasks() == []
    assert scheduler.generate_plan(DAY) == []
    assert scheduler.conflict_warnings() == []


def test_owner_with_no_pets_and_filter_for_unknown_pet():
    owner = Owner("Jordan", 60)
    assert owner.get_all_tasks() == []
    assert owner.filter_tasks(pet_name="Mochi") == []

    owner.add_pet(Pet("Luna", "cat"))
    assert owner.filter_tasks(pet_name="Mochi") == []


# --- edge cases: planning budget and ties ----------------------------------

def test_plan_with_zero_available_minutes_is_empty():
    owner, mochi, _ = make_owner(available=0)
    mochi.add_task(make_task("walk"))

    assert Scheduler(owner).generate_plan(DAY) == []


def test_plan_includes_a_task_that_exactly_fills_the_budget():
    owner, mochi, _ = make_owner(available=30)
    mochi.add_task(make_task("walk", minutes=30))

    assert [t.title for t in Scheduler(owner).generate_plan(DAY)] == ["walk"]


def test_task_longer_than_the_whole_budget_is_left_out_and_explained():
    owner, mochi, _ = make_owner(available=20)
    mochi.add_task(make_task("long", 8, minutes=60, priority=3))
    mochi.add_task(make_task("short", 9, minutes=10, priority=1))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(DAY)

    assert [t.title for t in plan] == ["short"]
    assert "Left out: long" in scheduler.explain_plan(plan)


def test_equal_priority_tasks_are_chosen_earliest_first():
    owner, mochi, _ = make_owner(available=30)
    mochi.add_task(make_task("later", 9, minutes=30, priority=2))
    mochi.add_task(make_task("earlier", 8, minutes=30, priority=2))

    assert [t.title for t in Scheduler(owner).generate_plan(DAY)] == ["earlier"]


def test_explanation_does_not_list_other_days_as_left_out():
    owner, mochi, _ = make_owner()
    mochi.add_task(make_task("today", 8))
    mochi.add_task(Task("tomorrow", "Mochi", 30, 3, at(8, 0, date(2026, 10, 28))))
    scheduler = Scheduler(owner)

    explanation = scheduler.explain_plan(scheduler.generate_plan(DAY))

    assert "tomorrow" not in explanation


# --- edge cases: exact same time and overlap shapes ------------------------

def test_two_tasks_at_the_exact_same_time_are_both_planned_and_flagged():
    owner, mochi, luna = make_owner()
    mochi.add_task(make_task("walk", 8, 0, 30))
    luna.add_task(make_task("feed", 8, 0, 10))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(DAY)

    assert {t.title for t in plan} == {"walk", "feed"}
    assert "Conflict:" in scheduler.explain_plan(plan)


def test_conflict_across_midnight_is_detected():
    owner, _, _ = make_owner()
    late = Task("late", "Mochi", 60, 1, datetime(2026, 10, 27, 23, 30))
    early = Task("early", "Mochi", 30, 1, datetime(2026, 10, 28, 0, 15))

    assert Scheduler(owner).detect_conflicts([late, early]) == [(late, early)]


def test_long_task_overlapping_two_short_ones_gives_exactly_two_pairs():
    owner, _, _ = make_owner()
    long_task = make_task("long", 8, 0, 120)
    short_a = make_task("a", 8, 30, 15)
    short_b = make_task("b", 9, 0, 30)  # starts after a ends, so a and b don't clash

    conflicts = Scheduler(owner).detect_conflicts([short_b, long_task, short_a])

    assert conflicts == [(long_task, short_a), (long_task, short_b)]


def test_conflicts_for_ignores_completed_tasks():
    owner, mochi, _ = make_owner()
    done = make_task("done", 8, 0, 30)
    mochi.add_task(done)
    done.completed = True

    assert Scheduler(owner).conflicts_for(make_task("new", 8, 15, 30)) == []


# --- edge cases: recurring tasks and tagging --------------------------------

def test_completing_an_already_completed_task_does_not_duplicate_it():
    pet = Pet("Mochi", "dog")
    walk = make_task(frequency="daily")
    pet.add_task(walk)

    pet.complete_task(walk, now=at(8))
    pet.complete_task(walk, now=at(8))

    assert len(pet.tasks) == 2


def test_the_next_occurrence_can_itself_be_completed_and_recurs_again():
    pet = Pet("Mochi", "dog")
    walk = make_task(frequency="daily")
    pet.add_task(walk)
    pet.complete_task(walk, now=at(8))

    pet.complete_task(pet.tasks[1], now=at(8, 0, date(2026, 10, 28)))

    assert [t.scheduled_time.day for t in pet.tasks] == [27, 28, 29]


def test_adding_a_task_tags_it_with_the_pets_name():
    pet = Pet("Luna", "cat")
    task = Task("Feed", "WrongName", 10, 2, at(8))

    pet.add_task(task)

    assert task.pet_name == "Luna"
