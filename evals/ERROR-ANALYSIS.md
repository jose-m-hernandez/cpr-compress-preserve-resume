# Error analysis of the dev baseline (one seed)

This file has two parts. The first reads the repaired run (r1), the headline run. The second, below it, is the analysis of the first run, kept as written.

# Repaired run (r1), 2026-10-18

This reads the committed results in `evals/results/dev-baseline-1seed-r1/` (`scores.json`, `REPORT.md`, `labels.json`, `arms/`, `probes/`): the same 19 dev fixtures, one seed, the `baseline` arm against `oracle` and `floor`. Nothing here calls a model; every figure is read from those files, or recomputed from `labels.json` and the probe answers by an offline script.

## What changed since the first run

- Eight "not started" probes (`dev-002` p6, `dev-005` p6, `dev-010` p6, `dev-011` p10, `dev-013` p6, `dev-015` p10, `dev-016` p6, `dev-019` p6) are excluded from scoring in their specs. `REPORT.md` lists them under "Excluded" (8) and does not count them as dropped.
- Two abstention probes the oracle line answered (`dev-009` p8, `dev-012` p9) were replaced with near-miss questions. Probe sessions were re-run for the fixtures whose probes changed.
- The baseline `CLAUDE.md` files were not regenerated. All 19 `arms/baseline/*/s1.md` files in r1 are byte-identical to the first run's (checked with `cmp`), so every difference below comes from the probe set, the probe sessions and the scoring code.

## Headline figures

From `scores.json` and `REPORT.md` in r1:

| Figure | Baseline | Oracle | Floor |
|---|---|---|---|
| Primary (mean over 19 fixtures) | 0.861 [0.816, 0.903] | 1.000 | 0.000 |
| Primary (all non-abstention probes) | 0.857 [0.810, 0.901] | 0.995 | 0.000 |
| Recall | 0.885 [0.847, 0.922] | 1.000 | 0.000 |
| Precision | 0.574 [0.534, 0.619] | 1.000 | n/a |
| Placement | 0.793 [0.730, 0.852] | 1.000 | n/a |
| False answers | 0.079 [0.000, 0.158] | 0.000 | 0.000 |
| Delta lines | 25.8 [23.9, 27.8] | 19.8 [19.1, 20.7] | 0.0 |
| Delta tokens | 590.9 [516.8, 688.4] | 275.9 [254.5, 300.2] | 0.0 |

The primary is a mean of 19 per-fixture shares. Pooled over the probes, the baseline answered 121 of the 142 scorable probes correctly (0.852). The 142 is the 143 non-abstention probes less the one dropped probe (`dev-004` p9, `oracle_minority`), after the 8 exclusions; `REPORT.md` shows 83 repo-states probes and 59 session-only probes (83 + 59 = 142). The first run had 150 scorable probes and the same 121 correct, so every probe removed was a miss. The baseline-to-oracle gap is 0.139 (`REPORT.md`, paired differences).

The sensitivity check in the first-run section holds: the first run's 0.813 becomes 0.861 with the 8 removed (this r1 figure) and 0.867 if the 8 had been counted correct. That 0.867 was recomputed from the first run's `scores.json` (per-fixture primary times `scorable_counts`, one extra correct answer in each of the 8 fixtures).

Precision is 0.574 against 0.578 in the first run, and Delta tokens 590.9 against 589.8. The first run's reasons for low precision (table scaffolding, the release-branch codename line, repeats, true session facts the inventory does not list) apply unchanged, because the `CLAUDE.md` files are the same. One difference in scope: the first run averaged the line metrics over 18 fixtures, while the r1 `REPORT.md` paired table shows n = 19 for them. The token difference comes from the re-run probe sessions. This analysis did not trace the exact cause of the 0.004 precision shift.

## The 21 scorable misses

The baseline missed 21 scorable probes: 15 labelled `abstained` and 6 `incorrect` (121 + 21 = 142). In addition there are 3 false answers on abstention probes. The 21 are exactly the first run's 32 failures less the 8 excluded probes, less `dev-009` p8 (replaced), less the two abstention false answers that stay in the false-answer column (`dev-004` p12, `dev-011` p13): 32 - 8 - 1 - 2 = 21. The classes in the first-run section therefore keep their sizes except the two removed ones, giving 7 / 7 / 4 / 3 over the same 21 probes:

| Class | Count | Probes |
|---|---|---|
| Partial: a related fragment kept, the asked part lost | 7 | `dev-002` p3, `dev-004` p5, `dev-006` p9, `dev-008` p5, `dev-015` p5, `dev-016` p5, `dev-020` p5 |
| Dropped: no line on the fact | 7 | `dev-007` p5, `dev-009` p5, `dev-012` p5, `dev-015` p1, `dev-017` p5, `dev-018` p5, `dev-019` p5 |
| Remaining-work order replaced or diluted | 4 | `dev-003` p7, `dev-006` p12, `dev-011` p11, `dev-015` p11 |
| Wrong or stale statement kept | 3 | `dev-003` p6, `dev-004` p6, `dev-015` p6 |

Those probe ids are the ones the first-run table assigns to each class; the table above is that table with the excluded and replaced rows removed. The labels in `labels.json` match: 15 `abstained` and 6 `incorrect`. Two rows of the "wrong or stale" class (`dev-003` p6, `dev-015` p6) are labelled `abstained` in r1, not `incorrect`: the class describes what the first-run reading found in the `CLAUDE.md`, and the label describes the answer.

## The three false answers

False answers are abstention probes whose label is not `abstained`. In r1 they are `dev-004` p12, `dev-005` p8 and `dev-011` p13, giving 0.079 as the mean of three fixture rates of 0.5 over 19 fixtures. The oracle has none (its two first-run cases were the replaced probes). Quotes are from the r1 probe answers in `probes/baseline/<fixture>/s1.json` and the baseline `CLAUDE.md` in `arms/baseline/<fixture>/s1.md`.

- **`dev-004` p12.** Question: "Which exit code is returned when the config file is malformed JSON?" Answer: "Exit code 4 (config or unknown-rule error), though the instructions don't explicitly mention malformed JSON." Traces to line 38 of the `CLAUDE.md`: "Exit code 0 means clean (or warnings only), 1 means error findings, 4 means a config or unknown-rule error." The answer is a hedged inference from that line, and the repo's code supports it (`EXIT_CONFIG = 4`).
- **`dev-005` p8 (not analysed before).** Question: "How long does the cache keep the result for an unknown flag?" Gold: UNKNOWN (the probe has `near: m1`, the 30-second TTL, and `code_answers: false`). Answer: "It doesn't; unknown results are not cached." Traces to line 32 of the `CLAUDE.md`, a Decisions row: "`evaluate()` returns `False` for an unknown flag and never raises | Requested behavior; unknown results are not cached." The clause "unknown results are not cached" is the run's own addition: the fixture's item `m3` says only that `evaluate()` returns `False` for an unknown flag and never raises, and no item mentions caching of unknown flags. The clause is true of the repo, since `FlagStore.evaluate` in `flags/store.py` returns `False` before it reaches `cache.put`. So the baseline stated a true, code-derived fact that the session did not settle, and the probe session used it. This is the same pattern as `dev-004` p12 and `dev-011` p13. The first run's answer to this probe was "UNKNOWN" from the identical `CLAUDE.md`, so the false answer is probe-session variation, not a change in the skill's output. One reading problem for the next review: the question presumes unknown flags are cached, and the code answers it, yet the spec tags `code_answers: false`. The tag was wrong; it has been corrected to `code_answers: true`. The probe is a weaker near-miss than intended, and nothing else was changed.
- **`dev-011` p13.** Question: "Does the Retry-After header also appear on 4xx responses?" Answer: "No; `response_headers` gives `Retry-After: 30` only to 5xx responses." Traces to line 14 ("`response_headers(status)`, which gives 5xx responses `Retry-After: 30`") and line 42 ("`Retry-After: 30` (plain seconds) on every 5xx"). The repo's `router/dispatch.py` supports the answer; the session never said whether 4xx responses carry it.

All three answers are supported by the repo and traced to lines the run added or inferred from, so they count against the baseline only because probe sessions see `CLAUDE.md` alone and are meant to abstain on what the session did not settle.

## Repo states it against session only

Primary by `code_answers` tag, from the r1 `REPORT.md` ("Primary by whether the repo states the answer"):

| Run | Repo states it | Session only |
|---|---|---|
| First run (`evals/results/dev-baseline-1seed/REPORT.md`) | 0.838 [0.772, 0.899] | 0.771 [0.663, 0.870] |
| r1 | 0.838 [0.772, 0.899] | 0.882 [0.777, 0.968] |

The order flipped, and the reason is mechanical. The 8 excluded probes are all `code_answers: false` (session-only) and all were misses, so removing them lifted only the session-only column, from 0.771 to 0.882, and left the repo-states column unchanged. The intervals overlap in both runs, and in r1 the two columns differ by 0.044 with intervals of about 0.13 and 0.19 in width. With one seed, r1 does not show that either kind of fact is easier for the skill to keep; the first run's reading (part of the gap is the skill leaving out what the code already says) is not supported or refuted by r1.

## Follow-ups from r1

- The `dev-005` p8 tag (`code_answers`) and the strength of its near-miss need a decision before another run.
- A plain-prompt comparison arm has been built but has not run, and it is not part of this package; see `evals/ITERATIONS.md`.

# First run (0.813), 2026-10-18

The rest of this file is the analysis of the first run, kept as written. Its figures (0.813, 32 failures, the eight "not started" defects, the two oracle false answers) describe `evals/results/dev-baseline-1seed/`, not r1.

This reads the committed results in `evals/results/dev-baseline-1seed/`: 19 dev fixtures, one seed, the `baseline` arm (the `CLAUDE.md` written by the real `/cpr:preserve`) against the `oracle` arm.

The headline is a primary score of 0.813 [0.767, 0.853] for the baseline, 1.000 for the oracle and 0.000 for the floor.

The baseline fails 32 probes. Nine of them are defects in the probe or fixture, not in the skill's output. Eight of the nine are "not started" questions whose gold leaves out items that are equally unstarted.

Without those eight, the primary would be 0.861 with them excluded, or 0.867 with them counted correct, against 0.813 as scored, and the baseline-to-oracle gap about 0.05 smaller than the +0.187 the headline shows.

## Scope and method

A failure is a baseline probe that is either scorable and not labelled `correct`, or an abstention probe whose label is neither `abstained` nor empty. That gives 29 scorable failures (15 `abstained`, 14 `incorrect`) plus 3 false answers on abstention probes (`dev-004` p12, `dev-009` p8, `dev-011` p13). Scorable means the floor was never correct and the oracle was correct in a majority of seeds (`scorable_probes` in `evals/score.py`).

Nothing here calls a model. Every label comes from the committed `labels.json` and `scores.json`, read through small offline scripts. `REPORT.md` regenerates byte-identically from `scores.json`, and the scripts reproduce the committed primary for all 567 label rows.

The line metrics (recall, precision, placement) average over 18 fixtures, not 19: the baseline line labels for `dev-011` are invalid and are left out of those three. The primary and false-answer figures use all 19.

Classes were assigned by reading each failing probe's question, gold, answer, the lines the baseline added, and the fixture's items. Quotes below come from `spec.json` fields, fixture `repo/` files and the committed `arms/` and `probes/` files.

## Failure classes

The classes below are exhaustive and sum to 32. No failure was a judge mislabel and none was a probe-session error.

| Class | Count | Metric that catches it | Example |
|---|---|---|---|
| Probe or fixture defect | 9 | Primary (scorable set); false answers for `dev-009` p8 | `dev-005` p6 gold "Percentage rollouts."; answer "Audit log, percentage rollouts, and admin UI have not been started." |
| Remaining-work order replaced or diluted | 4 | Primary; recall still counts the line as matched | `dev-006` p12 gold "CSV export, then the budget limits, then a README."; answer "Budget limits, then CSV export, then the README" |
| Wrong or stale statement kept | 3 | Primary; recall still counts the line as matched | `dev-004` p6 gold "alphabetical by rule name"; answer "in the order the rules were added (not alphabetical)" |
| Partial: a related fragment kept, the asked part lost | 7 | Primary; recall counts the item as matched | `dev-016` p5 gold "Only name, plan and link."; answer "only name `plan` as an allowed placeholder", full list not given |
| Dropped: no line on the fact | 7 | Recall and primary | `dev-017` p5 "What must a counter name end in?" gold "_total"; answer "UNKNOWN" |
| Abstention answered from lines the run added | 2 | False answers | `dev-011` p13 "Does the Retry-After header also appear on 4xx responses?" answer "No, `Retry-After: 30` is given only to 5xx responses." |
| Judge mislabel / probe-session error | 0 | n/a | none found |

Class sizes: 9 + 4 + 3 + 7 + 7 + 2 + 0 = 32.

All 32 failures:

| Fixture | Probe | Type | Code answers | Class |
|---|---|---|---|---|
| `dev-002` | `p3` | single-fact | true | Partial |
| `dev-002` | `p6` | single-fact | false | Probe or fixture defect |
| `dev-003` | `p6` | single-fact | false | Wrong or stale kept |
| `dev-003` | `p7` | temporal | false | Order replaced or diluted |
| `dev-004` | `p5` | single-fact | true | Partial |
| `dev-004` | `p6` | single-fact | false | Wrong or stale kept |
| `dev-004` | `p12` | abstention | true | Abstention answered |
| `dev-005` | `p6` | single-fact | false | Probe or fixture defect |
| `dev-006` | `p9` | single-fact | false | Partial |
| `dev-006` | `p12` | temporal | false | Order replaced or diluted |
| `dev-007` | `p5` | single-fact | true | Dropped |
| `dev-008` | `p5` | single-fact | true | Partial |
| `dev-009` | `p5` | single-fact | true | Dropped |
| `dev-009` | `p8` | abstention | true | Probe or fixture defect |
| `dev-010` | `p6` | single-fact | false | Probe or fixture defect |
| `dev-011` | `p10` | single-fact | false | Probe or fixture defect |
| `dev-011` | `p11` | temporal | false | Order replaced or diluted |
| `dev-011` | `p13` | abstention | true | Abstention answered |
| `dev-012` | `p5` | single-fact | true | Dropped |
| `dev-013` | `p6` | single-fact | false | Probe or fixture defect |
| `dev-015` | `p1` | single-fact | true | Dropped |
| `dev-015` | `p5` | single-fact | false | Partial |
| `dev-015` | `p6` | single-fact | false | Wrong or stale kept |
| `dev-015` | `p10` | single-fact | false | Probe or fixture defect |
| `dev-015` | `p11` | temporal | false | Order replaced or diluted |
| `dev-016` | `p5` | single-fact | true | Partial |
| `dev-016` | `p6` | single-fact | false | Probe or fixture defect |
| `dev-017` | `p5` | single-fact | true | Dropped |
| `dev-018` | `p5` | single-fact | true | Dropped |
| `dev-019` | `p5` | single-fact | true | Dropped |
| `dev-019` | `p6` | single-fact | false | Probe or fixture defect |
| `dev-020` | `p5` | single-fact | true | Partial |

Two patterns stand out. Every dropped probe has `code_answers: true`: the skill left out facts the repo already states, which is a defensible choice that the eval scores as a loss. And all four order failures are `temporal` probes whose plan the baseline reordered or padded.

### The eight "not started" defects

`dev-002` p6, `dev-005` p6, `dev-010` p6, `dev-011` p10, `dev-013` p6, `dev-015` p10, `dev-016` p6 and `dev-019` p6 ask which piece of work has not been started, and each gold names one item. Each fixture's own inventory also holds an item "Remaining work, in order: X, then Y, then Z", so other items are just as unstarted. Every baseline answer names the gold item plus the others, and the judge followed the gold and labelled them `incorrect`.

For `dev-005` the gold is "Percentage rollouts." while the inventory's remaining work is the audit log, then percentage rollouts, then the admin UI. The skill recorded that status correctly; the question cannot tell a right answer from a wrong one.

## Sensitivity of the headline

Each figure is the mean, over the 19 fixtures, of that fixture's share of scorable probes labelled `correct`, recomputed offline from the committed labels.

| Variant | Baseline primary |
|---|---|
| As scored | 0.813 |
| The eight "not started" answers counted `correct` | 0.867 |
| The eight removed from their fixtures' scorable sets | 0.861 |

The baseline-to-oracle gap is +0.187 as scored. With the eight defects removed it is 0.139, so the headline overstates the gap by about 0.05. The oracle is 1.000 by construction: a probe is scorable only if the oracle answers it correctly.

## Why precision is low

Baseline precision is 0.578. Of the lines the baseline added over the floor on the 18 fixtures (first run), 170 are labelled `needed`, 119 `unplanted` and 11 `not_needed`. The 130 lines that are not `needed` split as follows (first run, 18 fixtures) (the sub-kinds are this analysis's own reading, one per line):

| Sub-kind | Lines |
|---|---|
| Code or layout description (a repo file or its behaviour) | 29 |
| Markdown table header or separator row (`\| Decision \| Reason \|`, `\| --- \| --- \|`) | 28 |
| True fact the session produced, not inventoried: decision or caveat | 22 |
| True fact the session produced, not inventoried: status or open work | 23 |
| Release-branch codename line | 16 |
| Item the inventory marks not needed | 11 |
| Generic tooling advice | 1 |
| Total | 130 |

The release-branch codename is planted in each session so the harness can check that the preserve run saw the history. The baseline copied it into `CLAUDE.md` in 18 of the 19 fixtures, and 16 such lines fall among the 130 above, so that check adds lines that are not `needed` by design.

Two readings follow. Twenty-eight lines are table scaffolding, so they lower precision by construction whenever a decisions table is written, however good its rows. And 45 more lines are true facts from the session that the inventory simply does not list, so some of the 0.578 is the inventory's coverage, not the skill's noise.

The `needed` numerator also counts repeats: 170 `needed` lines match 123 distinct items, so 47 lines restate an item another line already matched. Precision rewards that repetition; recall does not.

## Oracle false answers

Two oracle probes on abstention questions are not `abstained`: `dev-009` p8 (labelled `incorrect`) and `dev-012` p9 (labelled `correct`).

In both, the oracle's own line for the probe's `near` item states the answer. The `dev-009` oracle `CLAUDE.md` has "Differences of 1 unit or less are ignored (was 2): the new scale reads to the unit.", and the oracle answered that the tolerance is "an absolute number of units". The `dev-012` oracle `CLAUDE.md` has "Snapshot folders are named by UTC timestamp", and the oracle answered with that.

The rule: an abstention probe whose answer is stated by the fixture's own oracle line is a probe defect, because the oracle arm is supposed to hold the facts and should not have to abstain. Neither changes a baseline number. The `dev-012` label `correct` counts as a false answer just as `incorrect` would, since the metric counts every label other than `abstained`.

## The dropped probe (`dev-004` p9)

`dev-004` p9 is the one probe dropped as `oracle_minority`: the oracle answered "UNKNOWN". The probe is `code_answers: false`.

The gold is "line-length, trailing-space, heading-increment and no-bare-urls." for the question "Which rules are done and documented?". Item `o9` states those four rules as "done and documented". Its `oracle_line` is "- Done: line-length, trailing-space, heading-increment, no-bare-urls, `--config`, `--format json`." and the oracle `CLAUDE.md` carries it under `## Status`. The word "documented" is not in that line.

The oracle `CLAUDE.md` does say, elsewhere, that `docs/rules.md` "documents each rule", but nothing ties documentation to those four. The probe asks for two properties and the oracle line gives one. This analysis reads the oracle line as the weaker side: it under-states its item. The probe session's reasoning is not recorded, so this is the likeliest explanation, not a proven one.

## Abstention probes the code answers

A probe session sees only `CLAUDE.md`. An abstention probe whose answer only the repo's code states stays valid: the session never settled the question, and a later session working from `CLAUDE.md` alone should say so.

- `dev-004` p12 (exit code for a malformed config): `mdcheck/runner.py` raises `ConfigError` on invalid JSON and `mdcheck/errors.py` sets `EXIT_CONFIG = 4`. Floor "UNKNOWN", baseline "Exit code 4 (config or unknown-rule error), though the instructions don't explicitly mention malformed JSON.", oracle "UNKNOWN". Valid; the baseline answer is a guess from added lines, hedged.
- `dev-011` p13 (`Retry-After` on 4xx): `router/dispatch.py` adds the header only for 5xx. Floor has no answer, baseline "No, `Retry-After: 30` is given only to 5xx responses.", oracle "UNKNOWN". Valid; the baseline stated more than the session did.
- `dev-018` p9 (CSV column separator): `rota/export.py` writes the CSV with Python's `csv` module. Floor, baseline and oracle all answered "UNKNOWN". Valid and passed by every arm.

By contrast `dev-009` p8 and `dev-012` p9 are defects, because the fixture's own oracle line answers them (previous section).

## How-but-not-why probes

Rule: a probe whose code shows how something works but not why stays tagged `code_answers: false`. The tag asks whether a file holds a line a reader would quote as the answer; a mechanism is not a reason.

Of the 32 failures, one fits: `dev-006` p9, "Why can the budget limits not be built yet?". The repo stores categories as free text, but nothing in it says limits wait for an accountant's list. The tag is right as it stands. The baseline kept the warning not to validate categories against a fixed list but lost the link to the limits, which is why it is classed Partial.

## What contradicts the headline

- The sensitivity figures above: 0.867 and 0.861 against 0.813, and a gap to the oracle about 0.05 smaller.
- Two of the three baseline false answers (`dev-004` p12, `dev-011` p13; first run, in the repaired run all three are, see above) are answers the repo's code supports. They count against the baseline because probe sessions see only `CLAUDE.md`, not because the answers are wrong about the repo.
- The baseline false-answer rate (0.079) sits close to the oracle's (0.053), and the oracle's two cases are probe defects. The comparison rests on a handful of probes.
- "Repo states it" scores 0.838 against 0.771 for facts only the session holds. Part of the gap is the skill leaving out what code already says (all seven dropped probes are `code_answers: true`).
- Precision of 0.578 mixes inventory coverage, table scaffolding and repeats, as described above.

No other contradiction was found.

## Follow-ups

- Repair the eight "not started" probes and the two abstention probes the oracle line answers. This needs new probe runs and new judge calls. Proposal 1 in `evals/ITERATIONS.md`.
- Add a standing scorable guard: a gold must not be contradicted by another item in the same fixture. Proposal 2 in `evals/ITERATIONS.md`.
- `test_private_terms_must_be_configured` depends on the installed Claude Code version matching the pin in `evals/config.json`, so it fails whenever the host version drifts. Make it independent of the host.
