# Evaluation report: pilot-20261017

Split dev, run date 20261017. 5 fixtures, 3 seeds, arms floor, baseline, oracle.
Pins: Claude Code 2.1.302, model claude-sonnet-5-5, plugin ref cfd1e77e07d2, judge claude-opus-5-5.
Unit of analysis: the fixture (seed means). Intervals are 95% percentile bootstrap intervals (10000 resamples, seed 20261017).

## Judge sanity controls

Oracle recall 1.000 (minimum 0.95). Mismatch recall 0.000 (maximum 0.05). PASS.

## Per-arm metrics

Each cell is the mean over fixtures with its interval. Primary is probe accuracy on scorable probes; Primary (all) is accuracy on every non-abstention probe, that is, the primary recomputed with the dropped probes included (for the oracle arm it is the probe-validity diagnostic). False answers are abstention probes answered with something other than UNKNOWN. Delta lines is the change in `wc -l` against the floor; Delta tokens is the arm's probe-session input tokens (input, cache creation and cache read) minus the floor's for the same fixture and seed. The last column is the pooled within-fixture SD of the primary across seeds.

| Arm | Primary | Primary (all) | Recall | Precision | Placement | False answers | Delta lines | Delta tokens | Within-fixture SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| floor | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | n/a | n/a | 0.000 [0.000, 0.000] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.000 |
| baseline | 0.786 [0.715, 0.862] | 0.771 [0.686, 0.857] | 0.931 [0.851, 1.000] | 0.647 [0.569, 0.755] | 0.734 [0.695, 0.765] | 0.167 [0.000, 0.367] | 25.3 [20.7, 28.8] | 516.5 [419.3, 609.7] | 0.070 |
| oracle | 1.000 [1.000, 1.000] | 0.987 [0.960, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 19.6 [19.0, 20.8] | 280.8 [256.4, 325.4] | 0.000 |

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

Dropped 1 of 38 non-abstention probes (floor answered correctly: 0; oracle in minority: 1).

## Paired differences against the baseline

Difference is the arm minus the baseline, per fixture. Wilcoxon is the two-sided signed-rank test (exact when n is at most 25 with no tied values); Holm adjusts across all rows of this table.

| Arm | Metric | n | Mean diff | 95% CI | Wilcoxon p | Holm p | SD of diffs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| floor | Primary | 5 | -0.786 | [-0.862, -0.715] | 0.0625 | 0.3268 | 0.095 |
| floor | Recall | 5 | -0.931 | [-1.000, -0.851] | 0.0545 | 0.3268 | 0.096 |
| floor | Precision | 0 | n/a | n/a | n/a | n/a | n/a |
| floor | Placement | 0 | n/a | n/a | n/a | n/a | n/a |
| oracle | Primary | 5 | 0.214 | [0.138, 0.285] | 0.0625 | 0.3268 | 0.095 |
| oracle | Recall | 5 | 0.069 | [0.000, 0.149] | 0.5000 | 0.5000 | 0.096 |
| oracle | Precision | 5 | 0.353 | [0.245, 0.431] | 0.0625 | 0.3268 | 0.121 |
| oracle | Placement | 5 | 0.266 | [0.235, 0.305] | 0.0625 | 0.3268 | 0.044 |

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
| baseline | 516.5 | 1.000 |
| oracle | 280.8 | 0.544 |

## Cost

Dollar figures are the API-price equivalent of each call's reported cost; under a subscription they are not billed. Input tokens count input, cache creation and cache read.

| Call type | Arm | Calls | $ | Input tokens | Output tokens | Wall-clock s |
| --- | --- | --- | --- | --- | --- | --- |
| preserve | baseline | 15 | 2.0464 | 1687520 | 27156 | 239.8 |
| probe | floor | 15 | 0.2272 | 58221 | 3238 | 49.8 |
| probe | baseline | 15 | 0.2718 | 65969 | 4595 | 58.1 |
| probe | oracle | 15 | 0.2553 | 62433 | 4362 | 56.1 |
| judge | judge | 191 | 4.7784 | 647277 | 28428 | 840.8 |
| total |  | 251 | 7.5791 | 2521420 | 67779 | 1244.6 |

baseline preserve runs that changed CLAUDE.md: 15 of 15.

## Missing and invalid

Probe answers missing or unparsable: 0 (counted as incorrect in accuracy, left out of the false-answer rate).
Judge labels invalid: 0. Judge calls this pass: 191; cache hits: 68.

## Failure gallery

### Baseline probe failures (first failing seed per scorable probe)

| Fixture | Probe | Seed | Label | Question | Expected | Answer |
| --- | --- | --- | --- | --- | --- | --- |
| dev-001-csv-tally | p2 | 2 | abstained | Which decimal separator do numeric columns need? | A period ('.'). | UNKNOWN |
| dev-002-notes-api | p3 | 1 | abstained | How long may a note title be? | At most 80 characters. | UNKNOWN |
| dev-002-notes-api | p4 | 1 | abstained | Which module holds the title and body validation? | notes_api/validation.py | UNKNOWN |
| dev-002-notes-api | p6 | 1 | incorrect | Which features have not been started? | Pagination and rate limiting. | Rate limiting, pagination, and docs have not been started. |
| dev-003-sales-etl | p6 | 1 | abstained | Which part of the code is written but has little test coverage? | etl/report.py | UNKNOWN |
| dev-003-sales-etl | p7 | 1 | abstained | In what order is the remaining work to be done? | The monthly rollup first, then the comparison against the finance export. | UNKNOWN |
| dev-004-md-linter | p5 | 3 | abstained | Which keys does each JSON output object have, and which module formats it? | path, line, rule and severity; mdcheck/formats.py. | UNKNOWN |
| dev-004-md-linter | p6 | 1 | incorrect | Where and in what order are new rules registered? | In the RULES list at the bottom of rules.py, alphabetical by rule name. | In the `RULES` registry in `mdcheck/rules.py`, in the order added (not alphabetical). |
| dev-004-md-linter | p10 | 1 | abstained | In what order is the remaining work to be done? | Trailing-space autofix, then --watch mode, then packaging. | UNKNOWN |
| dev-005-flag-service | p6 | 1 | incorrect | Which feature has not been started yet? | Percentage rollouts. | The audit log, percentage rollouts, and admin UI have not been started. |

### Needed items the baseline never matched

| Fixture | Item | Statement |
| --- | --- | --- |
| dev-002-notes-api | j3 | Note titles are limited to 80 characters; the store raises ValueError('title too long (max 80)') beyond that. |
