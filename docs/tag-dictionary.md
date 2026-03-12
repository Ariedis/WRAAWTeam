# Tag Dictionary

This file defines the canonical tag vocabulary for `notes/match_tags.csv`.

Tags use `lower_snake_case`. When populating match tags, only use tags from this list to ensure clean analytics.

---

## Defensive — Conceded

| Tag | Description |
|-----|-------------|
| `conceded_set_piece` | Goal conceded from a corner, free kick, or throw-in routine |
| `conceded_through_ball` | Goal conceded after a ball played in behind the defensive line |
| `conceded_cross` | Goal conceded from a wide delivery or cutback |
| `conceded_error` | Goal conceded directly from a defensive mistake or poor pass |
| `conceded_second_ball` | Goal conceded after losing a 50/50 or second ball |
| `conceded_transition` | Goal conceded on the counter-attack or in transition |
| `high_line_exposed` | Defensive line caught too high, space exploited behind |
| `marking_breakdown` | Goal conceded because a player was left free at a set piece or in open play |

---

## Defensive — Patterns

| Tag | Description |
|-----|-------------|
| `press_bypassed` | Opposition played through or over our press successfully |
| `wide_overload_allowed` | Opposition had numerical advantage in wide areas |
| `build_out_issues` | Struggles to play out from the back under pressure |
| `goalkeeper_distribution_poor` | GK restarts led to immediate pressure or turnovers |
| `defensive_shape_held` | Team maintained defensive shape and structure well |
| `clean_sheet` | No goals conceded in the match |

---

## Attacking — Positives

| Tag | Description |
|-----|-------------|
| `created_chances_right` | Chances or attacks created consistently down the right flank |
| `created_chances_left` | Chances or attacks created consistently down the left flank |
| `created_chances_central` | Chances created through central combinations |
| `press_successful` | High press won the ball back and led to dangerous moments |
| `set_piece_goal` | Goal scored from a set piece (corner, free kick) |
| `goal_from_counter` | Goal scored on the counter-attack |
| `combination_play_effective` | Short passing combinations created clear opportunities |
| `individual_quality` | Individual skill or effort directly created a goal/chance |

---

## Attacking — Problems

| Tag | Description |
|-----|-------------|
| `lost_ball_central` | Possession lost repeatedly in central areas under pressure |
| `finishing_poor` | Clear chances not converted; finishing below expected level |
| `final_third_entry_blocked` | Struggled to enter the final third; opposition well-organized |
| `wide_play_ineffective` | Crosses or wide moves produced no meaningful chances |

---

## Tactical / Team Shape

| Tag | Description |
|-----|-------------|
| `compact_shape` | Team stayed compact and well-organized throughout |
| `transition_slow` | Team slow to transition between defensive and attacking phases |
| `width_used_well` | Team used full width of the pitch effectively in possession |
| `overloaded_midfield` | Midfield was outnumbered or out-worked by the opposition |
| `second_half_improved` | Performance noticeably better in the second half |
| `second_half_faded` | Team dropped off physically or tactically in the second half |

---

## Discipline / Physicality

| Tag | Description |
|-----|-------------|
| `yellow_card` | One or more yellow cards received |
| `red_card` | One or more red cards received |
| `physical_battle` | Match was high-intensity, contested physically throughout |

---

## Administration / Context

| Tag | Description |
|-----|-------------|
| `forfeit` | Match recorded as a forfeit (by either team) |
| `short_squad` | Team played with fewer than a full squad |
| `weather_affected` | Conditions (heat, rain, wind) significantly affected the match |

---

## Adding new tags

If you need a tag not listed here:
1. Follow the `lower_snake_case` convention.
2. Add it to this file with a description before using it in `match_tags.csv`.
3. The CI validation checks against this dictionary — new tags must be added here first.
