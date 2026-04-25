# OpenClaw Installation And Scheduling

Use this reference when the user asks how to install or schedule the skill.

## Suggested Location

For a user-level install, place the skill folder at:

```text
~/.openclaw/skills/memento-mori
```

For a workspace install, place it under the workspace skills directory, for example:

```text
~/.openclaw/workspace/skills/memento-mori
```

The folder may use a hyphenated slug (`memento-mori`) while the `SKILL.md` frontmatter uses the OpenClaw skill name `memento_mori`.

The state file defaults to:

```text
~/.openclaw/skills/memento-mori/state.json
```

To keep state somewhere else, set:

```bash
MEMENTO_MORI_STATE=/path/to/state.json
```

## Manual Setup

From the skill folder:

```bash
python scripts/life_stats.py setup --birthdate 1995-03-15 --life-expectancy-years 85
python scripts/life_stats.py read
```

PowerShell uses the same option form:

```powershell
python scripts\life_stats.py setup --birthdate 1995-03-15 --life-expectancy-years 85
python scripts\life_stats.py read
```

Useful checks:

```bash
python scripts/life_stats.py journal --entry "This week had one thing worth keeping." --summary "Kept one thing from the week."
python scripts/life_stats.py share
python scripts/life_stats.py share --format svg --out card.svg
python scripts/life_stats.py stats --last-n 12
python scripts/life_stats.py review --year 2026
python scripts/life_stats.py export --format markdown --out journal.md
```

## Weekly Reminder

Use OpenClaw cron when the user wants the skill to proactively check in. Manual use does not require cron.

Example OpenClaw cron job:

```bash
openclaw cron add \
  --name "memento-mori-weekly" \
  --cron "0 21 * * 0" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "Use $memento_mori for the weekly check-in. Run checkin, mention at most one new milestone, then ask one short reflection question." \
  --announce \
  --channel last
```

This means every Sunday at 21:00 in the host machine's configured timezone.

If the host uses another scheduler, preserve the same intent: one weekly reminder, preferably Sunday evening, with a message that explicitly invokes `$memento_mori`.

## Privacy And Safety

The script stores data locally in `state.json` and does not make network requests.

Because this skill discusses mortality, do not use countdown framing when the user expresses self-harm intent, suicidal thoughts, immediate danger, or severe hopelessness. In those cases, use supportive crisis-safe language and encourage immediate real-world help.
