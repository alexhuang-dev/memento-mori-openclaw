---
name: memento_mori
description: Personal memento mori and life-in-weeks journaling ritual for OpenClaw. Use when the user asks about remaining lifetime, life calendar, memento mori, death countdown, "how many weeks do I have left", weekly reflection/check-ins, life milestones, setup with birthdate/life expectancy, viewing or exporting life journal entries, saving a remembered moment, shareable life cards, annual review, recent-week summary, streaks, or configuring the reminder style.
metadata:
  openclaw:
    requires:
      bins:
        - python
---

# Memento Mori

Use this OpenClaw skill to help the user see life as a finite number of weeks and turn weekly reflection into a cumulative journal. Treat it as an AI companion ritual, not a productivity tracker. Be direct about mortality, but keep the tone calm, grounded, and non-dramatic.

Use OpenClaw's shell/exec capability to run `scripts/life_stats.py`; do not rely on Codex-specific metadata.

## Safety Boundary

If the user expresses self-harm intent, suicidal thoughts, immediate danger, or strong hopelessness, pause the death-countdown framing. Do not show remaining weeks, mortality statistics, or milestone pressure. Respond supportively, encourage contacting a trusted person immediately, and direct them to local emergency services or a crisis hotline. After the user is stable, offer to use the journal only as a gentle grounding log.

## Core Workflow

1. Use `scripts/life_stats.py` for state reads, calculations, journal writes, summaries, reviews, config, and exports.
2. Prefer option arguments over JSON in OpenClaw because they quote safely across shells.
3. If `read` or `checkin` returns `{"error":"not_setup"}`, ask for the user's birthdate and optional life expectancy. Use 85 years when the user does not provide one.
4. After setup or read, present the life overview in plain text, not a Markdown table.
5. For weekly check-ins, run `checkin`, mention at most one `new_milestones` item, ask exactly one question, wait for the user, then save both raw text and a concise faithful summary.
6. For journal queries, preserve the user's wording. Use summaries only for compact display.

Read `references/philosophy.md` when tone matters or the user is emotionally sensitive. Read `references/install.md` when the user asks how to install, schedule, or configure the skill.

## Script Commands

```bash
python scripts/life_stats.py read
python scripts/life_stats.py checkin
python scripts/life_stats.py setup --birthdate 1995-03-15 --life-expectancy-years 85
python scripts/life_stats.py journal --week 2026-W17 --entry "I finished the first version." --summary "Finished the first version."
python scripts/life_stats.py log --last-n 10
python scripts/life_stats.py stats --last-n 12
python scripts/life_stats.py review --year 2026
python scripts/life_stats.py share
python scripts/life_stats.py share --format svg --out card.svg
python scripts/life_stats.py config show
python scripts/life_stats.py config set --life-expectancy-years 90 --checkin-style sharp
python scripts/life_stats.py export --format markdown --out journal.md
```

JSON arguments also work when the shell supports safe quoting.

The script stores state in `~/.openclaw/skills/memento-mori/state.json` by default. For testing or custom installs, set `MEMENTO_MORI_STATE` to another JSON file path.

## State Shape

New entries preserve both the user's original words and an agent summary:

```json
{
  "profile": {
    "birthdate": "1995-03-15",
    "life_expectancy_years": 85,
    "setup_complete": true
  },
  "config": {
    "checkin_style": "stoic",
    "preserve_raw_entries": true,
    "default_life_expectancy_years": 85
  },
  "journal": {
    "2026-W17": {
      "raw": "This week I rebuilt the skill and felt strangely calm.",
      "summary": "Rebuilt the skill and felt calm.",
      "created_at": "2026-04-24",
      "updated_at": "2026-04-24"
    }
  },
  "milestones_notified": ["birthday:31"],
  "last_checkin": "2026-04-24",
  "total_checkins": 12
}
```

The script still reads older string-only journal entries.

## First Use

When setup is missing:

1. Explain briefly: this keeps a life-in-weeks overview and a weekly memory log.
2. Ask for birthdate in `YYYY-MM-DD` format and optional life expectancy. Say 85 is a default assumption, not a prediction.
3. Run `setup`.
4. Show the overview.
5. Ask: `你来到这里的第一周，想留下什么？`

## Weekly Check-In

On a scheduled reminder:

1. Run `python scripts/life_stats.py checkin`.
2. If `new_milestones` is not empty, mention only the first meaningful milestone.
3. Prefer the returned `suggested_opening` unless the user has clearly asked for a different voice.
4. After the user replies, call `journal` with:
   - `--entry`: the user's original wording, lightly cleaned only if needed.
   - `--summary`: one faithful sentence, no embellishment.

Good openings:

- `stoic`: `第 1,549 周。还剩 2,203 周。这一周是否值得记录？`
- `gentle`: `这一周也走到尾声了。普通的一周也可以被留下来。一句话就好。`
- `sharp`: `你没有失去一天。你失去的是这一整周。要留下些什么吗？`
- `poetic`: `这一格，要留下什么？`
- `minimal`: `第 1,549 周。还剩 2,203 周。留下些什么？`

Avoid emojis, cheerleading, long comfort, productivity advice, and lines like `你还有很多时间`.

## Overview Format

After `read` or `setup`, present a compact plain-text overview:

```text
你已经活了 10,847 天，第 1,549 周。

还剩大约 2,203 周。

如果把这些周排成一排，
已经用掉的是 ████████████████░░░░░░░░░░░░░░░░ 41%

今年你 29 岁。
如果人生是一本书，你刚翻完第 3 章。

————

最近写下的：
W1547: "第一次独立完成了一个完整项目"
W1548: —
W1549: （等你写）
```

Rules:

- Use `█` and `░` for the progress bar, no more than 32 cells.
- Show a whole-number percentage.
- Show at most 3 recent journal entries.
- Display empty entries as `—`.
- Keep the voice sober and gentle.

## Milestones

Use `checkin` for scheduled reminders because it returns only unannounced `new_milestones` and marks them as notified.

- `round_week`: `今天是你的第 N 周。整数的重量。`
- `approaching_round`: `再过 N 周，你将到达第 X 周。`
- `birthday`: `这周你又大了一岁。`
- `quarter`: `你刚刚用完了人生的四分之一。` Adjust naturally for 50% or 75%.

Do not over-explain milestones.

## Reviews And Summaries

- Recent pattern: run `stats --last-n 12`, then summarize coverage, streak, empty weeks, and recurring terms.
- Annual review: run `review --year YYYY`, then write a calm year-in-review using concrete entries. Do not turn it into productivity advice.
- Journal browsing: run `log --last-n N` or `log --year YYYY`.

## Share Cards

Use `share` when the user asks to share, screenshot, post, or show their life calendar.

```bash
python scripts/life_stats.py share
python scripts/life_stats.py share --format svg --out card.svg
```

For text output, present it as a compact card. For SVG output, tell the user where the file was written. Do not include private journal entries unless the user explicitly asked to share them.

## Configuration

Use `config show` to inspect profile and behavior. Use `config set` for changes:

```bash
python scripts/life_stats.py config set --life-expectancy-years 90
python scripts/life_stats.py config set --checkin-style sharp
```

Supported public `checkin_style` values are informal guidance for the agent: `stoic`, `gentle`, `sharp`, `poetic`, and `minimal`. Prefer `sharp` when the user wants the most shareable, screenshot-friendly reminder voice. `terse` remains accepted as a legacy/internal compatibility style, but do not recommend it in user-facing docs.

## User Intents

- Remaining time or life overview: run `read`, then show the overview.
- Setup or update birthdate/life expectancy: run `setup` or `config set`, then show the overview.
- Save this week: run `journal`; if no week is specified, let the script use the current ISO week.
- View journal: run `log`, optionally with `last_n` or `year`.
- Share life card: run `share`, optionally with `format=svg` and `out`.
- Recent summary: run `stats`, then explain patterns briefly.
- Annual review: run `review`, then synthesize the year from the entries.
- Export journal: run `export` with `format` set to `markdown` or `json`; use `--out` when the user asks for a file.
