"""main.py — Demo script to verify PawPal+ scheduling logic in the terminal."""

from pawpal_system import Owner, Pet, Task, Scheduler


# ── Setup ─────────────────────────────────────────────────────────────────────

owner = Owner(name="Mridula", available_minutes=60)

dog = Pet(name="Bruno", species="dog", age=4)
cat = Pet(name="Luna", species="cat", age=11)

# Tasks for Bruno
dog.add_task(Task(
    name="Morning walk",
    duration_minutes=20,
    priority=1,
    category="walk",
    description="30-minute walk around the block.",
    frequency="daily",
))
dog.add_task(Task(
    name="Breakfast",
    duration_minutes=5,
    priority=1,
    category="feeding",
    description="One cup of dry food.",
    frequency="daily",
))
dog.add_task(Task(
    name="Grooming",
    duration_minutes=25,
    priority=3,
    category="grooming",
    description="Brush coat and clean ears.",
    frequency="weekly",
))

# Tasks for Luna
cat.add_task(Task(
    name="Medication",
    duration_minutes=5,
    priority=1,
    category="medication",
    description="Half a tablet hidden in wet food.",
    frequency="daily",
))
cat.add_task(Task(
    name="Playtime",
    duration_minutes=15,
    priority=2,
    category="enrichment",
    description="Feather wand session.",
    frequency="daily",
))

owner.add_pet(dog)
owner.add_pet(cat)


# ── Generate plan ─────────────────────────────────────────────────────────────

scheduler = Scheduler(owner)
plan = scheduler.generate_plan()


# ── Print output ──────────────────────────────────────────────────────────────

print("=" * 45)
print(f"  TODAY'S SCHEDULE — {owner.name}")
print("=" * 45)

for i, task in enumerate(plan.scheduled_tasks, start=1):
    print(f"  {i}. [{task.category.upper()}] {task.name}")
    print(f"     {task.duration_minutes} min  |  priority {task.priority}  |  {task.frequency}")
    if task.description:
        print(f"     {task.description}")
    print()

print("-" * 45)
print(f"  {plan.summary()}")
print("-" * 45)

if plan.has_skipped():
    print("\n  Skipped (not enough time):")
    for task in plan.skipped_tasks:
        print(f"    - {task.name} ({task.duration_minutes} min)")

print("\n  Reasoning:")
for line in plan.reasoning.splitlines():
    print(f"    {line}")

print("=" * 45)