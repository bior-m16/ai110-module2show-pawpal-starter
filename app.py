from datetime import date, datetime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

PRIORITY_VALUES = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABELS = {value: label for label, value in PRIORITY_VALUES.items()}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# The "vault": create the Owner once per session and reuse it on every rerun.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)
owner: Owner = st.session_state.owner

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

if owner.get_all_tasks():
    st.write("All tasks:")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        pet_filter = st.selectbox("Show pet", ["All"] + [pet.name for pet in owner.pets])
    with filter_col2:
        status_filter = st.selectbox("Show status", ["All", "pending", "done"])

    shown = owner.filter_tasks(
        pet_name=None if pet_filter == "All" else pet_filter,
        completed={"All": None, "pending": False, "done": True}[status_filter],
    )
    if shown:
        st.table(
            [
                {
                    "pet": t.pet_name,
                    "task": t.title,
                    "start": f"{t.scheduled_time:%a %H:%M}",
                    "minutes": t.duration_minutes,
                    "priority": PRIORITY_LABELS[t.priority],
                    "repeats": t.frequency,
                    "done": t.completed,
                }
                for t in Scheduler.sort_by_time(shown)
            ]
        )
    else:
        st.info("No tasks match that filter.")

    # Standing conflict list: stays visible until the overlap is fixed.
    for warning in Scheduler(owner).conflict_warnings():
        st.warning(warning)

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    if not plan:
        st.info("Nothing to schedule yet. Add a pet and some tasks.")
    else:
        st.table(
            [
                {
                    "start": f"{t.scheduled_time:%H:%M}",
                    "pet": t.pet_name,
                    "task": t.title,
                    "minutes": t.duration_minutes,
                    "priority": PRIORITY_LABELS[t.priority],
                }
                for t in plan
            ]
        )
        for warning in scheduler.conflict_warnings(plan):
            st.warning(warning)
        with st.expander("Why this plan?", expanded=True):
            st.text(scheduler.explain_plan(plan))
