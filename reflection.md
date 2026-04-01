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
Added __post_init__ validation to Owner and Task.
The initial design had no guards on field values. Without them, nothing would stop code like Task(priority=99) or Owner(available_minutes=-10) from being created — both would silently produce wrong results when generate_plan() runs. Owner now rejects available_minutes that is zero or negative, and Task now rejects any priority outside of 1, 2, or 3, and any duration_minutes that is not positive. A ValueError is raised immediately at construction so the bug surfaces at the source rather than deep inside scheduling logic.
Added duration_minutes validation to Task.
Related to the above — a task with zero duration would pass the priority check but still silently corrupt the schedule by consuming a slot without using any time. The same __post_init__ block catches this.
Changed bare list to list[Task] in DailyPlan.
scheduled_tasks and skipped_tasks were typed as plain list, which gives no information about what the list should contain. Changing both to list[Task] makes the contract explicit — the Streamlit UI and any tests can rely on these always being lists of Task objects, and type checkers will flag misuse early.
Implemented _sort_by_priority with a two-key sort.
The initial stub left this method as pass. The sort key is (priority, duration_minutes) — primary sort on priority (1 first), secondary sort on duration ascending. The secondary key is a Shortest Job First tiebreaker: when multiple tasks share the same priority, scheduling the shorter one first maximises the number of tasks that fit within the available time window. This was implemented in the skeleton rather than deferred because the sort strategy directly affects the behaviour of generate_plan(), which is the next thing to build.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

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
