import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes=60)

PRIORITY_MAP = {"High": 1, "Medium": 2, "Low": 3}

st.title("🐾 PawPal+")

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
        st.markdown(f"- {pet.get_summary()}")

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

    description = st.text_input("Description (optional)", value="")
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])

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
            ))
            st.success(f"'{task_name}' added to {selected_pet}!")

    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("All tasks:")
        st.table([
            {
                "Pet": next(p.name for p in st.session_state.owner.pets if task in p.tasks),
                "Task": task.name,
                "Duration": f"{task.duration_minutes} min",
                "Priority": priority_label,
                "Category": task.category,
            }
            for task, priority_label in [
                (t, {1: "High", 2: "Medium", 3: "Low"}[t.priority])
                for t in all_tasks
            ]
        ])

st.divider()

# ── Section 4: Generate schedule ─────────────────────────────────────────────

st.subheader("Generate Today's Schedule")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    if not owner.name:
        st.warning("Please save your owner info first.")
    elif not owner.pets:
        st.warning("Add at least one pet before generating a schedule.")
    elif not owner.get_all_pending_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        plan = Scheduler(owner).generate_plan()
        st.success(plan.summary())

        st.markdown("### Scheduled Tasks")
        for i, task in enumerate(plan.scheduled_tasks, start=1):
            st.markdown(f"**{i}. {task.name}** — {task.duration_minutes} min | {task.category} | priority {task.priority}")
            if task.description:
                st.caption(task.description)

        if plan.has_skipped():
            st.markdown("### Skipped (not enough time)")
            for task in plan.skipped_tasks:
                st.markdown(f"- {task.name} ({task.duration_minutes} min)")

        with st.expander("Reasoning"):
            st.text(plan.reasoning)