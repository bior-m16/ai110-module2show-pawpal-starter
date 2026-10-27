from datetime import datetime

from formatting import priority_badge, status_badge, task_emoji, task_rows, tasks_table
from pawpal_system import Task


def make_task(title="Morning walk", priority=3, completed=False) -> Task:
    return Task(title, "Mochi", 30, priority, datetime(2026, 10, 27, 7, 30), completed=completed)


def test_priority_badges_are_color_coded():
    assert priority_badge(1) == "🟢 Low"
    assert priority_badge(2) == "🟡 Medium"
    assert priority_badge(3) == "🔴 High"
    assert priority_badge(9) == "⚪ 9"   # unknown numbers don't crash


def test_status_badge_shows_done_or_pending():
    assert status_badge(make_task(completed=True)) == "✅ Done"
    assert status_badge(make_task(completed=False)) == "⏳ Pending"


def test_task_emoji_is_chosen_from_keywords_in_the_title():
    assert task_emoji("Morning walk") == "🦮"
    assert task_emoji("Breakfast and medication") == "🍖"   # first matching group wins
    assert task_emoji("Give MEDICATION") == "💊"             # not case sensitive
    assert task_emoji("Vet checkup") == "🩺"
    assert task_emoji("Grooming") == "🧼"
    assert task_emoji("Play session") == "🎾"
    assert task_emoji("Something unusual") == "🐾"           # default


def test_task_rows_include_badges_and_optional_columns():
    row = task_rows([make_task()], show_date=True)[0]

    assert row["Time"] == "Tue 07:30"
    assert row["Task"] == "🦮 Morning walk"
    assert row["Priority"] == "🔴 High"
    assert row["Status"] == "⏳ Pending"
    assert set(task_rows([make_task()], show_status=False)[0]) == {"Time", "Task", "Pet", "Min", "Priority"}
    assert task_rows([make_task()])[0]["Time"] == "07:30"


def test_tasks_table_is_a_boxed_table_with_headers_and_every_task():
    table = tasks_table([make_task("Morning walk"), make_task("Play session", priority=2)])

    for text in ("Time", "Task", "Pet", "Min", "Priority", "Status", "Morning walk", "Play session", "🟡 Medium"):
        assert text in table
    assert table.splitlines()[0].startswith("╭") and table.splitlines()[-1].startswith("╰")


def test_tasks_table_for_no_tasks_says_none():
    assert tasks_table([]) == "(none)"
