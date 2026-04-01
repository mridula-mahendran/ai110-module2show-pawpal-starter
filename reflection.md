# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial design uses five classes: Owner, Pet, Task, Scheduler, and DailyPlan. The core principle is separation of concerns — data classes hold information only, and all scheduling logic lives exclusively in Scheduler.

Owner is a dataclass with three fields: name (str), available_minutes (int), and preferences (dict). It makes no decisions. Its only role is to give the Scheduler the time budget and any owner-side preferences to factor in.

Pet is a dataclass with four fields: name, species, age, and a reference to its Owner. It is also purely a data container. The owner reference means the Scheduler can access both pet and owner information through a single object if needed.

Task is a dataclass representing one care activity. It has four fields: name (str), duration_minutes (int), priority (int, where 1 is highest and 3 is lowest), and category (str, such as "walk", "feeding", or "medication"). A task knows nothing about scheduling — it only describes what the activity is.

Scheduler is the only class with logic. It holds references to an Owner, a Pet, and a list of Task objects. Its public method generate_plan() orchestrates the full scheduling process and returns a DailyPlan. Two private helpers support it: _sort_by_priority() returns tasks sorted from priority 1 down to 3, and _fits_in_time() checks whether a single task can still fit within the remaining time budget.

DailyPlan is the output object. It holds four fields: scheduled_tasks (the tasks that made it into the plan), skipped_tasks (those dropped due to time constraints), total_duration (the sum of scheduled task durations), and reasoning (a string the UI can display to explain how the plan was built).

The relationships are: Pet references one Owner. Scheduler reads constraints from Owner, schedules for Pet, organizes a list of Task objects, and produces one DailyPlan.

**b. Design changes**

Four changes were made to the skeleton after reviewing the initial design.

Added __post_init__ validation to Owner and Task. The initial design had no guards on field values. Without them, nothing would stop code like Task(priority=99) or Owner(available_minutes=-10) from being created — both would silently produce wrong results when generate_plan() runs. Owner now rejects available_minutes that is zero or negative, and Task now rejects any priority outside of 1, 2, or 3, and any duration_minutes that is not positive. A ValueError is raised immediately at construction so the bug surfaces at the source rather than deep inside scheduling logic.

Added duration_minutes validation to Task. Related to the above — a task with zero duration would pass the priority check but still silently corrupt the schedule by consuming a slot without using any time. The same __post_init__ block catches this.

Changed bare list to list[Task] in DailyPlan. scheduled_tasks and skipped_tasks were typed as plain list, which gives no information about what the list should contain. Changing both to list[Task] makes the contract explicit — the Streamlit UI and any tests can rely on these always being lists of Task objects, and type checkers will flag misuse early.

Implemented _sort_by_priority with a two-key sort. The initial stub left this method as pass. The sort key is (priority, duration_minutes) — primary sort on priority (1 first), secondary sort on duration ascending. The secondary key is a Shortest Job First tiebreaker: when multiple tasks share the same priority, scheduling the shorter one first maximises the number of tasks that fit within the available time window. This was implemented in the skeleton rather than deferred because the sort strategy directly affects the behaviour of generate_plan(), which is the next thing to build.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: available time (owner's available_minutes), task priority (1–3), and task duration. It ignores tasks already marked complete via is_completed, and skips tasks whose frequency has already been satisfied.

Priority was treated as the primary constraint because it most directly reflects what a pet owner actually cares about — a medication task should never be bumped for a grooming task regardless of duration. Duration was chosen as the tiebreaker using a Shortest Job First strategy, which maximises the number of tasks that fit in the available window when multiple tasks share the same priority.

time_slot and due_date inform display order and conflict detection but do not currently affect which tasks make it into the plan — the greedy algorithm schedules by priority first, not by time of day.

**b. Tradeoffs**

The scheduler uses a greedy algorithm, which does not guarantee the best possible plan. generate_plan() works through the sorted task list from highest to lowest priority and schedules each task the moment it fits, without looking ahead. This means it can make locally correct decisions that lead to a globally suboptimal result.

For example: if two priority-1 tasks each take 55 minutes and the owner has 60 minutes available, the greedy algorithm schedules the first one and skips the second — leaving 5 minutes unused and a high-priority task unscheduled. A smarter algorithm might recognise that neither fits alongside the other and prompt the owner to choose, or swap in lower-priority tasks to fill the remaining time more efficiently.

This tradeoff is reasonable for PawPal+ because the task lists are small (typically under 10 tasks per owner), the scheduling window is a single day, and simplicity matters more than optimality at this scale. A greedy approach is also predictable — the owner can understand why each task was chosen or skipped by reading the reasoning field, which would be harder to explain with a more complex algorithm like dynamic programming.

---

## Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest -v
```

**What the tests cover:**

- **Task completion** — verifying `mark_complete()` updates `is_completed` correctly
- **Pet task management** — confirming `add_task()` increases the pet's task count
- **Sorting correctness** — ensuring `sort_by_time()` returns tasks in chronological order regardless of insertion order
- **Recurrence logic** — confirming daily and weekly tasks auto-generate a next occurrence on completion, and that `as_needed` tasks do not
- **Conflict detection** — verifying the scheduler flags both exact same-start and partial time overlaps, and produces no false positives for non-overlapping tasks
- **Edge cases** — empty task lists, tasks that exceed available time, a task that fits exactly, and filtering by a pet name that doesn't exist

**Confidence level: ★★★★☆**

Core scheduling behaviors are well covered and all 14 tests pass. The one-star gap reflects areas not yet tested: preference-aware scheduling, multi-pet time budget splitting, and UI-layer behavior in `app.py`. Those would be the next additions to the suite.



PawPal+ goes beyond a basic to-do list with four scheduling improvements built into the `Scheduler` class.

**Sort by time.** `sort_by_time()` orders tasks by their preferred start time using `HH:MM` string comparison. Because times are zero-padded, lexicographic order matches chronological order — no datetime parsing needed.

**Filter by pet or status.** `filter_by_pet()` returns tasks belonging to a single named pet. `filter_by_status()` returns all tasks across every pet that are either complete or incomplete. Both methods let the UI show a focused view instead of a flat list.

**Recurring tasks.** Every `Task` has a `frequency` field (`daily`, `weekly`, or `as_needed`) and a `due_date`. When `mark_task_complete()` is called on a daily or weekly task, `clone_for_next_occurrence()` automatically creates a fresh copy scheduled for the next due date using Python's `timedelta`. Tasks marked `as_needed` are completed without spawning a follow-up.

**Conflict detection.** `detect_conflicts()` checks every pair of tasks using `itertools.combinations` and flags any two whose time windows overlap. The overlap condition is `start_A < end_B and start_B < end_A`, which catches both exact same-start collisions and partial overlaps. Warnings are returned as a list of strings so the app can display them without crashing.


## Smarter Scheduling

PawPal+ goes beyond a basic to-do list with four scheduling improvements built into the `Scheduler` class.

**Sort by time.** `sort_by_time()` orders tasks by their preferred start time using `HH:MM` string comparison. Because times are zero-padded, lexicographic order matches chronological order — no datetime parsing needed.

**Filter by pet or status.** `filter_by_pet()` returns tasks belonging to a single named pet. `filter_by_status()` returns all tasks across every pet that are either complete or incomplete. Both methods let the UI show a focused view instead of a flat list.

**Recurring tasks.** Every `Task` has a `frequency` field (`daily`, `weekly`, or `as_needed`) and a `due_date`. When `mark_task_complete()` is called on a daily or weekly task, `clone_for_next_occurrence()` automatically creates a fresh copy scheduled for the next due date using Python's `timedelta`. Tasks marked `as_needed` are completed without spawning a follow-up.

**Conflict detection.** `detect_conflicts()` checks every pair of tasks using `itertools.combinations` and flags any two whose time windows overlap. The overlap condition is `start_A < end_B and start_B < end_A`, which catches both exact same-start collisions and partial overlaps. Warnings are returned as a list of strings so the app can display them without crashing.

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?