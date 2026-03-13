---
description: Generate a training report with trend analysis, drills and session plan from last 4 matches
argument-hint: [optional focus area, e.g. "defensive shape" or "finishing"]
allowed-tools: Bash, Read, WebSearch, Write
---

Generate a football training report for West Ryde Rovers FC All Age Women's 04.

## Step 1 — Setup

- Set `FOCUS_AREA` = `$ARGUMENTS` (may be empty)
- Set `TODAY` = today's date in YYYY-MM-DD format
- Set `OUTPUT_PATH` = `reports/training_report_TODAY.md`
- If `FOCUS_AREA` is non-empty, announce it: "Generating training report with focus on: FOCUS_AREA"

## Step 2 — Extract match data

Run the data extraction script:

```bash
cd "D:/Coding/Projects/WRAAWTeam" && python scripts/generate_training_data.py --output reports/.training_data_tmp.json
```

If `FOCUS_AREA` is set, append `--focus "FOCUS_AREA"` to the command.

Then read the resulting JSON file at `reports/.training_data_tmp.json`.

## Step 3 — Analyse the data

From the JSON payload:

- Note all `has_*` flags (has_notes, has_tags, has_player_notes, has_attendance, has_lineups)
- From `trend_stats`: identify the primary weakness
  - If `ga_avg` >= 2.0: defensive shape / conceding is the primary concern
  - If `gf_avg` <= 1.0: attacking / finishing is a secondary concern
  - Check `shutouts_conceded` (matches where we scored 0) and `shutouts_kept` (matches where we conceded 0)
- If `has_tags` = true: look for recurring tag patterns in the `tags` array
- If `has_notes` = true: extract coach themes from `notes` array (`key_themes_for`, `key_themes_against`, `focus_next_week`)
- Always frame context: this is a social AAW (All Age Women's) grade, recreational level, mixed ability squad

## Step 4 — Web research

Run 3 targeted web searches to source reputable training drills. Use these sources in preference order:
- UEFA: `uefa.com/insideuefa/football-development`
- The FA: `thefa.com/football-rules-governance/coaching`
- United Soccer Coaches: `unitedsoccercoaches.org`
- Coerver Coaching: `coerver.com`
- Coaches Voice: `coachesvoice.com`
- SoccerTutor: `soccertutor.com`

**Search 1 — Defensive drills:**

Primary query:
```
site:thefa.com OR site:uefa.com OR site:unitedsoccercoaches.org "women's football" training drills defensive shape social recreational
```
Fallback (if fewer than 2 drill-specific results):
```
site:thefa.com OR site:uefa.com OR site:unitedsoccercoaches.org football training drills defensive shape social recreational
```

**Search 2 — Attacking/finishing drills:**

Primary query:
```
site:coachesvoice.com OR site:soccertutor.com OR site:coerver.com football training finishing conversion recreational women
```
Fallback:
```
site:coachesvoice.com OR site:soccertutor.com OR site:coerver.com football training finishing conversion recreational
```

**Search 3 — Focus area or session structure:**

If `FOCUS_AREA` is set:
Primary query:
```
site:thefa.com OR site:unitedsoccercoaches.org OR site:soccertutor.com football training drills "FOCUS_AREA" women recreational
```
Fallback:
```
site:thefa.com OR site:unitedsoccercoaches.org OR site:soccertutor.com football training drills "FOCUS_AREA" social recreational
```

If `FOCUS_AREA` is not set:
Primary query:
```
site:thefa.com OR site:uefa.com OR site:unitedsoccercoaches.org women's football training session structure fun drills social
```
Fallback:
```
site:thefa.com OR site:uefa.com OR site:unitedsoccercoaches.org football training session structure fun drills social recreational
```

Use the fallback if the primary returns fewer than 2 results that describe a named drill with clear setup instructions (not just general articles).

For each search: extract 1–2 specific drills with:
- Drill name
- Description
- Equipment needed
- Suggested duration
- Source URL (cite the specific page; if no reputable source found, label as "general coaching guidance")

## Step 5 — Write the training report

Write the complete report to `OUTPUT_PATH` using the structure below.

---

```markdown
# Training Report — TODAY
**Team:** [team from JSON]
**Generated:** TODAY
**Matches analysed:** last [window] completed fixtures
[**Focus area:** FOCUS_AREA  ← only if set]

---

## Last [N] Matches — Summary

| Round | Date | Opponent | GF | GA | Result |
|-------|------|----------|----|----|--------|
[one row per match from JSON matches array]

**Form:** `[results_string]`
**Avg GF:** [gf_avg] | **Avg GA:** [ga_avg]

---

## Trend Analysis

[3–4 paragraphs covering:]
[1. Result direction — winning/losing streak, general pattern]
[2. Scoring trend — are we creating chances? scoring consistently?]
[3. Conceding trend — clean sheets, high-scoring losses, patterns]
[4. Standout result — best or most notable match in the window]

[If has_notes=false: "**Note on data:** Match notes are currently empty stubs. To enrich future reports, fill in `notes/match_notes.csv` — especially the `key_themes_for`, `key_themes_against`, and `focus_next_week` fields after each game."]
[If has_tags=false: "**Note on data:** No match tags have been entered yet. Adding tags to `notes/match_tags.csv` after each game (using the vocabulary in `docs/tag-dictionary.md`) will allow pattern analysis across matches."]

---

## Identified Strengths

[Bullet list of genuine positive moments from match data. Even in a losing run, find:]
- Any wins or draws in the window
- Matches where we scored 2+ goals
- Competitive scorelines (e.g. lost 1–2) vs heavy defeats
[If has_tags: reference specific positive tags]
[If has_notes: reference key_themes_for content]

---

## Areas for Improvement

[Up to 5 prioritised bullets with data evidence:]
1. [Primary — highest priority, data-backed]
2. [Secondary]
3. [etc.]

[If has_notes=false or has_tags=false: "Note: Analysis is based on scorelines only. Adding match notes and tags will provide deeper insight into specific tactical patterns."]

---

## Advice for the Coach

1. **Tactical suggestion:** [specific, actionable, based on trend analysis]
2. **Rotation & participation:** [ensure everyone gets game time — social grade priority]
3. **Morale note:** [honest acknowledgement of the run + positive framing]
4. **Pre-match prep:** [one specific thing to emphasise before next game]
5. **Something to celebrate:** [find something genuine to recognise]

---

## Message for the Team

[4–6 sentences written FROM the coach TO the players. Honest, positive, specific. No clichés like "give 110%" or "heart of a champion". Reference actual scorelines and opponents. Warm but direct tone.]

---

## Recommended Training Drills

[4–6 drills sourced from web research. For each drill:]

### [Drill Name]
- **Focus:** [e.g. Defensive shape / Pressing trigger / Finishing]
- **Duration:** [e.g. 15 minutes]
- **Players needed:** [e.g. 8–12]
- **Equipment:** [e.g. Cones, bibs, 1 ball per 4 players]
- **Difficulty:** [Beginner / Intermediate]

[2–3 sentence description of how to run the drill.]

**Why this drill:** [1 sentence linking directly to identified issue from trend analysis.]

**Source:** [URL or "General coaching guidance"]

---
[repeat for each drill]

[Include a mix: at least 2 defensive-themed + 2 attacking-themed + any focus-area-specific drills]

---

## Session Plan (60–75 minutes)

| Block | Theme | Duration | Activity |
|-------|-------|----------|----------|
| Warm-Up | Ball familiarity | 10 min | [ball-based warm-up activity, e.g. rondos or passing patterns] |
| Main Block 1 | [Primary Theme — defensive] | 20 min | [reference specific drill(s) from above] |
| Main Block 2 | [Secondary Theme — attacking] | 20 min | [reference specific drill(s) from above] |
| Scrimmage | Applied play | 15 min | Small-sided game (e.g. 5v5 or 6v6) with constraint: [theme-linked rule, e.g. "must win ball back within 5 seconds" or "goal only counts after 3 passes"] |
| Cool-Down | Recovery + reflection | 5 min | Light stretching + team reflection question: [e.g. "Name one thing a teammate did well today"] |

---
```

If `FOCUS_AREA` was provided, add this section after the Session Plan:

```markdown
## Deep Dive: FOCUS_AREA

### Why This Focus
[1–2 sentences connecting FOCUS_AREA to the match data — e.g. which matches showed this issue, what the scorelines suggest]

### Additional Drills

[2–3 additional drills sourced from the focus-area web search, using the same drill format as above]

### Integration into Session Plan
[1 short paragraph explaining how to substitute or extend the session plan to incorporate the focus-area drills]

---
```

Always end the report with:

```markdown
## Data Quality Note

**Data available for this report:**
- Match results: ✓ ([N] fixtures)
- Match notes: [✓ present / ✗ not yet entered — add to `notes/match_notes.csv`]
- Match tags: [✓ present / ✗ not yet entered — add to `notes/match_tags.csv` using vocabulary from `docs/tag-dictionary.md`]
- Player notes: [✓ present / ✗ not recorded]
- Attendance: [✓ present / ✗ not recorded]
- Lineups: [✓ present / ✗ not recorded]

[If any flags are false: "To enrich future training reports, fill in the missing data files listed above after each match."]

*Generated by Claude Code — /training-report command*
```

## Step 6 — Cleanup and confirm

```bash
rm "D:/Coding/Projects/WRAAWTeam/reports/.training_data_tmp.json"
```

Tell the user: "Training report written to `OUTPUT_PATH`"
