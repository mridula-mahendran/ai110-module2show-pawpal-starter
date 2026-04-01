import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes=60)

PRIORITY_MAP      = {"High": 1, "Medium": 2, "Low": 3}
PRIORITY_LABEL    = {1: "High", 2: "Medium", 3: "Low"}

st.title("🐾 PawPal+")
st.caption("A smart daily care planner for your pets.")
st.divider()


# ── Section 1: Owner setup ────────────────────────────────────────────────────

st.subheader("Owner Setup")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value=st.session_state.owner.name)
with col2:
    available_minutes = st.number_input(
        "Time available today (minutes)",
        min_value=1, max_value=480,
        value=st.session_state.owner.available_minutes,
    )

if st.button("Save owner info"):
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_minutes = available_minutes
    st.success(f"Saved! {owner_name} has {available_minutes} minutes today.")

st.divider()


# ── Section 2: Add a pet ──────────────────────────────────────────────────────

st.subheader("Add a Pet")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
with col3:
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)

if st.button("Add pet"):
    if not pet_name.strip():
        st.warning("Please enter a pet name.")
    else:
        st.session_state.owner.add_pet(Pet(name=pet_name, species=species, age=age))
        st.success(f"{pet_name} added!")

if st.session_state.owner.pets:
    st.write("Your pets:")
    for pet in st.session_state.owner.pets:
        tag = " 🐾 senior" if pet.is_senior() else ""
        st.markdown(f"- {pet.get_summary()}{tag}")

st.divider()


# ── Section 3: Add a task ─────────────────────────────────────────────────────

st.subheader("Add a Task")

if not st.session_state.owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in st.session_state.owner.pets]

    col1, col2 = st.columns(2)
    with col1:
        selected_pet = st.selectbox("Assign to pet", pet_names)
    with col2:
        task_name = st.text_input("Task name", value="Morning walk")

    col1, col2, col3 = st.columns(3)
    with col1:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col2:
        priority_label = st.selectbox("Priority", ["High", "Medium", "Low"])
    with col3:
        category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])

    col1, col2 = st.columns(2)
    with col1:
        time_slot = st.text_input("Preferred time (HH:MM)", value="08:00")
    with col2:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])

    description = st.text_input("Description (optional)", value="")

    if st.button("Add task"):
        if not task_name.strip():
            st.warning("Please enter a task name.")
        else:
            pet = st.session_state.owner.get_pet(selected_pet)
            pet.add_task(Task(
                name=task_name,
                duration_minutes=int(duration),
                priority=PRIORITY_MAP[priority_label],
                category=category,
                description=description,
                frequency=frequency,
                time_slot=time_slot,
            ))
            st.success(f"'{task_name}' added to {selected_pet}!")

st.divider()


# ── Section 4: View tasks ─────────────────────────────────────────────────────

st.subheader("All Tasks")

all_tasks = st.session_state.owner.get_all_tasks()

if not all_tasks:
    st.info("No tasks yet. Add some above.")
else:
    scheduler = Scheduler(st.session_state.owner)

    # Conflict warnings — shown before the task table so they're hard to miss
    conflicts = scheduler.detect_conflicts(all_tasks)
    if conflicts:
        st.error(f"⚠ {len(conflicts)} scheduling conflict(s) detected — review your task times:")
        for warning in conflicts:
            st.warning(warning)

    # Pet filter
    pet_names = ["All pets"] + [p.name for p in st.session_state.owner.pets]
    selected_filter = st.selectbox("Filter by pet", pet_names)

    if selected_filter == "All pets":
        tasks_to_show = scheduler.sort_by_time(all_tasks)
    else:
        tasks_to_show = scheduler.sort_by_time(scheduler.filter_by_pet(selected_filter))

    # Task table
    if tasks_to_show:
        st.table([
            {
                "Time": t.time_slot,
                "Task": t.name,
                "Pet": next(p.name for p in st.session_state.owner.pets if t in p.tasks),
                "Duration": f"{t.duration_minutes} min",
                "Priority": PRIORITY_LABEL[t.priority],
                "Category": t.category,
                "Frequency": t.frequency,
                "Done": "✓" if t.is_completed else "○",
            }
            for t in tasks_to_show
        ])
    else:
        st.info(f"No tasks found for {selected_filter}.")

st.divider()


# ── Section 5: Generate schedule ──────────────────────────────────────────────

st.subheader("Generate Today's Schedule")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    if not owner.name:
        st.warning("Please save your owner info first.")
    elif not owner.pets:
        st.warning("Add at least one pet before generating a schedule.")
    elif not owner.get_all_pending_tasks():
        st.warning("No pending tasks to schedule.")
    else:
        scheduler = Scheduler(owner)

        # Show conflict warnings before the plan
        conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
        if conflicts:
            st.error("⚠ Conflicts found in your task list. Consider fixing these before running the schedule:")
            for c in conflicts:
                st.warning(c)

        plan = scheduler.generate_plan()
        st.success(plan.summary())

        if plan.scheduled_tasks:
            st.markdown("### Scheduled Tasks")
            for i, task in enumerate(plan.scheduled_tasks, start=1):
                st.markdown(
                    f"**{i}. {task.name}** — {task.time_slot} | "
                    f"{task.duration_minutes} min | {task.category} | "
                    f"priority {PRIORITY_LABEL[task.priority]}"
                )
                if task.description:
                    st.caption(task.description)

        if plan.has_skipped():
            st.markdown("### Skipped (not enough time)")
            for task in plan.skipped_tasks:
                st.warning(f"{task.name} ({task.duration_minutes} min) could not fit in today's schedule.")

        with st.expander("Reasoning"):
            st.text(plan.reasoning)