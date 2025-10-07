"""Workplan creation agent for consulting-style projects.

This module provides a command-line interface that guides a user through
creating a structured workplan, stores the plan as JSON, renders an HTML
"dashboard", and prompts for morning/evening status updates.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import textwrap
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "workplan.json"
DASHBOARD_FILE = Path("dashboard.html")

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"


def now() -> dt.datetime:
    """Return the current datetime without timezone information."""
    return dt.datetime.now().replace(microsecond=0)


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.strptime(value, ISO_FORMAT)


def to_iso(value: dt.datetime) -> str:
    return value.strftime(ISO_FORMAT)


def slugify(value: str) -> str:
    return "-".join(
        "".join(ch for ch in part.lower() if ch.isalnum())
        for part in value.split()
        if part
    ) or "section"


def stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    slug = slugify(text)
    return f"{prefix}-{slug}-{digest}" if slug else f"{prefix}-{digest}"


KEY_QUESTIONS = [
    (
        "objective",
        "What is the primary objective or desired outcome for '{task}'?",
    ),
    (
        "stakeholders",
        "Who are the executive sponsors and day-to-day stakeholders?",
    ),
    (
        "deadline",
        "What timeline or deadline constraints should we plan for?",
    ),
    (
        "deliverables",
        "What are the must-have deliverables or decision points?",
    ),
    (
        "data_sources",
        "What data sources, systems, or subject matter experts are required?",
    ),
    (
        "risks",
        "What risks, blockers, or open questions need to be monitored?",
    ),
    (
        "team",
        "Who will execute the work (internal team, client resources, vendors)?",
    ),
]


@dataclass
class Step:
    description: str
    hours: float
    status: str = "Not Started"
    notes: str = ""
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = stable_id("step", self.description)


@dataclass
class Component:
    name: str
    focus: str
    steps: List[Step]
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = stable_id("component", self.name)

    @property
    def total_hours(self) -> float:
        return sum(step.hours for step in self.steps)


@dataclass
class UpdateRecord:
    label: str
    timestamp: str
    updates: List[Dict[str, str]]


@dataclass
class Workplan:
    task: str
    answers: Dict[str, str]
    components: List[Component]
    created_at: str
    last_updated: str
    next_updates: List[Dict[str, str]]
    update_history: List[UpdateRecord] = field(default_factory=list)

    @property
    def total_hours(self) -> float:
        return sum(component.total_hours for component in self.components)

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "answers": self.answers,
            "components": [
                {
                    "id": component.id,
                    "name": component.name,
                    "focus": component.focus,
                    "steps": [asdict(step) for step in component.steps],
                    "total_hours": component.total_hours,
                }
                for component in self.components
            ],
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "next_updates": self.next_updates,
            "total_hours": self.total_hours,
            "update_history": [asdict(record) for record in self.update_history],
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "Workplan":
        components = [
            Component(
                id=item.get("id", stable_id("component", item["name"])),
                name=item["name"],
                focus=item.get("focus", ""),
                steps=[
                    Step(
                        id=step.get("id", stable_id("step", step["description"])),
                        description=step["description"],
                        hours=step["hours"],
                        status=step.get("status", "Not Started"),
                        notes=step.get("notes", ""),
                    )
                    for step in item["steps"]
                ],
            )
            for item in payload["components"]
        ]
        update_history = [
            UpdateRecord(
                label=record["label"],
                timestamp=record["timestamp"],
                updates=record.get("updates", []),
            )
            for record in payload.get("update_history", [])
        ]
        return cls(
            task=payload["task"],
            answers=payload["answers"],
            components=components,
            created_at=payload["created_at"],
            last_updated=payload["last_updated"],
            next_updates=payload["next_updates"],
            update_history=update_history,
        )


def ask_questions(task: str) -> Dict[str, str]:
    print("\nLet's define the project so we can build a consulting-ready workplan.\n")
    answers: Dict[str, str] = {}
    for key, prompt in KEY_QUESTIONS:
        question = prompt.format(task=task)
        response = input(f"{question}\n> ").strip()
        if not response:
            response = "No response provided."
        answers[key] = response
        print()
    return answers


def base_components(task: str, answers: Dict[str, str]) -> List[Component]:
    objective = answers.get("objective", "the project")
    stakeholders = answers.get("stakeholders", "stakeholders")
    deliverables = answers.get("deliverables", "defined deliverables")
    data_sources = answers.get("data_sources", "required data sources")
    risks = answers.get("risks", "defined risks")
    deadline = answers.get("deadline", "the agreed timeline")
    team = answers.get("team", "the project team")

    return [
        Component(
            name="Discovery & Alignment",
            focus=(
                f"Confirm scope, success metrics, and expectations for {task} "
                f"with {stakeholders}."
            ),
            steps=[
                Step(
                    description=(
                        f"Kickoff with sponsors to confirm the objective — {objective} — "
                        "and success measures."
                    ),
                    hours=2.0,
                ),
                Step(
                    description=(
                        f"Document current context, stakeholder map ({stakeholders}), "
                        "and decision cadence."
                    ),
                    hours=1.5,
                ),
                Step(
                    description="Finalize problem statement, decision rights, and engagement guardrails.",
                    hours=1.5,
                ),
            ],
        ),
        Component(
            name="Current State & Data Assessment",
            focus=(
                f"Inventory existing processes, technology, and data needed from {data_sources}."
            ),
            steps=[
                Step(
                    description="Conduct working sessions to map current workflows and tooling.",
                    hours=3.0,
                ),
                Step(
                    description=(
                        f"Audit data availability, quality, and access requirements across {data_sources}."
                    ),
                    hours=2.5,
                ),
                Step(
                    description="Synthesize findings into opportunity brief and assumptions log.",
                    hours=2.0,
                ),
            ],
        ),
        Component(
            name="Solution Design",
            focus=(
                f"Translate insights into a future-state design and prioritize deliverables ({deliverables})."
            ),
            steps=[
                Step(
                    description=(
                        f"Define user stories, success metrics, and experience flows that deliver {objective}."
                    ),
                    hours=3.5,
                ),
                Step(
                    description=(
                        f"Draft architecture / operating model options and review with {stakeholders}."
                    ),
                    hours=4.0,
                ),
                Step(
                    description="Create implementation roadmap with phased milestones and dependencies.",
                    hours=3.0,
                ),
            ],
        ),
        Component(
            name="Build & Iterate",
            focus=(
                f"Develop prioritized workstreams with {team}, validate with pilot users, "
                "and incorporate feedback."
            ),
            steps=[
                Step(
                    description=(
                        "Stand up development environment, assign owners, and confirm sprint logistics."
                    ),
                    hours=4.0,
                ),
                Step(
                    description=(
                        f"Execute build sprints with weekly showcases and backlog grooming to meet {deadline}."
                    ),
                    hours=8.0,
                ),
                Step(
                    description="Run pilot / UAT sessions and capture iteration requirements.",
                    hours=4.0,
                ),
            ],
        ),
        Component(
            name="Enablement & Change Management",
            focus=(
                "Equip stakeholders with training, documentation, and support for adoption."
            ),
            steps=[
                Step(
                    description="Develop enablement materials and training curriculum.",
                    hours=3.0,
                ),
                Step(
                    description="Facilitate training sessions and gather readiness feedback.",
                    hours=2.5,
                ),
                Step(
                    description="Finalize support model and handoff documentation.",
                    hours=2.0,
                ),
            ],
        ),
        Component(
            name="Measurement & Iteration",
            focus=(
                f"Define operating rhythms to monitor outcomes, risks ({risks}), and backlog refinements."
            ),
            steps=[
                Step(
                    description="Launch performance dashboard and baseline key metrics.",
                    hours=2.5,
                ),
                Step(
                    description="Run retrospective to capture lessons learned and enhancement backlog.",
                    hours=2.0,
                ),
                Step(
                    description="Plan next-wave initiatives aligned to strategic objectives.",
                    hours=1.5,
                ),
            ],
        ),
    ]


def default_update_schedule(reference: Optional[dt.datetime] = None) -> List[Dict[str, str]]:
    reference = reference or now()
    schedule = []
    for label, hour in [("Morning check-in", 9), ("Evening wrap-up", 17)]:
        target = reference.replace(hour=hour, minute=0, second=0)
        if target <= reference:
            target += dt.timedelta(days=1)
        schedule.append({"label": label, "scheduled_for": to_iso(target)})
    return schedule


def create_workplan(task: str) -> Workplan:
    answers = ask_questions(task)
    components = base_components(task, answers)
    created = to_iso(now())
    plan = Workplan(
        task=task,
        answers=answers,
        components=components,
        created_at=created,
        last_updated=created,
        next_updates=default_update_schedule(),
    )
    save_workplan(plan)
    render_dashboard(plan)
    print("\nWorkplan created and saved to data/workplan.json.")
    print("Dashboard generated at dashboard.html.\n")
    print(summary(plan))
    return plan


def summary(plan: Workplan) -> str:
    total_hours = plan.total_hours
    lines = [
        f"Task: {plan.task}",
        f"Total estimated effort: {total_hours:.1f} hours",
        "Components:",
    ]
    for component in plan.components:
        lines.append(
            f"  - {component.name}: {component.total_hours:.1f} hours across {len(component.steps)} steps"
        )
    return "\n".join(lines)


def save_workplan(plan: Workplan) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as fh:
        json.dump(plan.to_dict(), fh, indent=2)


def load_workplan() -> Workplan:
    if not DATA_FILE.exists():
        raise FileNotFoundError("No workplan found. Run 'create' first.")
    with DATA_FILE.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return Workplan.from_dict(payload)


def prompt_for_updates(plan: Workplan, label: str) -> None:
    print(f"\n=== {label.upper()} STATUS UPDATE ===")
    updated_steps: List[Dict[str, str]] = []
    for component in plan.components:
        print(f"\n{component.name} — {component.focus}")
        for step in component.steps:
            print(
                textwrap.fill(
                    f"• {step.description} (Estimated {step.hours:.1f}h, Status: {step.status})",
                    width=88,
                )
            )
            status = input("  New status (press enter to keep current): ").strip()
            notes = input("  Notes / blockers (optional): ").strip()
            if status:
                step.status = status
            if notes:
                step.notes = notes
            if status or notes:
                updated_steps.append(
                    {
                        "component": component.name,
                        "step": step.description,
                        "status": step.status,
                        "notes": step.notes,
                    }
                )
        print()
    if updated_steps:
        record = UpdateRecord(
            label=label,
            timestamp=to_iso(now()),
            updates=updated_steps,
        )
        plan.update_history.append(record)
        plan.last_updated = record.timestamp
        print(f"Recorded {len(updated_steps)} updates.")
    else:
        print("No changes captured this round.")


def roll_next_update(schedule_entry: Dict[str, str]) -> None:
    current = parse_time(schedule_entry["scheduled_for"])
    next_timepoint = current + dt.timedelta(days=1)
    schedule_entry["scheduled_for"] = to_iso(next_timepoint)


def run_updates_if_due(plan: Workplan) -> bool:
    current_time = now()
    updates_due = [
        entry for entry in plan.next_updates if parse_time(entry["scheduled_for"]) <= current_time
    ]
    if not updates_due:
        return False
    for entry in updates_due:
        prompt_for_updates(plan, entry["label"])
        roll_next_update(entry)
    save_workplan(plan)
    render_dashboard(plan)
    return True


def render_dashboard(plan: Workplan) -> None:
    DASHBOARD_FILE.write_text(build_dashboard_html(plan), encoding="utf-8")


def build_dashboard_html(plan: Workplan) -> str:
    key_details = "".join(
        f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        for key, value in plan.answers.items()
    )
    components_html = "".join(
        f"""
        <section class=\"component\" id=\"{component.id}\">
          <h2>{component.name}</h2>
          <p class=\"focus\">{component.focus}</p>
          <table>
            <thead>
              <tr>
                <th>Step</th>
                <th>Estimated Hours</th>
                <th>Status</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {''.join(
                f"<tr><td>{step.description}</td><td>{step.hours:.1f}</td><td>{step.status}</td><td>{step.notes or '&mdash;'}</td></tr>"
                for step in component.steps
              )}
            </tbody>
            <tfoot>
              <tr>
                <td>Total</td>
                <td>{component.total_hours:.1f}</td>
                <td colspan=\"2\"></td>
              </tr>
            </tfoot>
          </table>
        </section>
        """
        for component in plan.components
    )

    history_html = "".join(
        f"""
        <article>
          <h3>{record.label} — {record.timestamp}</h3>
          <ul>
            {''.join(
              f"<li><strong>{update['component']}</strong>: {update['step']}<br />"
              f"Status: {update['status']}<br />Notes: {update['notes'] or '&mdash;'}</li>"
              for update in record.updates
            )}
          </ul>
        </article>
        """
        for record in plan.update_history
    ) or "<p>No updates captured yet. Run the agent for your next check-in.</p>"

    schedule_html = "".join(
        f"<li>{entry['label']}: {entry['scheduled_for']}</li>" for entry in plan.next_updates
    )

    return f"""
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Workplan Dashboard</title>
    <link rel=\"stylesheet\" href=\"style.css\" />
  </head>
  <body class=\"dashboard\">
    <header>
      <h1>Workplan Dashboard</h1>
      <p class=\"task\">{plan.task}</p>
      <div class=\"meta\">
        <span>Created: {plan.created_at}</span>
        <span>Last updated: {plan.last_updated}</span>
        <span>Total estimated effort: {plan.total_hours:.1f} hours</span>
      </div>
    </header>
    <main>
      <section class=\"overview\">
        <h2>Key Inputs</h2>
        <ul>
          {key_details}
        </ul>
      </section>
      <section class=\"schedule\">
        <h2>Next Check-Ins</h2>
        <ul>{schedule_html}</ul>
      </section>
      {components_html}
      <section class=\"history\">
        <h2>Update History</h2>
        {history_html}
      </section>
    </main>
  </body>
</html>
"""


def show(plan: Workplan) -> None:
    print(summary(plan))
    print("\nNext check-ins:")
    for entry in plan.next_updates:
        print(f"  - {entry['label']}: {entry['scheduled_for']}")
    print("\nDashboard location: dashboard.html")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Workplan creation agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a new workplan")
    create_parser.add_argument("task", help="High-level task or project description")

    subparsers.add_parser("show", help="Show a summary of the existing workplan")
    subparsers.add_parser("run", help="Run scheduled updates if they are due")
    subparsers.add_parser("update", help="Force a status update regardless of schedule")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "create":
        create_workplan(args.task)
        return

    plan = load_workplan()
    if args.command == "show":
        show(plan)
    elif args.command == "run":
        if run_updates_if_due(plan):
            print("\nUpdates captured and dashboard refreshed.")
        else:
            print("No updates due right now. Next check-ins:")
            for entry in plan.next_updates:
                print(f"  - {entry['label']}: {entry['scheduled_for']}")
    elif args.command == "update":
        prompt_for_updates(plan, "Ad-hoc update")
        save_workplan(plan)
        render_dashboard(plan)
        print("Update saved and dashboard refreshed.")


if __name__ == "__main__":
    main()
