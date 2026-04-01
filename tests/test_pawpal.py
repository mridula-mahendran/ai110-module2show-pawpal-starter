"""tests/test_pawpal.py — Basic tests for PawPal+ core logic."""

from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    """Calling mark_complete() should set is_completed to True."""
    task = Task(
        name="Morning walk",
        duration_minutes=20,
        priority=1,
        category="walk",
    )
    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list length by 1."""
    pet = Pet(name="Bruno", species="dog", age=4)
    assert len(pet.tasks) == 0

    pet.add_task(Task(
        name="Breakfast",
        duration_minutes=5,
        priority=1,
        category="feeding",
    ))
    assert len(pet.tasks) == 1