"""main.py — Demo script to verify conflict detection in the terminal."""

from pawpal_system import Owner, Pet, Task, Scheduler


# ── Setup ─────────────────────────────────────────────────────────────────────

owner = Owner(name="Mridula", available_minutes=120)

dog = Pet(name="Bruno", species="dog", age=4)
cat = Pet(name="Luna", species="cat", age=11)

# Bruno: walk starts at 07:00 (20 min) → ends 07:20
#        grooming starts at 07:10 (25 min) → overlaps walk by 10 min
dog.add_task(Task(
    name="Morning walk",
    duration_minutes=20,
    priority=1,
    category="walk",
    time_slot="07:00",
))
dog.add_task(Task(
    name="Grooming",
    duration_minutes=25,
    priority=3,
    category="grooming",
    time_slot="07:10",   # ← overlaps Morning walk
))

# Luna: medication at 08:00 (5 min) → ends 08:05
#       playtime at 08:00 (15 min) → exact same start, overlaps
cat.add_task(Task(
    name="Medication",
    duration_minutes=5,
    priority=1,
    category="medication",
    time_slot="08:00",
))
cat.add_task(Task(
    name="Playtime",
    duration_minutes=15,
    priority=2,
    category="enrichment",
    time_slot="08:00",   # ← same start time as Medication
))

# No conflict: Breakfast starts at 09:00, well after everything above
dog.add_task(Task(
    name="Breakfast",
    duration_minutes=5,
    priority=1,
    category="feeding",
    time_slot="09:00",
))

owner.add_pet(dog)
owner.add_pet(cat)

scheduler = Scheduler(owner)


# ── Run conflict detection ────────────────────────────────────────────────────

all_tasks = owner.get_all_tasks()
conflicts = scheduler.detect_conflicts(all_tasks)

print("=" * 50)
print("  CONFLICT DETECTION REPORT")
print("=" * 50)

if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")

print("=" * 50)