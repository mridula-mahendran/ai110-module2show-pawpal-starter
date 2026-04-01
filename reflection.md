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

## 3. AI Collaboration

**a. How you used AI**

AI was used at every stage of this project. During system design, it helped brainstorm which classes to create and what responsibilities to assign to each. During implementation, it drafted method stubs and filled in logic incrementally — starting with `generate_plan()`, then adding sorting, filtering, recurring tasks, and conflict detection one phase at a time. During testing, it generated the full pytest suite based on the actual method signatures in the code. During refactoring, it suggested replacing the nested loop in `detect_conflicts()` with `itertools.combinations`, which was both shorter and clearer.

The most helpful prompts were specific ones that referenced the actual code — for example, asking "what validation should I add to Task and Owner before implementing generate_plan?" produced more useful output than open-ended questions. Asking AI to explain a tradeoff before implementing it (such as Shortest Job First vs. other tiebreakers) also helped make deliberate design decisions rather than just accepting the first suggestion.

**b. Judgment and verification**

One moment where the AI suggestion was not accepted as-is was the initial class design. The first draft included helper methods like `is_senior()`, `to_dict()`, and `get_summary()` on `Pet` and `Task` before it was clear whether the Streamlit UI would actually need them. Rather than implementing all of them immediately, the decision was made to stub them out and only flesh out the ones that were genuinely needed during the UI wiring phase. This avoided over-engineering the data classes before the requirements were confirmed.

Every AI-generated method was verified by running it in `main.py` before moving on. For example, the recurring task logic was tested by printing the full task list before and after calling `mark_task_complete()` to confirm the new task appeared with the correct `due_date`. Tests were also used as a second layer of verification — if a method passed its pytest case, it was considered reliable enough to wire into the UI.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers fourteen behaviors across five categories. Task completion verifies that `mark_complete()` correctly flips `is_completed`. Pet task management confirms that `add_task()` increases the task count. Sorting correctness checks that `sort_by_time()` returns tasks in chronological order regardless of insertion order. Recurrence logic confirms that daily tasks produce a next occurrence one day later, weekly tasks produce one seven days later, and `as_needed` tasks produce no follow-up. Conflict detection verifies that both exact same-start overlaps and partial overlaps are flagged, and that non-overlapping tasks produce no false warnings. Edge cases cover empty task lists, tasks that exceed available time, a task that fits exactly, and filtering by a pet name that does not exist.

These tests were important because the scheduler's core value depends on correctness — a pet owner relying on this app to manage medication schedules cannot afford silent bugs in priority sorting or recurrence logic.

**b. Confidence**

Confidence level: ★★★★☆

All 14 tests pass. The core scheduling behaviors — priority sorting, time fitting, recurrence, and conflict detection — are well covered. The one-star gap reflects three untested areas: preference-aware scheduling (the `preferences` dict on `Owner` is stored but never read by `generate_plan()`), multi-pet time budget splitting (the scheduler treats all pets' tasks as a flat pool), and the Streamlit UI layer (no tests verify that session state persists correctly across reruns). If given more time, those three areas plus invalid `time_slot` format inputs (e.g. `"8:0"` instead of `"08:00"`) would be the next test cases to write.

---

## 5. Reflection

**a. What went well**

The separation of concerns across the five classes held up well throughout the entire build. Because `Scheduler` was the only class with logic and the data classes were kept clean, it was straightforward to add new methods in Phase 3 without touching any existing code. The `generate_plan()` method in particular stayed readable even after the surrounding system grew significantly, because its job never changed — it delegates to helpers and returns a `DailyPlan`.

**b. What you would improve**

The `preferences` dict on `Owner` is the biggest gap between design and implementation. It was planned as a way for the scheduler to honor owner preferences like "prefer morning walks first" or "skip grooming on weekdays," but it was never wired into `generate_plan()`. In another iteration, `preferences` would be replaced with a dedicated `Preferences` dataclass with typed fields, and `generate_plan()` would apply them as a post-sort filter before building the schedule.

The conflict detection system would also be improved. Currently it flags conflicts but does not block scheduling — the plan is still generated even if two tasks overlap. A better design would either prevent conflicting tasks from both being scheduled, or prompt the owner to resolve the conflict before generating the plan.

**c. Key takeaway**

The most important thing learned was that AI is most useful when you already have a clear mental model of what you are building. When prompts were vague — "help me design the system" — the output needed significant editing. When prompts were specific — "add `__post_init__` validation to Task that rejects priority outside 1–3 and duration_minutes that is zero or negative" — the output was accurate and ready to use with minimal changes. Working with AI effectively is less about letting it drive and more about giving it precise enough instructions that its output lands close to what you actually need.