import os
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from formatting import priority_badge, task_emoji
from pawpal_system import Owner, Pet, Scheduler, Task

PRIORITY_VALUES = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABELS = {value: label for label, value in PRIORITY_VALUES.items()}

# Where pets and tasks are remembered between runs (set PAWPAL_DATA_FILE to use another file).
DATA_FILE = Path(os.environ.get("PAWPAL_DATA_FILE", Path(__file__).with_name("data.json")))


def show_conflicts(warnings: list[str], suggestions: list[str] = ()) -> None:
    """Show every conflict in one box: what is wrong, which tasks, and what to do about it."""
    if not warnings:
        return
    plural = "s" if len(warnings) > 1 else ""
    details = "\n".join(f"- {w.removeprefix('Warning: ')}" for w in warnings)
    message = (
        f"**{len(warnings)} scheduling conflict{plural}.** You can't do two things at once, "
        f"so change one task in each pair to a different time, or remove it, using "
        f"**Edit or remove a task**.\n\n{details}"
    )
    if suggestions:
        message += "\n\n**Suggestions:**\n" + "\n".join(f"- {s}" for s in suggestions)
    st.warning(message)


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# The "vault": load the saved Owner (or start a new one) once per session and reuse it.
if "owner" not in st.session_state:
    loaded = None
    try:
        loaded = Owner.load_from_json(DATA_FILE)
    except ValueError:
        # Keep the unreadable file as a backup instead of overwriting it.
        os.replace(DATA_FILE, DATA_FILE.with_name(DATA_FILE.name + ".bak"))
        st.session_state.load_warning = (
            f"{DATA_FILE.name} could not be read, so PawPal+ started fresh. "
            f"The old file was kept as {DATA_FILE.name}.bak."
        )
    st.session_state.owner = loaded if loaded is not None else Owner(name="Jordan", available_minutes=90)
owner: Owner = st.session_state.owner

if "load_warning" in st.session_state:
    st.warning(st.session_state.pop("load_warning"))

st.markdown(
    """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time and priority, and explains the plan it builds.
"""
)

st.divider()

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input("Minutes available today", min_value=1, max_value=720, value=owner.available_minutes)
)

st.divider()

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name")
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
    new_age = st.number_input("Age", min_value=0, max_value=40, value=1)
    pet_submitted = st.form_submit_button("Add pet")

if pet_submitted:
    cleaned_name = new_pet_name.strip()
    if not cleaned_name:
        st.error("Please enter a pet name.")
    elif cleaned_name in [pet.name for pet in owner.pets]:
        st.error(f"You already have a pet named {cleaned_name}.")
    else:
        owner.add_pet(Pet(name=cleaned_name, species=new_species, age=int(new_age)))
        st.success(f"Added {cleaned_name}.")

if owner.pets:
    st.table(
        [{"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.tasks)} for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        chosen_pet_name = st.selectbox("Pet", [pet.name for pet in owner.pets])
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", list(PRIORITY_VALUES), index=2)
        col4, col5 = st.columns(2)
        with col4:
            start_time = st.time_input("Start time", value=datetime(2000, 1, 1, 8, 0).time())
        with col5:
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        task_submitted = st.form_submit_button("Add task")

    if task_submitted:
        if not task_title.strip():
            st.error("Please enter a task title.")
        else:
            pet = next(p for p in owner.pets if p.name == chosen_pet_name)
            new_task = Task(
                title=task_title.strip(),
                pet_name=pet.name,
                duration_minutes=int(duration),
                priority=PRIORITY_VALUES[priority],
                scheduled_time=datetime.combine(date.today(), start_time),
                frequency=frequency,
            )
            pet.add_task(new_task)
            st.success(f"Added '{new_task.title}' for {pet.name}.")

st.divider()

st.subheader("Your Tasks")
scheduler = Scheduler(owner)

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

if not owner.get_all_tasks():
    st.info("No tasks yet. Add one above.")
else:
    # Completing a task runs before the table below is drawn, so the table shows the result.
    pending = scheduler.sort_by_time(owner.filter_tasks(completed=False))
    with st.expander("Mark a task complete"):
        if not pending:
            st.write("Everything is done. 🎉")
        else:
            pick = st.selectbox(
                "Task",
                range(len(pending)),
                format_func=lambda i: (
                    f"{pending[i].pet_name}: {pending[i].title} ({pending[i].scheduled_time:%a %H:%M})"
                ),
            )
            if st.button("Mark complete"):
                done_task = pending[pick]
                pet = next(p for p in owner.pets if p.name == done_task.pet_name)
                count_before = len(pet.tasks)
                pet.complete_task(done_task)
                st.success(f"Completed '{done_task.title}' for {pet.name}.")
                if len(pet.tasks) > count_before:
                    nxt = pet.tasks[-1]
                    st.info(f"It repeats {nxt.frequency}: next one is on {nxt.scheduled_time:%A at %H:%M}.")

    with st.expander("Edit or remove a task"):
        # Stable order (by pet, as added) so the selection doesn't jump when a time is edited.
        every_task = owner.get_all_tasks()
        by_id = {id(t): t for t in every_task}
        # The number makes labels unique, so identical-looking tasks can be told apart.
        labels = {
            id(t): f"{n}. {t.pet_name}: {t.title} ({t.scheduled_time:%a %H:%M})"
            for n, t in enumerate(every_task, start=1)
        }
        task_id = st.selectbox("Task to edit", list(by_id), format_func=labels.get)
        task = by_id[task_id]
        edit_pet = next(p for p in owner.pets if p.name == task.pet_name)

        with st.form("edit_task_form"):
            edit_title = st.text_input("Title", value=task.title, key=f"edit_title_{task_id}")
            edit_col1, edit_col2 = st.columns(2)
            with edit_col1:
                edit_duration = st.number_input(
                    "Duration (minutes)", min_value=1, max_value=240,
                    value=task.duration_minutes, key=f"edit_duration_{task_id}",
                )
                edit_time = st.time_input(
                    "Start time", value=task.scheduled_time.time(), key=f"edit_time_{task_id}"
                )
            with edit_col2:
                edit_priority = st.selectbox(
                    "Priority", list(PRIORITY_VALUES), index=task.priority - 1,
                    key=f"edit_priority_{task_id}",
                )
                edit_frequency = st.selectbox(
                    "Repeats", ["once", "daily", "weekly"],
                    index=["once", "daily", "weekly"].index(task.frequency),
                    key=f"edit_frequency_{task_id}",
                )
            edit_date = st.date_input(
                "Date", value=task.scheduled_time.date(), key=f"edit_date_{task_id}"
            )
            edit_saved = st.form_submit_button("Save changes")

        if edit_saved:
            if not edit_title.strip():
                st.error("Please enter a task title.")
            else:
                task.title = edit_title.strip()
                task.duration_minutes = int(edit_duration)
                task.priority = PRIORITY_VALUES[edit_priority]
                task.frequency = edit_frequency
                task.scheduled_time = datetime.combine(edit_date, edit_time)
                st.success(f"Updated '{task.title}' for {task.pet_name}.")

        if st.button("Remove task"):
            edit_pet.remove_task(task)
            st.session_state.flash = f"Removed '{task.title}' from {edit_pet.name}."
            st.rerun()  # redraw so no widget above still lists the removed task

    # Conflicts come first because they are the thing the owner has to act on.
    pending_conflicts = scheduler.detect_conflicts(owner.filter_tasks(completed=False))
    suggestions = []
    for _, clashing in pending_conflicts:
        slot = scheduler.find_next_free_slot(
            clashing.duration_minutes,
            day=clashing.scheduled_time.date(),
            after=clashing.scheduled_time,
            ignore=clashing,
        )
        if slot is None:
            suggestions.append(
                f"No free {clashing.duration_minutes}-minute slot is left for '{clashing.title}' "
                f"on {clashing.scheduled_time:%A}."
            )
        else:
            suggestions.append(
                f"Move '{clashing.title}' ({clashing.pet_name}) to {slot:%H:%M}, "
                f"the next free {clashing.duration_minutes} minutes."
            )
    show_conflicts(scheduler.conflict_warnings(), suggestions)
    conflicting = {id(t) for pair in pending_conflicts for t in pair}

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        pet_filter = st.selectbox("Show pet", ["All"] + [pet.name for pet in owner.pets])
    with filter_col2:
        status_filter = st.selectbox("Show status", ["All", "pending", "done"])
    with filter_col3:
        sort_choice = st.selectbox("Sort by", ["Time", "Priority, then time"])

    shown = owner.filter_tasks(
        pet_name=None if pet_filter == "All" else pet_filter,
        completed={"All": None, "pending": False, "done": True}[status_filter],
    )
    if shown:
        st.table(
            [
                {
                    "pet": t.pet_name,
                    "task": f"{task_emoji(t.title)} {t.title}",
                    "start": f"{t.scheduled_time:%a %H:%M}",
                    "minutes": t.duration_minutes,
                    "priority": priority_badge(t.priority),
                    "repeats": t.frequency,
                    "status": "✅ done" if t.completed else "⏳ pending",
                    "conflict": "⚠️ overlap" if id(t) in conflicting else "",
                }
                for t in (scheduler.sort_by_priority(shown) if sort_choice != "Time" else scheduler.sort_by_time(shown))
            ]
        )
    else:
        st.info("No tasks match that filter.")

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    plan = scheduler.generate_plan()
    if not plan:
        st.info("Nothing to schedule for today. Add a pet and some tasks.")
    else:
        used = sum(t.duration_minutes for t in plan)
        st.success(f"Planned {len(plan)} task(s) using {used} of {owner.available_minutes} minutes.")
        metric1, metric2 = st.columns(2)
        metric1.metric("Tasks planned", len(plan))
        metric2.metric("Minutes used", f"{used} / {owner.available_minutes}")
        st.table(
            [
                {
                    "start": f"{t.scheduled_time:%H:%M}",
                    "pet": t.pet_name,
                    "task": f"{task_emoji(t.title)} {t.title}",
                    "minutes": t.duration_minutes,
                    "priority": priority_badge(t.priority),
                }
                for t in plan
            ]
        )
        show_conflicts(scheduler.conflict_warnings(plan))
        with st.expander("Why this plan?", expanded=True):
            st.text(scheduler.explain_plan(plan))

# Save after every interaction so the next run picks up where this one left off.
try:
    owner.save_to_json(DATA_FILE)
except OSError as error:
    st.warning(f"Your changes could not be saved to {DATA_FILE.name}: {error}")
