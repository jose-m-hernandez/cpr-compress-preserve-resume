# Evaluation report: dev-baseline-1seed

Split dev, run date 20261018. 19 fixtures, 1 seeds, arms floor, baseline, oracle.
Pins: Claude Code 2.1.302, model claude-sonnet-5-5, plugin ref cfd1e77e07d2, judge claude-opus-5-5.
Unit of analysis: the fixture (seed means). Intervals are 95% percentile bootstrap intervals (10000 resamples, seed 20261017).

## Judge sanity controls

Oracle recall 1.000 (minimum 0.95). Mismatch recall 0.000 (maximum 0.05). PASS.

## Per-arm metrics

Each cell is the mean over fixtures with its interval. Primary is probe accuracy on scorable probes; Primary (all) is accuracy on every non-abstention probe, that is, the primary recomputed with the dropped probes included (for the oracle arm it is the probe-validity diagnostic). False answers are abstention probes answered with something other than UNKNOWN. Delta lines is the change in `wc -l` against the floor; Delta tokens is the arm's probe-session input tokens (input, cache creation and cache read) minus the floor's for the same fixture and seed. The last column is the pooled within-fixture SD of the primary across seeds.

| Arm | Primary | Primary (all) | Recall | Precision | Placement | False answers | Delta lines | Delta tokens | Within-fixture SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| floor | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | n/a | n/a | 0.000 [0.000, 0.000] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | n/a |
| baseline | 0.813 [0.767, 0.853] | 0.808 [0.762, 0.850] | 0.884 [0.844, 0.925] | 0.578 [0.533, 0.624] | 0.793 [0.730, 0.857] | 0.079 [0.000, 0.158] | 25.8 [23.9, 27.8] | 589.8 [515.8, 687.4] | n/a |
| oracle | 1.000 [1.000, 1.000] | 0.995 [0.984, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.053 [0.000, 0.132] | 19.8 [19.1, 20.7] | 274.6 [253.3, 299.0] | n/a |

Fixtures with no scorable probe: 0.

## Scorable probes

A probe is scorable when the floor answered it correctly in none of its seeds and the oracle answered it correctly in a majority of its seeds. A dropped probe can fail both tests.

| Fixture | Scorable | Dropped | Floor answered correctly | Oracle in minority |
| --- | --- | --- | --- | --- |
| dev-001-csv-tally | 7 | 0 | 0 | 0 |
| dev-002-notes-api | 7 | 0 | 0 | 0 |
| dev-003-sales-etl | 7 | 0 | 0 | 0 |
| dev-004-md-linter | 9 | 1 | 0 | 1 |
| dev-005-flag-service | 7 | 0 | 0 | 0 |
| dev-006-ledger-cli | 12 | 0 | 0 | 0 |
| dev-007-link-shortener | 7 | 0 | 0 | 0 |
| dev-008-photo-renamer | 7 | 0 | 0 | 0 |
| dev-009-inventory-diff | 7 | 0 | 0 | 0 |
| dev-010-cron-expr | 7 | 0 | 0 | 0 |
| dev-011-webhook-router | 11 | 0 | 0 | 0 |
| dev-012-backup-snapshots | 8 | 0 | 0 | 0 |
| dev-013-unit-convert | 7 | 0 | 0 | 0 |
| dev-015-adventure-engine | 11 | 0 | 0 | 0 |
| dev-016-mail-templates | 7 | 0 | 0 | 0 |
| dev-017-metrics-exporter | 8 | 0 | 0 | 0 |
| dev-018-shift-planner | 7 | 0 | 0 | 0 |
| dev-019-plugin-registry | 7 | 0 | 0 | 0 |
| dev-020-ci-summary | 7 | 0 | 0 | 0 |

Dropped 1 of 151 non-abstention probes (floor answered correctly: 0; oracle in minority: 1).

## Primary by whether the repo states the answer

Probe sessions see only CLAUDE.md. Each probe is tagged by whether a file in the fixture's repo, other than CLAUDE.md, states its answer (code_answers in the spec). Each cell is the primary over that group's scorable probes, as a mean over fixtures with its interval; a fixture with no scorable probe in a group is left out of that column.

| Arm | Primary, repo states it | Primary, session only |
| --- | --- | --- |
| floor | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| baseline | 0.838 [0.772, 0.899] | 0.771 [0.663, 0.870] |
| oracle | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |

Scorable probes: repo states it 83, session only 67. Fixtures with at least one: 19 and 19.

## Paired differences against the baseline

Difference is the arm minus the baseline, per fixture. Wilcoxon is the two-sided signed-rank test (exact when n is at most 25 with no tied values); Holm adjusts across all rows of this table.

| Arm | Metric | n | Mean diff | 95% CI | Wilcoxon p | Holm p | SD of diffs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| floor | Primary | 19 | -0.813 | [-0.853, -0.767] | 0.0001 | 0.0007 | 0.097 |
| floor | Recall | 18 | -0.884 | [-0.925, -0.844] | 0.0002 | 0.0009 | 0.089 |
| floor | Precision | 0 | n/a | n/a | n/a | n/a | n/a |
| floor | Placement | 0 | n/a | n/a | n/a | n/a | n/a |
| oracle | Primary | 19 | 0.187 | [0.147, 0.233] | 0.0002 | 0.0009 | 0.097 |
| oracle | Recall | 18 | 0.116 | [0.075, 0.156] | 0.0014 | 0.0014 | 0.089 |
| oracle | Precision | 18 | 0.422 | [0.376, 0.467] | 0.0002 | 0.0009 | 0.100 |
| oracle | Placement | 18 | 0.207 | [0.143, 0.270] | 0.0007 | 0.0014 | 0.143 |

## A/A split

Per fixture, the mean of seeds 1 and 2 minus the mean of seeds 3 and 4 (seed 5 is left out). The arm is compared with itself, so this is the noise floor of the other tables.

| Arm | Metric | n | Mean diff | 95% CI | SD |
| --- | --- | --- | --- | --- | --- |
| floor | Primary | 0 | n/a | n/a | n/a |
| floor | Recall | 0 | n/a | n/a | n/a |
| baseline | Primary | 0 | n/a | n/a | n/a |
| baseline | Recall | 0 | n/a | n/a | n/a |
| oracle | Primary | 0 | n/a | n/a | n/a |
| oracle | Recall | 0 | n/a | n/a | n/a |

## Probe-context tokens

The arm's mean Delta tokens (the share of the probe context its CLAUDE.md adds over the floor), and that as a ratio to the baseline's.

| Arm | Delta tokens | Ratio to baseline |
| --- | --- | --- |
| floor | 0.0 | 0.000 |
| baseline | 589.8 | 1.000 |
| oracle | 274.6 | 0.466 |

## Cost

Dollar figures are the API-price equivalent of each call's reported cost; under a subscription they are not billed. Input tokens count input, cache creation and cache read.

| Call type | Arm | Calls | $ | Input tokens | Output tokens | Wall-clock s |
| --- | --- | --- | --- | --- | --- | --- |
| preserve | baseline | 19 | 2.7682 | 2346857 | 36214 | 319.9 |
| probe | floor | 19 | 0.2880 | 73336 | 4280 | 64.1 |
| probe | baseline | 19 | 0.3568 | 84543 | 6678 | 78.0 |
| probe | oracle | 19 | 0.3245 | 78554 | 5842 | 73.4 |
| judge | judge | 97 | 3.7193 | 404596 | 48718 | 650.8 |
| total |  | 173 | 7.4568 | 2987886 | 101732 | 1186.2 |

baseline preserve runs that changed CLAUDE.md: 19 of 19.

## Missing and invalid

Probe answers missing or unparsable: 13 (counted as incorrect in accuracy, left out of the false-answer rate).
Judge labels invalid: 1. Judge calls this pass: 98; cache hits: 31.

## Failure gallery

### Baseline probe failures (first failing seed per scorable probe)

| Fixture | Probe | Seed | Label | Question | Expected | Answer |
| --- | --- | --- | --- | --- | --- | --- |
| dev-002-notes-api | p3 | 1 | abstained | How long may a note title be? | At most 80 characters. | UNKNOWN |
| dev-002-notes-api | p6 | 1 | incorrect | Which features have not been started? | Pagination and rate limiting. | Rate limiting, pagination, and docs (all three next steps are unchecked). |
| dev-003-sales-etl | p6 | 1 | abstained | Which part of the code is written but has little test coverage? | etl/report.py | UNKNOWN |
| dev-003-sales-etl | p7 | 1 | abstained | In what order is the remaining work to be done? | The monthly rollup first, then the comparison against the finance export. | UNKNOWN |
| dev-004-md-linter | p5 | 1 | abstained | Which keys does each JSON output object have, and which module formats it? | path, line, rule and severity; mdcheck/formats.py. | UNKNOWN |
| dev-004-md-linter | p6 | 1 | incorrect | Where and in what order are new rules registered? | In the RULES list at the bottom of rules.py, alphabetical by rule name. | In the RULES registry in mdcheck/rules.py, in the order the rules were added (not alphabetical). |
| dev-005-flag-service | p6 | 1 | incorrect | Which feature has not been started yet? | Percentage rollouts. | Audit log, percentage rollouts, and admin UI have not been started. |
| dev-006-ledger-cli | p9 | 1 | abstained | Why can the budget limits not be built yet? | They wait for the accountant's category list; categories stay free text until then. | UNKNOWN |
| dev-006-ledger-cli | p12 | 1 | incorrect | In what order is the remaining work planned? | CSV export, then the budget limits, then a README. | Budget limits, then CSV export, then the README (also fixing the CLAUDE.md layout). |
| dev-007-link-shortener | p5 | 1 | abstained | Which URL schemes can be shortened? | Only http and https. | UNKNOWN |

### Needed items the baseline never matched

| Fixture | Item | Statement |
| --- | --- | --- |
| dev-002-notes-api | j3 | Note titles are limited to 80 characters; the store raises ValueError('title too long (max 80)') beyond that. |
| dev-004-md-linter | o1 | The maximum line length is 88 characters (it was first set to 100). |
| dev-004-md-linter | o6 | New rules are registered in the RULES list at the bottom of rules.py, in alphabetical order by rule name. |
| dev-006-ledger-cli | i9 | Budget limits per category are blocked until the accountant sends the category list; categories stay free text until then. |
| dev-007-link-shortener | i5 | Only http and https URLs can be shortened; other schemes such as ftp are rejected. |
| dev-008-photo-renamer | i2 | New names use a lowercase hyphenated slug, such as 2026-04-02_harbour-walk.jpg. |
| dev-008-photo-renamer | i5 | Two photos with the same date and title collide, and the planner refuses rather than adding a counter suffix. |
| dev-009-inventory-diff | i5 | SKUs must be upper-case letters, a dash and digits; a lower-case SKU such as a-100 is rejected. |
| dev-010-cron-expr | i5 | Weekday 7 is rejected: Sunday is 0. |
| dev-012-backup-snapshots | i5 | A destination inside the source tree is refused, because the snapshot would copy itself. |
