"""tests/test_pawpal.py — Automated test suite for PawPal+ core behaviors."""

from datetime import date, timedelta
import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def owner():
    """A basic owner with 60 minutes available."""
    return Owner(name="Mridula", available_minutes=60)

@pytest.fixture
def pet():
    """A pet with no tasks — used as a clean starting point."""
    return Pet(name="Bruno", species="dog", age=4)

@pytest.fixture
def scheduler(owner, pet):
    """A Scheduler with one pet and no tasks yet."""
    owner.add_pet(pet)
    return Scheduler(owner)


# ── Original tests ────────────────────────────────────────────────────────────

def test_mark_complete_changes_status(pet):
    """Calling mark_complete() should set is_completed to True."""
    task = Task(name="Morning walk", duration_minutes=20, priority=1, category="walk")
    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count(pet):
    """Adding a task to a Pet should increase its task list length by 1."""
    assert len(pet.tasks) == 0
    pet.add_task(Task(name="Breakfast", duration_minutes=5, priority=1, category="feeding"))
    assert len(pet.tasks) == 1


# ── Sorting correctness ───────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order(scheduler, pet):
    """sort_by_time() should return tasks ordered earliest to latest regardless of insertion order."""
    pet.add_task(Task(name="Evening walk", duration_minutes=20, priority=2, category="walk", time_slot="18:00"))
    pet.add_task(Task(name="Medication",   duration_minutes=5,  priority=1, category="medication", time_slot="08:00"))
    pet.add_task(Task(name="Playtime",     duration_minutes=15, priority=2, category="enrichment", time_slot="11:00"))

    sorted_tasks = scheduler.sort_by_time(scheduler.owner.get_all_tasks())
    times = [t.time_slot for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_time_single_task(scheduler, pet):
    """sort_by_time() on a single task should return that task unchanged."""
    task = Task(name="Breakfast", duration_minutes=5, priority=1, category="feeding", time_slot="07:30")
    pet.add_task(task)
    result = scheduler.sort_by_time(scheduler.owner.get_all_tasks())
    assert len(result) == 1
    assert result[0].name == "Breakfast"


# ── Recurrence logic ──────────────────────────────────────────────────────────

def test_daily_task_creates_next_occurrence(scheduler, pet):
    """Completing a daily task should add a new task due the following day."""
    today = date.today()
    pet.add_task(Task(name="Morning walk", duration_minutes=20, priority=1, category="walk", frequency="daily"))

    scheduler.mark_task_complete("Morning walk")

    assert len(pet.tasks) == 2
    new_task = pet.tasks[1]
    assert new_task.due_date == today + timedelta(days=1)
    assert new_task.is_completed is False


def test_weekly_task_creates_next_occurrence(scheduler, pet):
    """Completing a weekly task should add a new task due seven days later."""
    today = date.today()
    pet.add_task(Task(name="Grooming", duration_minutes=25, priority=3, category="grooming", frequency="weekly"))

    scheduler.mark_task_complete("Grooming")

    assert len(pet.tasks) == 2
    assert pet.tasks[1].due_date == today + timedelta(weeks=1)


def test_as_needed_task_does_not_recur(scheduler, pet):
    """Completing an as_needed task should NOT create a new task."""
    pet.add_task(Task(name="Vet visit", duration_minutes=60, priority=2, category="medication", frequency="as_needed"))

    scheduler.mark_task_complete("Vet visit")

    assert len(pet.tasks) == 1
    assert pet.tasks[0].is_completed is True


# ── Conflict detection ────────────────────────────────────────────────────────

def test_detect_conflicts_flags_same_start_time(scheduler, pet):
    """Two tasks starting at the same time should be flagged as a conflict."""
    pet.add_task(Task(name="Medication", duration_minutes=5,  priority=1, category="medication", time_slot="08:00"))
    pet.add_task(Task(name="Playtime",   duration_minutes=15, priority=2, category="enrichment", time_slot="08:00"))

    conflicts = scheduler.detect_conflicts(scheduler.owner.get_all_tasks())
    assert len(conflicts) == 1
    assert "Medication" in conflicts[0]
    assert "Playtime" in conflicts[0]


def test_detect_conflicts_flags_partial_overlap(scheduler, pet):
    """A task starting mid-way through another should be flagged as a conflict."""
    pet.add_task(Task(name="Morning walk", duration_minutes=20, priority=1, category="walk",     time_slot="07:00"))
    pet.add_task(Task(name="Grooming",     duration_minutes=25, priority=3, category="grooming", time_slot="07:10"))

    conflicts = scheduler.detect_conflicts(scheduler.owner.get_all_tasks())
    assert len(conflicts) == 1


def test_detect_conflicts_no_conflicts(scheduler, pet):
    """Tasks with non-overlapping windows should return no conflicts."""
    pet.add_task(Task(name="Breakfast",    duration_minutes=5,  priority=1, category="feeding",  time_slot="07:00"))
    pet.add_task(Task(name="Morning walk", duration_minutes=20, priority=1, category="walk",      time_slot="08:00"))

    conflicts = scheduler.detect_conflicts(scheduler.owner.get_all_tasks())
    assert conflicts == []


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_generate_plan_with_no_tasks(scheduler):
    """generate_plan() on an owner with no tasks should return an empty plan without crashing."""
    plan = scheduler.generate_plan()
    assert plan.scheduled_tasks == []
    assert plan.skipped_tasks == []


def test_generate_plan_skips_tasks_that_exceed_time(owner, pet):
    """Tasks whose total duration exceeds available time should be skipped."""
    owner.add_pet(pet)
    pet.add_task(Task(name="Long task", duration_minutes=90, priority=1, category="walk"))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan()
    assert len(plan.scheduled_tasks) == 0
    assert len(plan.skipped_tasks) == 1


def test_task_fits_exactly_in_available_time(owner, pet):
    """A task equal to available_minutes should be scheduled with 0 minutes remaining."""
    owner.add_pet(pet)
    pet.add_task(Task(name="Exact fit", duration_minutes=60, priority=1, category="walk"))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan()
    assert len(plan.scheduled_tasks) == 1
    assert plan.total_duration == 60


def test_filter_by_pet_unknown_name_returns_empty(scheduler):
    """filter_by_pet() with a name that doesn't exist should return an empty list."""
    result = scheduler.filter_by_pet("NonExistentPet")
    assert result == []