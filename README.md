# Workplan Creation Agent

This repository now includes a command-line agent that will turn a high-level
engagement idea into a consulting-style workplan, capture status updates twice
a day, and render a shareable dashboard.

## Features

* **Structured discovery prompts** – answer a short list of questions so the
  agent can tailor deliverables, stakeholders, timelines, and risks to your
  project.
* **Auto-generated plan** – the agent breaks work into major components,
  creates granular steps with hour estimates, and totals the effort required.
* **Morning and evening nudges** – each time you run the agent it checks if the
  9am or 5pm check-in is due, collects progress, and re-schedules the next
  reminder.
* **Dashboard output** – your plan, next check-ins, and update history are
  published to `dashboard.html` so it can be viewed or shared instantly.

## Getting Started

1. **Create a plan**

   ```bash
   python workplan_agent.py create "Build automated staffing dashboard to track utilization"
   ```

   Answer the prompts (objective, stakeholders, timeline, etc.). A JSON record
   is written to `data/workplan.json` and the dashboard is generated.

2. **View the dashboard** – open `dashboard.html` in a browser to see the full
   component breakdown, step-by-step plan, and total effort.

3. **Capture updates**

   ```bash
   python workplan_agent.py run
   ```

   If the morning or evening window has passed, the agent will walk through
   each step and collect status/notes before rolling the reminder forward to
   the next day.

4. **Ad-hoc updates** – run `python workplan_agent.py update` whenever you need
   to log progress outside of the scheduled windows.

5. **Check the schedule** – use `python workplan_agent.py show` to display a
   concise summary and the next planned check-ins.

To automate morning and evening prompts, place the `python workplan_agent.py
run` command in your operating system's scheduled tasks (e.g., cron, Task
Scheduler). Each run will only request input when a check-in is due.
