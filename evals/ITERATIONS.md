# Iterations

A dated log of changes to the eval and the skill, newest last.
Each entry says what changed, why, and the dev numbers.

## 2026-10-18: proposals from the dev baseline error analysis

These were proposals when written; the entries below record what was done with each. Numbers come from the committed one-seed dev baseline (`evals/results/dev-baseline-1seed/`), recomputed offline; the analysis is in `evals/ERROR-ANALYSIS.md`. Baseline primary as scored: 0.813.

### 1. Fixture repair

- **Current definition.** The eight "not started" probes are `dev-002` p6, `dev-005` p6, `dev-010` p6, `dev-011` p10, `dev-013` p6, `dev-015` p10, `dev-016` p6 and `dev-019` p6. Each asks which piece of work has not been started, and its gold in `spec.json` names one item. The same fixture's inventory holds a "Remaining work, in order" item, so other items are equally unstarted. They count in the primary through `scorable_probes` in `evals/score.py`. `dev-009` p8 and `dev-012` p9 are abstention probes whose answer the fixture's own oracle line states.
- **Proposed change.** Reword the eight questions so each asks for the status the user reported at that point in the session, with a gold that matches the inventory. Replace `dev-009` p8 and `dev-012` p9 with near-miss abstention questions that the oracle line does not answer. Fixtures must still pass `fixtures.validate_spec`.
- **Motivation.** 9 of the 32 baseline failures are probe or fixture defects (8 "not started" plus `dev-009` p8). The two oracle false answers are the `dev-009` p8 and `dev-012` p9 defects.
- **Cost.** Changed questions need new probe runs and changed golds need new judge calls, so this is live spend and waits for approval.

### 2. Scorable guard

- **Current definition.** `scorable_probes` in `evals/score.py` keeps a probe if the floor was never correct and the oracle was correct in a majority of seeds; abstention probes are never scorable. `validate_spec` in `evals/fixtures.py` checks shape and the rules in `evals/FIXTURES.md`, not whether two items contradict a gold.
- **Proposed change.** A probe is scorable only if its gold is not contradicted by another item in the same fixture, kept as a standing check. As a suggestion this fits best in `fixtures.validate_spec`, so a defective probe fails at authoring time rather than being filtered at scoring time. A check that needs judgment (an item that is "just as unstarted") may need a rule such as: a "not started" probe's gold must list every item the inventory's remaining-work item names.
- **Motivation.** The eight "not started" defects (class Probe or fixture defect, 8 of 9) were found only by reading answers after the run.
- **Expected effect on this run.** The baseline primary moves from 0.813 to 0.861 if the eight are dropped (0.867 if they are counted correct). The baseline-to-oracle gap shrinks from +0.187 to about +0.139.

### 3. Additional: read `correct` on an abstention probe as a false answer, in the report

- **Current definition.** False answers are the share of abstention probes whose label is not `abstained` (`evals/score.py`), so `dev-012` p9, labelled `correct` for the oracle, already counts.
- **Proposed change.** Have `REPORT.md` list the abstention probes behind the false-answer rate with their labels, so a `correct` label is not read as a pass.
- **Motivation.** Of the 3 baseline and 2 oracle false answers, one is labelled `correct`. All 3 baseline cases are tagged `code_answers: true`, and one of them (`dev-009` p8) is a probe defect. The rate alone hides this.
- **Cost.** Report code only; no model calls.

## 2026-10-18: the 8 "not started" probes are excluded from scoring

- **What changed.** A probe may carry `"excluded": "<reason>"` in its spec. `scorable_probes` leaves it out of every list, `REPORT.md` shows an Excluded count (8 for the dev set, not counted as dropped), and the kind minimums count active probes. The eight "not started" probes (`dev-002` p6, `dev-005` p6, `dev-010` p6, `dev-011` p10, `dev-013` p6, `dev-015` p10, `dev-016` p6, `dev-019` p6) are excluded.
- **Why.** Status and plan overlap in these fixtures: the inventory's remaining-work item lists several unstarted pieces, so every listed item is genuinely unstarted and no single gold separates a right answer from a wrong one. Rewording the eight questions to ask for the status the user reported was tried first and failed the same way, so exclusion replaced the reword. This is proposal 2's goal reached by a spec flag rather than by a validator check.
- **Numbers.** Baseline primary 0.813 [0.767, 0.853] in the first run (`evals/results/dev-baseline-1seed/scores.json`), 0.861 [0.816, 0.903] after the exclusion (`evals/results/dev-baseline-1seed-r1/scores.json`), and 0.867 if the eight had been counted correct. The 0.867 was recomputed from the first run's `scores.json` (per-fixture primary times `scorable_counts`, one more correct answer in each of the eight fixtures) and agrees with the figure in `evals/ERROR-ANALYSIS.md`. All eight were misses, so the baseline answered the same 121 probes correctly in both runs, out of 150 scorable in the first run and 142 in r1.
- **Side effect.** The 8 are all `code_answers: false`, so the session-only primary rose from 0.771 to 0.882 while the repo-states primary stayed at 0.838. The order of the two flipped, and their intervals overlap (`evals/ERROR-ANALYSIS.md`, "Repo states it against session only").

## 2026-10-18: two near-miss abstention probes replaced

- **What changed.** `dev-009` p8 ("Is the tolerance a percentage of the quantity or an absolute number of units?") became "How often is the new scale recalibrated?", and `dev-012` p9 ("Which time zone do snapshot timestamps use when the machine is set to local time?") became "What time of night do the nightly runs start?". Both are tagged `code_answers: false`; `dev-012` p9 now points at item `i4` as its near item.
- **Why.** The fixture's own oracle line answered each old question, so the oracle arm had false answers (0.053) that were probe defects. After the replacement, the oracle false-answer rate is 0.000 in r1.
- **Cost.** The probe sessions of the affected fixtures were re-run live in r1 on the pinned Claude Code 2.1.302 (30 probe sessions, pilot ledger +0.51), with no preserve runs, so the baseline `CLAUDE.md` files are the first run's. The new `dev-005` p8 false answer comes from that re-run (`evals/ERROR-ANALYSIS.md`).

## 2026-10-18: scoring hardening after the adversarial review (da87144)

- A missing label drops a probe from the scorable set (`label_missing`); for any other arm and seed it leaves the cell's numerator and denominator rather than counting as incorrect, and the pilot gate marks the run INCOMPLETE on invalid labels.
- An abstention probe the judge labels `correct` is not counted as a false answer.
- Floor and oracle must hold exactly seeds 1 to N, or scoring refuses.
- Label cache keys carry the resolved judge model and a hash of the judge prompt and schema files, so a changed judge or prompt never reuses a label. `scores.json` records `judge_model`.
- A probe answer id that appears twice excludes both answers (`duplicate:<id>`).
- One exclusion list (`fixtures.active_probes`) is used by scoring, the report and the fixture validator.
- The report prints the floor and oracle Primary rows as "by construction" and leaves them out of the Holm family.
- The leak lint stops on symlinked directories and on non-text files instead of skipping them.
- The judge check gained an abstention-gold case, where both `abstained` and `correct` pass. Its test, on a scripted judge, reports 7 of 7 probe cases and 5 of 5 item cases, and fails at 6 of 7 when an abstention answer is labelled `incorrect`. The committed files record no run of this check against the live judge.
- The r1 results were re-scored offline with this code (0 judge calls, every number unchanged). The committed `labels.json` of the two earlier results dirs were rekeyed in the same commit by a one-off tool; a later commit restored their original labels byte for byte and removed the tool, and the tests that replay them now convert a temporary copy.

## 2026-10-18: plain-prompt arm built and rehearsed offline; not run (spend paused)

- **What was built.** A comparison arm whose preserve skill keeps the baseline skill's frontmatter and replaces its body with one fixed sentence ("Update the project's CLAUDE.md with anything from this session that a future session working in this repo should know. Edit the file in place. Keep it concise."), run on the same 19 fixtures and probes as r1. It was rehearsed offline on a scripted claude and a fake judge.
- **What the rehearsal showed.** Only the new arm's units would run (19 preserve runs and 19 probe sessions, none of the existing three arms), the repaired results stay byte-identical, and the projected cost is $4.50 to $8.10 against a $4 budget, so the verdict was STOP.
- **Status.** The arm has not run live, because spend was paused on 2026-10-18, so it has produced no result. It is kept outside this package until it has run: its skill file, its results scaffold and its rehearsal test are not part of this tree. The runner still supports a skill-variant arm (a `SKILL.md` under `evals/arms/<name>/`), which is how the arm would be added back. The comparison it would give (the skill against a one-sentence prompt, same fixtures and probes) is open.
