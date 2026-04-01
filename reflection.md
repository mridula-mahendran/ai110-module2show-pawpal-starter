# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial design uses four classes. Each class has one clear responsibility so that scheduling logic stays separate from data storage.

Owner
Holds the owner's name, total time available in the day (in minutes), and any preferences (such as preferring morning walks). This class is purely a data container — it makes no decisions. The scheduler reads from it to understand constraints.

Pet
Holds the pet's name, species, and age. Also holds a reference to its Owner. Like Owner, this is a data class. Species and age could later inform default task recommendations, but for now they are stored without driving logic.

Task
Represents a single care activity. Attributes: name (str), duration_minutes (int), priority (int, 1–3 where 1 is highest), and category (str, e.g. "feeding", "walk", "medication"). This class knows nothing about scheduling — it only describes what a task is.

Scheduler
This is where all the logic lives. It takes an Owner, a Pet, and a list of Task objects. Its main method — generate_plan() — sorts tasks by priority, fits them into the available time window, and returns a DailyPlan. If total task duration exceeds available time, lower-priority tasks are dropped and noted as skipped.

DailyPlan
A simple output object. Holds an ordered list of tasks that made it into the plan, a list of skipped tasks, the total scheduled duration, and a reasoning string that the UI can display to explain the decisions made.
Relationships: Pet has one Owner. Scheduler depends on Owner, Pet, and a list of Task objects. Scheduler produces one DailyPlan.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

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
