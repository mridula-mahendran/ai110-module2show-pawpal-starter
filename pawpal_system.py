"""PawPal+ — Smart Pet Care Management System"""

from dataclasses import dataclass, field
from typing import Optional

VALID_FREQUENCIES = ("daily", "weekly", "as_needed")


# ── Task ─────────────────────────────────────────────────────────────────────

@dataclass
class Task:
    """Represents a single pet care activity."""
    name: str
    duration_minutes: int
    priority: int        # 1 (highest) to 3 (lowest)
    category: str        # e.g. "feeding", "walk", "medication"
    description: str = ""
    frequency: str = "daily"   # "daily" | "weekly" | "as_needed"
    is_completed: bool = False

    def __post_init__(self):
        if self.priority not in (1, 2, 3):
            raise ValueError(f"priority must be 1, 2, or 3, got {self.priority}")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}, got '{self.frequency}'")

    def mark_complete(self):
        """Mark this task as completed."""
        self.is_completed = True

    def reset(self):
        """Reset completion status (call at the start of each new day)."""
        self.is_completed = False

    def is_high_priority(self) -> bool:
        """Return True if this task has priority 1."""
        return self.priority == 1

    def to_dict(self) -> dict:
        """Serialize to a dict (used for Streamlit session state storage)."""
        return {
            "name": self.name,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "description": self.description,
            "frequency": self.frequency,
            "is_completed": self.is_completed,
        }


# ── Pet ──────────────────────────────────────────────────────────────────────

@dataclass
class Pet:
    """Stores pet details and owns a list of care tasks."""
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> bool:
        """Remove a task by name. Returns True if found and removed."""
        for task in self.tasks:
            if task.name == task_name:
                self.tasks.remove(task)
                return True
        return False

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.is_completed]

    def get_tasks_by_category(self, category: str) -> list[Task]:
        """Return all tasks matching a given category."""
        return [t for t in self.tasks if t.category == category]

    def reset_all_tasks(self):
        """Reset completion on all tasks (call at the start of each new day)."""
        for task in self.tasks:
            task.reset()

    def is_senior(self) -> bool:
        """Return True if the pet is senior age for its species."""
        thresholds = {"dog": 8, "cat": 10, "rabbit": 6}
        return self.age >= thresholds.get(self.species.lower(), 10)

    def get_summary(self) -> str:
        """Return a short human-readable label for UI display."""
        return f"{self.name} ({self.species}, age {self.age})"


# ── Owner ─────────────────────────────────────────────────────────────────────

@dataclass
class Owner:
    """Manages multiple pets and provides a unified view of all their tasks."""
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)
    # Expected preference keys:
    #   "prefer_morning_walks" (bool) — schedule walk tasks first
    #   "skip_categories"      (list[str]) — categories to exclude from planning
    preferences: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.available_minutes <= 0:
            raise ValueError(f"available_minutes must be positive, got {self.available_minutes}")

    def add_pet(self, pet: Pet):
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        for pet in self.pets:
            if pet.name == pet_name:
                self.pets.remove(pet)
                return True
        return False

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up a pet by name. Returns None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]

    def get_available_time(self) -> int:
        """Return the owner's daily time budget in minutes."""
        return self.available_minutes


# ── DailyPlan ─────────────────────────────────────────────────────────────────

@dataclass
class DailyPlan:
    """Output object produced by Scheduler.generate_plan()."""
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    # One line per scheduling decision, e.g.:
    #   "Scheduled 'walk' (20 min, priority 1)."
    #   "Skipped 'grooming' (30 min) — not enough time remaining."
    reasoning: str = ""

    def summary(self) -> str:
        """Return a short human-readable summary for the UI header."""
        n_sched = len(self.scheduled_tasks)
        n_skip = len(self.skipped_tasks)
        base = f"{n_sched} task(s) scheduled ({self.total_duration} min total)"
        return base + (f", {n_skip} skipped." if n_skip else ".")

    def has_skipped(self) -> bool:
        """Return True if any tasks were dropped due to time constraints."""
        return len(self.skipped_tasks) > 0


# ── Scheduler ─────────────────────────────────────────────────────────────────

class Scheduler:
    """Retrieves, organizes, and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Sort all pending tasks by priority, fit them into available time, and return a DailyPlan."""
        pending = self.owner.get_all_pending_tasks()
        sorted_tasks = self._sort_by_priority(pending)

        scheduled: list[Task] = []
        skipped: list[Task] = []
        remaining = self.owner.get_available_time()
        lines: list[str] = []

        for task in sorted_tasks:
            if self._fits_in_time(task, remaining):
                scheduled.append(task)
                remaining -= task.duration_minutes
                lines.append(
                    f"Scheduled '{task.name}' ({task.duration_minutes} min, priority {task.priority})."
                )
            else:
                skipped.append(task)
                lines.append(
                    f"Skipped '{task.name}' ({task.duration_minutes} min) — not enough time remaining."
                )

        total = self.owner.get_available_time() - remaining
        reasoning = "\n".join(lines) if lines else "No pending tasks found."

        return DailyPlan(
            scheduled_tasks=scheduled,
            skipped_tasks=skipped,
            total_duration=total,
            reasoning=reasoning,
        )

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority ascending, then duration ascending as a tiebreaker."""
        return sorted(tasks, key=lambda t: (t.priority, t.duration_minutes))

    def _fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if the task fits within the remaining time budget."""
        return task.duration_minutes <= remaining_minutes

    def get_tasks_by_priority(self, priority: int) -> list[Task]:
        """Return all pending tasks across all pets at a given priority level."""
        return [t for t in self.owner.get_all_pending_tasks() if t.priority == priority]

    def get_tasks_by_category(self, category: str) -> list[Task]:
        """Return all pending tasks across all pets in a given category."""
        return [t for t in self.owner.get_all_pending_tasks() if t.category == category]

    def mark_task_complete(self, task_name: str) -> bool:
        """
        Find a task by name across all pets and mark it complete.
        Returns True if found, False if no matching task exists.
        """
        for task in self.owner.get_all_tasks():
            if task.name == task_name:
                task.mark_complete()
                return True
        return False

    def reset_all_tasks(self):
        """Reset completion status on every task across all pets (call at day start)."""
        for pet in self.owner.pets:
            pet.reset_all_tasks()