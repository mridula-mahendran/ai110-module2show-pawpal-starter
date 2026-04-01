"""PawPal+ — Smart Pet Care Management System"""

from dataclasses import dataclass, field


@dataclass
class Owner:
    """Data container for pet owner information and constraints."""
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)


@dataclass
class Pet:
    """Data container for pet information."""
    name: str
    species: str
    age: int
    owner: Owner


@dataclass
class Task:
    """Represents a single pet care activity."""
    name: str
    duration_minutes: int
    priority: int  # 1 (highest) to 3 (lowest)
    category: str  # e.g. "feeding", "walk", "medication"


@dataclass
class DailyPlan:
    """Output object holding the generated schedule."""
    scheduled_tasks: list = field(default_factory=list)
    skipped_tasks: list = field(default_factory=list)
    total_duration: int = 0
    reasoning: str = ""


class Scheduler:
    """Core scheduling engine that builds a DailyPlan from owner constraints and tasks."""

    def __init__(self, owner: Owner, pet: Pet, tasks: list):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def generate_plan(self) -> DailyPlan:
        """Sort tasks by priority, fit into available time, return a DailyPlan."""
        pass

    def _sort_by_priority(self, tasks: list) -> list:
        """Return tasks sorted by priority (1 = highest first)."""
        pass

    def _fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        """Check whether a task fits within the remaining time budget."""
        pass
