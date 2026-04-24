#!/usr/bin/env python3
"""
Memento Mori state and life-in-weeks calculations.

Commands:
  python scripts/life_stats.py read
  python scripts/life_stats.py checkin
  python scripts/life_stats.py setup --birthdate 1995-03-15 --life-expectancy-years 85
  python scripts/life_stats.py journal --entry "..." --summary "..."
  python scripts/life_stats.py log --last-n 10
  python scripts/life_stats.py stats --last-n 12
  python scripts/life_stats.py review --year 2026
  python scripts/life_stats.py config show
  python scripts/life_stats.py config set --checkin-style stoic
  python scripts/life_stats.py export --format markdown --out journal.md
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any


DEFAULT_STATE_FILE = Path.home() / ".openclaw" / "skills" / "memento-mori" / "state.json"
STATE_FILE = Path(os.environ.get("MEMENTO_MORI_STATE", DEFAULT_STATE_FILE)).expanduser()
ROUND_WEEK_MILESTONES = (500, 1000, 1500, 2000, 2500, 3000, 3500, 4000)
PERCENT_MILESTONES = (25, 50, 75)
BAR_WIDTH = 32
DEFAULT_CONFIG = {
    "checkin_style": "stoic",
    "preserve_raw_entries": True,
    "default_life_expectancy_years": 85,
}
STOPWORDS = {
    "the",
    "and",
    "that",
    "this",
    "with",
    "for",
    "was",
    "were",
    "are",
    "but",
    "you",
    "your",
    "我",
    "了",
    "的",
    "和",
    "是",
    "在",
    "这",
}


def default_state() -> dict[str, Any]:
    return {
        "profile": {"setup_complete": False},
        "config": dict(DEFAULT_CONFIG),
        "journal": {},
        "milestones_notified": [],
        "last_checkin": None,
        "total_checkins": 0,
    }


def load() -> dict[str, Any]:
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8-sig"))
    else:
        state = default_state()
    return migrate_state(state)


def migrate_state(state: dict[str, Any]) -> dict[str, Any]:
    migrated = default_state()
    migrated.update(state)
    migrated["config"] = {**DEFAULT_CONFIG, **state.get("config", {})}
    migrated.setdefault("profile", {"setup_complete": False})
    migrated.setdefault("journal", {})
    migrated.setdefault("milestones_notified", [])
    migrated.setdefault("last_checkin", None)
    migrated.setdefault("total_checkins", 0)
    return migrated


def save(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(migrate_state(state), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail("invalid_json", f"Could not parse command JSON: {exc.msg}")
    if not isinstance(parsed, dict):
        fail("invalid_args", "Command JSON must be an object.")
    return parsed


def parse_value(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def parse_command_args(raw_args: list[str]) -> dict[str, Any]:
    if not raw_args:
        return {}
    if raw_args[0].startswith("--"):
        parsed: dict[str, Any] = {}
        index = 0
        while index < len(raw_args):
            key = raw_args[index]
            if not key.startswith("--"):
                fail("invalid_args", f"Expected an option name, got {key}.")
            if index + 1 >= len(raw_args):
                fail("invalid_args", f"Missing value for {key}.")
            normalized = key[2:].replace("-", "_")
            value = parse_value(raw_args[index + 1])
            if normalized in {"life_expectancy_years", "default_life_expectancy_years", "last_n", "year"}:
                value = int(value)
            parsed[normalized] = value
            index += 2
        return parsed
    return parse_args_json(" ".join(raw_args))


def fail(code: str, message: str, status: int = 2) -> None:
    print(json.dumps({"error": code, "message": message}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(status)


def emit(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def add_years_safe(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def iso_week_key(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def week_index_from_key(week: str) -> int:
    match = re.fullmatch(r"(\d{4})-W(\d{2})", week)
    if not match:
        return -1
    return int(match.group(1)) * 100 + int(match.group(2))


def recent_week_keys(count: int, today: date | None = None) -> list[str]:
    today = today or date.today()
    week_start = today - timedelta(days=today.weekday())
    starts = [week_start - timedelta(weeks=offset) for offset in range(count - 1, -1, -1)]
    return [iso_week_key(day) for day in starts]


def iso_year_week_keys(year: int, today: date | None = None) -> list[str]:
    today = today or date.today()
    current_iso = today.isocalendar()
    if year > current_iso.year:
        return []
    if year == current_iso.year:
        last_week = current_iso.week
    else:
        last_week = date(year, 12, 28).isocalendar().week
    return [f"{year}-W{week:02d}" for week in range(1, last_week + 1)]


def is_birthday_this_week(today: date, birth: date) -> bool:
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    if birth.month == 2 and birth.day == 29:
        try:
            birthday = date(today.year, 2, 29)
        except ValueError:
            birthday = date(today.year, 2, 28)
    else:
        birthday = date(today.year, birth.month, birth.day)
    return week_start <= birthday <= week_end


def current_book_chapter(age_years: float, life_expectancy_years: int) -> int:
    if life_expectancy_years <= 0:
        return 1
    return max(1, min(10, int(age_years / life_expectancy_years * 10) + 1))


def milestone_id(milestone: dict[str, Any]) -> str:
    if milestone["type"] == "round_week":
        return f"round_week:{milestone['week']}"
    if milestone["type"] == "approaching_round":
        return f"approaching_round:{milestone['week']}:{milestone['weeks_away']}"
    if milestone["type"] == "birthday":
        return f"birthday:{milestone['age']}"
    if milestone["type"] == "quarter":
        return f"quarter:{milestone['pct']}"
    return json.dumps(milestone, sort_keys=True)


def compute(birthdate_str: str, life_expectancy_years: int, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    try:
        birth = date.fromisoformat(birthdate_str)
    except ValueError:
        fail("invalid_birthdate", "Birthdate must use YYYY-MM-DD format.")

    if birth > today:
        fail("invalid_birthdate", "Birthdate cannot be in the future.")
    if life_expectancy_years <= 0:
        fail("invalid_life_expectancy", "Life expectancy must be a positive number of years.")

    death_est = add_years_safe(birth, life_expectancy_years)
    days_lived = max(0, (today - birth).days)
    days_total = max(1, (death_est - birth).days)
    days_left = max(0, (death_est - today).days)
    weeks_lived = days_lived // 7
    weeks_total = days_total // 7
    weeks_left = days_left // 7
    age_years = days_lived / 365.2425
    pct_done_raw = days_lived / days_total * 100
    pct_done = round(min(100, max(0, pct_done_raw)), 1)
    filled = min(BAR_WIDTH, max(0, round(pct_done / 100 * BAR_WIDTH)))

    milestones: list[dict[str, Any]] = []
    for week in ROUND_WEEK_MILESTONES:
        if weeks_lived == week:
            milestones.append({"type": "round_week", "week": week})
        elif 0 < week - weeks_lived <= 4:
            milestones.append({"type": "approaching_round", "week": week, "weeks_away": week - weeks_lived})

    if is_birthday_this_week(today, birth):
        milestones.append({"type": "birthday", "age": int(age_years)})

    yesterday_pct = max(0, (days_lived - 1) / days_total * 100)
    for pct in PERCENT_MILESTONES:
        if pct_done_raw >= pct > yesterday_pct:
            milestones.append({"type": "quarter", "pct": pct})

    return {
        "today": today.isoformat(),
        "birthdate": birthdate_str,
        "life_expectancy_years": life_expectancy_years,
        "estimated_end_date": death_est.isoformat(),
        "age_years": round(age_years, 1),
        "age_years_floor": int(age_years),
        "days_lived": days_lived,
        "days_left": days_left,
        "weeks_lived": weeks_lived,
        "weeks_left": weeks_left,
        "weeks_total": weeks_total,
        "pct_done": pct_done,
        "pct_done_display": round(pct_done),
        "progress_bar": "█" * filled + "░" * (BAR_WIDTH - filled),
        "current_week": iso_week_key(today),
        "book_chapter": current_book_chapter(age_years, life_expectancy_years),
        "milestones": milestones,
    }


def require_profile(state: dict[str, Any]) -> dict[str, Any]:
    profile = state.get("profile", {})
    if not profile.get("setup_complete"):
        emit({"error": "not_setup", "message": "Ask the user for birthdate and optional life expectancy."})
        raise SystemExit(0)
    return profile


def entry_raw(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("raw", entry.get("entry", "")))
    return str(entry or "")


def entry_summary(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("summary", entry.get("raw", entry.get("entry", ""))))
    return str(entry or "")


def entry_created_at(entry: Any) -> str | None:
    if isinstance(entry, dict):
        return entry.get("created_at")
    return None


def normalized_entry(entry: Any) -> dict[str, Any]:
    if isinstance(entry, dict):
        raw = str(entry.get("raw", entry.get("entry", ""))).strip()
        summary = str(entry.get("summary", raw)).strip()
        return {
            "raw": raw,
            "summary": summary,
            "created_at": entry.get("created_at"),
            "updated_at": entry.get("updated_at"),
        }
    raw = str(entry or "").strip()
    return {"raw": raw, "summary": raw, "created_at": None, "updated_at": None}


def sorted_weeks(journal: dict[str, Any]) -> list[str]:
    return sorted(journal.keys(), key=week_index_from_key)


def recent_journal(journal: dict[str, Any], count: int = 3) -> dict[str, Any]:
    return {week: normalized_entry(journal[week]) for week in sorted_weeks(journal)[-count:]}


def journal_slice(journal: dict[str, Any], last_n: int | None = None, year: int | None = None) -> dict[str, Any]:
    weeks = sorted_weeks(journal)
    if year is not None:
        prefix = f"{year}-W"
        weeks = [week for week in weeks if week.startswith(prefix)]
    if last_n is not None:
        weeks = weeks[-last_n:]
    return {week: normalized_entry(journal[week]) for week in weeks}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]{2,}|[\u4e00-\u9fff]{1,4}", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def journal_stats(journal: dict[str, Any], last_n: int | None = None, year: int | None = None) -> dict[str, Any]:
    if year is not None:
        weeks = iso_year_week_keys(year)
    elif last_n is not None:
        weeks = recent_week_keys(last_n)
    else:
        weeks = sorted_weeks(journal)

    entries = {week: normalized_entry(journal.get(week, {})) for week in weeks}
    non_empty = [week for week, entry in entries.items() if entry_raw(entry) or entry_summary(entry)]
    empty = [week for week, entry in entries.items() if not (entry_raw(entry) or entry_summary(entry))]
    counter: Counter[str] = Counter()
    for entry in entries.values():
        counter.update(tokenize(f"{entry_raw(entry)} {entry_summary(entry)}"))

    streak = 0
    for week in reversed(recent_week_keys(520)):
        entry = normalized_entry(journal.get(week, {}))
        if entry_raw(entry) or entry_summary(entry):
            streak += 1
        else:
            break

    return {
        "weeks_considered": len(weeks),
        "entries_written": len(non_empty),
        "empty_weeks": empty,
        "current_streak_weeks": streak,
        "coverage_pct": round((len(non_empty) / len(weeks) * 100), 1) if weeks else 0,
        "top_terms": [{"term": term, "count": count} for term, count in counter.most_common(12)],
    }


def month_from_iso_week(week: str) -> str:
    year, week_no = week.split("-W")
    monday = date.fromisocalendar(int(year), int(week_no), 1)
    return f"{monday.year}-{monday.month:02d}"


def cmd_read(args: dict[str, Any]) -> None:
    state = load()
    profile = require_profile(state)
    stats = compute(profile["birthdate"], int(profile.get("life_expectancy_years", 85)))
    notified = set(state.get("milestones_notified", []))
    new_milestones = [m for m in stats["milestones"] if milestone_id(m) not in notified]
    emit(
        {
            **stats,
            "new_milestones": new_milestones,
            "recent_journal": recent_journal(state.get("journal", {})),
            "last_checkin": state.get("last_checkin"),
            "total_checkins": state.get("total_checkins", 0),
            "config": state.get("config", {}),
        }
    )


def cmd_checkin(args: dict[str, Any]) -> None:
    state = load()
    profile = require_profile(state)
    stats = compute(profile["birthdate"], int(profile.get("life_expectancy_years", 85)))
    notified = set(state.get("milestones_notified", []))
    new_milestones = [m for m in stats["milestones"] if milestone_id(m) not in notified]
    if args.get("mark_milestones", True):
        notified.update(milestone_id(m) for m in new_milestones)
        state["milestones_notified"] = sorted(notified)
        save(state)
    emit(
        {
            **stats,
            "new_milestones": new_milestones,
            "recent_journal": recent_journal(state.get("journal", {})),
            "last_checkin": state.get("last_checkin"),
            "total_checkins": state.get("total_checkins", 0),
            "config": state.get("config", {}),
        }
    )


def cmd_setup(args: dict[str, Any]) -> None:
    birthdate = args.get("birthdate")
    if not birthdate:
        fail("missing_birthdate", "setup requires birthdate.")
    life_expectancy = int(args.get("life_expectancy_years", args.get("default_life_expectancy_years", 85)))
    stats = compute(str(birthdate), life_expectancy)

    state = load()
    state["profile"] = {
        "birthdate": str(birthdate),
        "life_expectancy_years": life_expectancy,
        "setup_complete": True,
    }
    state.setdefault("journal", {})
    state.setdefault("total_checkins", 0)
    state.setdefault("last_checkin", None)
    state.setdefault("milestones_notified", [])
    state["config"] = {**DEFAULT_CONFIG, **state.get("config", {})}
    save(state)
    emit({"status": "ok", **stats})


def cmd_journal(args: dict[str, Any]) -> None:
    week = args.get("week") or iso_week_key(date.today())
    raw = str(args.get("raw", args.get("raw_entry", args.get("entry", "")))).strip()
    summary = str(args.get("summary", args.get("summary_entry", raw))).strip()
    if not isinstance(week, str) or not week:
        fail("invalid_week", "week must be a non-empty ISO week string.")
    now = date.today().isoformat()

    state = load()
    existing = normalized_entry(state.setdefault("journal", {}).get(week, {}))
    created_at = existing.get("created_at") or now
    state["journal"][week] = {
        "raw": raw,
        "summary": summary,
        "created_at": created_at,
        "updated_at": now,
    }
    state["last_checkin"] = now
    state["total_checkins"] = int(state.get("total_checkins", 0)) + 1
    save(state)
    emit({"status": "ok", "week": week, "entry": state["journal"][week]})


def cmd_log(args: dict[str, Any]) -> None:
    state = load()
    journal = state.get("journal", {})
    last_n = args.get("last_n")
    year = args.get("year")
    result = journal_slice(journal, last_n=int(last_n) if last_n is not None else None, year=int(year) if year else None)
    emit({"journal": result, "total_entries": len(result)})


def cmd_stats(args: dict[str, Any]) -> None:
    state = load()
    last_n = args.get("last_n")
    year = args.get("year")
    emit(
        {
            "stats": journal_stats(
                state.get("journal", {}),
                last_n=int(last_n) if last_n is not None else None,
                year=int(year) if year else None,
            )
        }
    )


def cmd_review(args: dict[str, Any]) -> None:
    state = load()
    year = int(args.get("year", date.today().year))
    entries = journal_slice(state.get("journal", {}), year=year)
    monthly_counts: Counter[str] = Counter()
    for week, entry in entries.items():
        if entry_raw(entry) or entry_summary(entry):
            monthly_counts[month_from_iso_week(week)] += 1
    emit(
        {
            "year": year,
            "stats": journal_stats(state.get("journal", {}), year=year),
            "monthly_counts": dict(sorted(monthly_counts.items())),
            "entries": entries,
            "review_prompt": "Use these entries to write a calm annual review. Preserve concrete details; do not turn it into productivity advice.",
        }
    )


def cmd_config(args: dict[str, Any]) -> None:
    state = load()
    action = args.get("action", "show")
    if action == "show":
        emit({"profile": state.get("profile", {}), "config": state.get("config", {})})
        return
    if action != "set":
        fail("invalid_config_action", "config action must be show or set.")

    config = {**DEFAULT_CONFIG, **state.get("config", {})}
    profile = state.get("profile", {})
    for key in ("checkin_style", "preserve_raw_entries", "default_life_expectancy_years"):
        if key in args:
            config[key] = args[key]
    if "life_expectancy_years" in args:
        profile["life_expectancy_years"] = int(args["life_expectancy_years"])
    if "birthdate" in args:
        profile["birthdate"] = str(args["birthdate"])
    if profile.get("birthdate"):
        profile["setup_complete"] = True
    state["config"] = config
    state["profile"] = profile
    save(state)
    emit({"status": "ok", "profile": profile, "config": config})


def export_markdown(state: dict[str, Any]) -> str:
    profile = state.get("profile", {})
    stats = journal_stats(state.get("journal", {}))
    lines = [
        "# Memento Mori Journal",
        "",
        f"- Birthdate: {profile.get('birthdate', 'unknown')}",
        f"- Life expectancy: {profile.get('life_expectancy_years', 85)} years",
        f"- Total check-ins: {state.get('total_checkins', 0)}",
        f"- Entries written: {stats['entries_written']}",
        f"- Current streak: {stats['current_streak_weeks']} weeks",
        "",
        "## Entries",
        "",
    ]
    journal = state.get("journal", {})
    for week in sorted_weeks(journal):
        entry = normalized_entry(journal[week])
        summary = entry_summary(entry) or "—"
        lines.append(f"- **{week}**: {summary}")
        raw = entry_raw(entry)
        if raw and raw != summary:
            lines.append(f"  - Raw: {raw}")
    return "\n".join(lines) + "\n"


def cmd_export(args: dict[str, Any]) -> None:
    fmt = str(args.get("format", "markdown")).lower()
    state = load()
    if fmt == "json":
        output = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    elif fmt == "markdown":
        output = export_markdown(state)
    else:
        fail("invalid_format", "export format must be markdown or json.")

    out = args.get("out")
    if out:
        path = Path(str(out)).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        emit({"status": "ok", "path": str(path), "format": fmt})
        return
    print(output, end="")


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "read"
    raw_args = argv[2:]
    if command == "config" and raw_args and not raw_args[0].startswith("--") and not raw_args[0].startswith("{"):
        action = raw_args[0]
        args = parse_command_args(raw_args[1:])
        args["action"] = action
    else:
        args = parse_command_args(raw_args)

    commands = {
        "read": lambda: cmd_read(args),
        "checkin": lambda: cmd_checkin(args),
        "setup": lambda: cmd_setup(args),
        "journal": lambda: cmd_journal(args),
        "log": lambda: cmd_log(args),
        "stats": lambda: cmd_stats(args),
        "summary": lambda: cmd_stats(args),
        "review": lambda: cmd_review(args),
        "config": lambda: cmd_config(args),
        "export": lambda: cmd_export(args),
    }
    if command not in commands:
        fail("unknown_command", f"Unknown command: {command}")
    commands[command]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
