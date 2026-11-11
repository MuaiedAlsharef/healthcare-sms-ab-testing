# Do SMS Reminders Reduce Missed Healthcare Appointments?

### A/B Testing and Causal Inference: From Experimental Design to Evidence-Based Decision

Final project for **A/B Testing and Causal Inference**, with acknowledgment to **[SDAIA Academy](https://github.com/SDAIAAcademy)** — برنامج التجارب واختبارات A/B والاستدلال السببي.

> **Synthetic educational experiment.** Every patient, appointment and outcome is simulated. No hospital, partnership, ethics approval or real clinical evidence is claimed. This project demonstrates a reproducible decision process; it does not establish effectiveness in an actual healthcare system.

{{DECISION}}

## Problem, objective and research question

Missed appointments leave clinical capacity unused and can reduce access. The objective is to estimate whether adding an automated SMS reminder **24 hours before the appointment** reduces no-shows enough to justify implementation while protecting operational outcomes.

**Research question:** Does assignment to the SMS reminder policy causally reduce the appointment no-show rate compared with the current process?

**Primary hypothesis:** the SMS policy reduces no-shows. Define Δ = P(no-show | assigned SMS) − P(no-show | assigned control). The confirmatory test is two-sided: **H₀: Δ = 0; H₁: Δ ≠ 0**, with an expected beneficial direction Δ < 0. Positive Δ means harm. There is exactly one primary outcome and one final analysis.

## Results at a glance

{{RESULTS}}

![No-show rates with uncertainty](outputs/charts/01_no_show_rates.png)
![Primary treatment effect](outputs/charts/02_treatment_effect.png)

## Experimental design

| Design element | Prospective policy |
|---|---|
| Target population | Adults booking nonurgent outpatient appointments with SMS access |
| Eligibility | Age 18–80, valid SMS-capable number and permission to receive reminders; appointment booked 2–30 days ahead; one index appointment per patient |
| Exclusions before assignment | Urgent/same-day care, appointments booked <2 days ahead, unavailable mobile contact, no messaging permission, patients already enrolled |
| Experimental and randomization unit | Individual patient with exactly one eligible index appointment |
| Allocation | Independent Bernoulli(0.5) assignment, expected 50/50; actual counts may differ |
| Assignment mechanism | Central computer draw at scheduling, independent of baseline covariates and potential outcomes; concealed until assignment |
| Treatment | Standard scheduling process plus one SMS attempt 24 hours before scheduled time |
| Control | Standard scheduling confirmation; no additional study SMS |
| Repeat-patient policy | Stable patient-ID enrollment registry prevents re-enrollment; no second appointment enters this experiment |
| Compliance | All assigned patients remain in ITT, including failed delivery, ignored reminders and subsequent cancellations |
| Follow-up | Final appointment status and any appointment-related complaint captured through one day after appointment |
| Outcome classification | Mutually exclusive attended, cancelled, no-show; any recorded cancellation before scheduled time is cancelled |
| Stopping | Fixed total enrollment then complete follow-up; no peeking, optional stopping or seed search |
| Blinding | Patients cannot be blinded to SMS; an operational rollout should use automated status capture and analyst-blinded group labels until data lock |
| Estimand | Average assignment-policy effect on no-show probability among eligible unique patients, including delivery failure |

For a real trial, assignment concealment, contact permission, deduplication and outcome capture need an audited implementation. Here, they are design assumptions enforced in the simulator, not claims about an existing organization. A reminder is attempted even if the index appointment subsequently cancels; no resend is modeled. `reminder_due_at` is a scheduled clock time in both groups, not proof of a control SMS.

**Causal identification:** random assignment provides exchangeability; each patient has positive probability of both assignments. Consistency requires a well-defined reminder policy. No interference assumes patients do not share reminders or alter other patients' attendance; unique contact ownership and no household spillovers are assumed. Complete outcome ascertainment avoids differential attrition. Under these assumptions, the unadjusted difference estimates the ITT causal effect **inside the synthetic experiment**. Delivery is post-treatment: conditioning on it would change the estimand and can introduce selection bias, so no per-protocol or delivery-adjusted estimate is used.

## Metrics and decision rules fixed before simulation

**Primary metric:** no-show rate = missed eligible index appointments / **all randomized eligible index appointments**, including cancellations and failed delivery. Unit: patient appointment; reported as a proportion and percentage. No patient is excluded after randomization.

| Metric | Denominator and units | Role |
|---|---|---|
| No-show rate | All randomized patients in each arm; proportion | One primary efficacy metric |
| Cancellation rate | All randomized patients in each arm; proportion | Guardrail; distinguish reduced no-shows from actual attendance |
| Complaint rate | All randomized patients in each arm; ≥1 appointment-related complaint; proportion | Comparable safety outcome, including non-SMS complaints in either arm |
| Delivery failure | All attempted SMS in treatment only; proportion | Operational diagnostic; control is not a failure-rate comparison group |
| Incremental SMS expense | All randomized patients in each arm; SAR/appointment | Observed simulated messaging expense; excludes standard care costs |
| Rollout cost | SMS attempts plus assumed monthly fixed cost / rollout volume; SAR/appointment | Scenario-based cost gate, not an observed full healthcare cost |

The prospective launch rule requires **all** of the following:

1. Two-sided primary p < 0.05 and beneficial effect; 95% CI excludes zero.
2. Point-estimate reduction of at least **2 percentage points**. This is a business target, distinct from the **3 pp planning MDE**. The rule does not require proving the reduction exceeds 2 pp.
3. Upper confidence bound for cancellation increase < **2 pp**, and complaint increase < **0.5 pp**. Two one-sided 97.5% bounds use Bonferroni protection for a joint safety claim. A nonsignificant superiority test is **not** proof of safety.
4. Treatment-only failure-rate 95% Wilson upper limit < **8%**; assumed fully loaded incremental cost ≤ **SAR 0.50/appointment**.
5. Net scenario value remains positive at the least favorable end of the primary 95% CI under the base economic assumptions.

Failure to establish a guardrail → **Modify and rerun the experiment**. If guards pass but evidence shows primary harm → **Do not launch**. All gates passing → **Launch** within the simulation. Otherwise → **Inconclusive / collect more evidence**. A guardrail failure can mean insufficient precision, not necessarily demonstrated harm. No repeat experiment or additional collection should be used as unplanned repeated testing of the same data; any follow-up requires a new protocol.

These thresholds are transparent educational operational tolerances, not empirically validated clinical standards. The study is powered for the primary outcome only; safety gates may be inconclusive.

## Sample size and duration

{{PLAN}}

The baseline is an illustrative planning assumption, not a literature-derived healthcare rate. A 3 pp reduction represents a 15% relative change from a 20% baseline and was selected as an operationally worthwhile, detectable alternative. No pilot outcomes were inspected to choose it.

For p₀ = baseline, p₁ = p₀ − MDE, p̄ = (p₀+p₁)/2:

```text
n_per_group = ceil(
  [z_(1−alpha/2) √(2 p̄(1−p̄))
   + z_power √(p₀(1−p₀) + p₁(1−p₁))]² / (p₁−p₀)²
)
```

This is the standard normal two-proportion planning approximation, without continuity correction. The code calculates it before generating results and saves `outputs/results/design.json`. The fixed total is twice the calculated group size; with independent 50/50 randomization, per-arm counts are **expected**, not guaranteed. The power target is approximate, not an observed post-hoc power claim. No attrition inflation is used because full outcome ascertainment is assumed. Calendar-day traffic includes weekends; a real clinic should substitute its operating-day schedule. Follow-up allows 30-day lead time plus one day for status lock. The simulation dates are fictional, beginning 2026-01-05.

![Power and MDE planning](outputs/charts/03_sample_size.png)

## Dataset and simulation assumptions

`data/appointments.csv` is generated by `src/generate_data.py`, using **NumPy seed 20261111 exactly once per reproducible run**. The same seed is reused to reproduce the same experiment, never searched to produce significance. Planned parameters are defined in the immutable `Design` configuration before outcomes are generated.

| Fields | Meaning |
|---|---|
| `patient_id`, `eligible`, `treatment` | Synthetic unique ID, eligibility flag, randomized assignment (0 control, 1 SMS) |
| `age`, `prior_no_show`, `lead_days`, `distance_km`, `specialty` | Pre-treatment characteristics; prior no-show is a baseline binary history flag |
| `scheduled_at`, `assigned_at`, `appointment_at` | Booking and assignment timestamps; planned index appointment time |
| `reminder_due_at`, `outcome_observed_at` | Planned reminder time and administrative outcome-lock time |
| `sms_attempted`, `sms_delivered`, `sms_cost_sar` | Post-assignment operational variables; zero in control |
| `no_show`, `cancelled`, `attended` | Mutually exclusive final status indicators |
| `complaint` | At least one appointment-related complaint during follow-up |

Age is uniform over integers 18–80, baseline prior no-show probability is 25%, lead time is uniform over integers 2–30, distance is uniform 1–50 km, and specialty proportions are 50% primary care, 20% dental and 30% specialist. These are simplified assumptions, not validated population characteristics. Baseline variables are independent for clarity; realistic correlations and clustering are not modeled.

```text
Control no-show risk = 0.20 + 0.10(prior_no_show − 0.25)
    + 0.002(lead_days − 16) + 0.0008(distance_km − 25.5)
    − 0.0005(age − 49)
Delivery probability among treatment assignments = 0.96
No-show risk after delivery = baseline risk − 0.04
Cancellation probability = 0.06 + 0.003 × delivered
Complaint probability = 0.003 + 0.001 × delivered
```

No-show/cancellation/attendance are sampled as mutually exclusive categories using one uniform draw. Complaints use a separate draw and may overlap any status. The **population simulation truth** is therefore approximately a **−3.84 pp ITT no-show effect** (0.96 × −4 pp), a **+0.288 pp cancellation effect**, and a **+0.096 pp complaint effect**. These inputs are distinct from the **estimated** effects reported above, and from the smaller planning MDE. Treatment effects are imposed by the synthetic mechanism; recovering them is not external clinical validation. Delivery is assumed independent of baseline risk. The linear risk range remains valid for every generated patient; invalid probabilities cause failure instead of clipping.

## Data quality and randomization diagnostics

{{QUALITY}}

The pipeline checks required columns and sample count, missing data, duplicate patient assignments, valid binary values, eligibility, date parsing and ordering, enrollment window, lead time, reminder timing, exclusive outcomes, delivery/attempt logic and costs. A Pearson chi-square **SRM diagnostic with 1 degree of freedom** compares observed counts with independent 50/50 assignment expectations; p < 0.001 stops analysis for investigation. This is appropriate for the Bernoulli design, unlike an exact-balanced design whose allocation counts would be fixed.

Pre-treatment balance uses standardized mean differences (SMDs), with |SMD| > 0.1 flagged descriptively. A small SMD or nonsignificant SRM does not prove randomization validity. Neither SMDs nor primary outcomes are used to rebalance, exclude records or regenerate data. Integrity errors raise an explicit exception and save a failure report; there is no silent cleaning. Missing outcomes would require a new missing-data analysis plan, not deletion.

See [readable quality report](outputs/results/data_quality.md), [machine-readable quality report](outputs/results/data_quality.json), and [balance table](outputs/results/covariate_balance.csv).

![Randomization diagnostics](outputs/charts/04_randomization.png)

## Statistical methodology

The primary estimator is the difference between independent arm means. With thousands of patients and hundreds of events per arm, the **unpooled Wald standard error** is appropriate:

```text
SE = √[p_T(1−p_T)/n_T + p_C(1−p_C)/n_C]
z = (p_T − p_C) / SE
p-value = 2 Φ(−|z|)
95% CI = (p_T − p_C) ± 1.959964 × SE
relative effect (%) = 100 × (p_T − p_C) / p_C
```

The test and CI use the same unpooled variance and therefore agree on zero exclusion. Wilson intervals describe individual group rates. For cancellation and especially sparse complaint outcomes, **Newcombe hybrid Wilson difference intervals** supply the safety upper bounds. Their 95% two-sided upper endpoints serve as one-sided 97.5% bounds; Bonferroni covers the two comparative safety outcomes at approximately 95% joint confidence. The delivery diagnostic uses its own conservative Wilson upper limit. All are approximate repeated-sampling intervals, not probabilities that a particular true effect lies inside them. A nonsignificant primary result means insufficient evidence against the null, not proof of no effect.

No covariate adjustment, subgroup significance search, post-treatment adjustment, multiple primary metrics or repeated looks are used. Relative effects are descriptive; inferential decisions use absolute risk difference. There is no claim of equivalence when a gate fails. Current code fails clearly for degenerate variance rather than reporting spurious certainty.

Method references: [SciPy chi-square diagnostic](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chisquare.html), [statsmodels documentation on independent proportion intervals](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.confint_proportions_2indep.html). The lightweight implementation uses SciPy and implements the published Wilson/Newcombe formulas directly; statsmodels is not a runtime dependency.

![Comparative guardrails](outputs/charts/05_guardrails.png)

## Business impact and recommendation

{{IMPACT}}

![Economic sensitivity](outputs/charts/06_business_sensitivity.png)

{{DECISION}}

## Assumptions, threats and limitations

- **Internal validity:** implementation errors, lost outcomes, differential complaint reporting, contamination, shared mobile contacts and repeat-patient enrollment could compromise a real trial. The simulator enforces simplified versions of these assumptions; diagnostics cannot detect every violation.
- **External validity:** synthetic probabilities, independent covariates, complete records and fixed treatment effects do not capture actual clinics, language accessibility, seasonal effects, patient preferences, rural access or specialty-specific effects. Adult SMS-accessible index appointments do not represent children, urgent care or patients without mobile access.
- **Outcome incentives:** cancellations are not no-shows; reducing the primary metric alone does not guarantee increased attendance or recoverable capacity. Cancellation and attendance are therefore reported alongside it.
- **Uncertainty:** primary power does not guarantee guardrail precision. Normal approximations are not exact finite-sample guarantees. Economic scenario uncertainty is broader than the plotted sampling interval. No clinical outcomes or patient benefit were measured.
- **Real-world requirements:** validate baseline rates and costs, obtain applicable institutional review and messaging permissions, prospectively register a protocol, audit assignment, and run a real randomized pilot before considering rollout. No approval is asserted here.

## Reproduce the project

Use **Python 3.11 or 3.12**. From the repository root:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python main.py
```

The default command deterministically regenerates the synthetic CSV, validates it, analyzes it, saves six PNG charts and JSON/CSV/Markdown results, and renders this README from `docs/README.template.md`. No keys, services, downloads or interactive prompts are required after dependency installation. To validate the committed dataset rather than regenerate it:

```bash
python main.py --input-csv data/appointments.csv
```

An explicit input file is never modified. Only use the input option for this schema and pre-specified design, not arbitrary observational data. The plan and required sample size are unchanged. A failed run may leave outputs from an earlier successful run; always inspect the current `data_quality.json` and process exit status before using reports.

GitHub Actions configuration installs pinned dependencies, runs tests, executes the complete pipeline, and checks committed reproducibility on Python 3.11 and 3.12. Presence of the workflow is not evidence of a successful hosted run; inspect the repository Actions tab after publication.

## Repository structure and technologies

```text
main.py                        # Noninteractive entry point
requirements.txt               # Pinned direct dependencies
README.md                      # Generated evaluator report
LICENSE                        # MIT
src/
  __init__.py
  experiment_design.py         # Prospective configuration and sample size
  generate_data.py              # Fixed-seed synthetic experiment
  data_quality.py               # Fail-fast checks, SRM and balance
  statistical_analysis.py       # ITT effect, intervals and guardrails
  business_impact.py            # Scenario economics and decision rules
  visualization.py             # Six publication-resolution charts
  reporting.py                 # Results-to-README rendering
  verify_outputs.py            # Independent artifact consistency checks
  checksums.py                 # Reproduction manifest
 data/appointments.csv
 docs/README.template.md
 docs/acceptance_checklist.md
 tests/test_project.py
 outputs/charts/*.png
 outputs/results/*
 .github/workflows/python-tests.yml
```

Technologies: Python, NumPy, pandas, SciPy, Matplotlib, pytest and GitHub Actions. Source and synthetic dataset are shared under the MIT license. Author attribution: project contributor; no institutional affiliation or academic credentials are asserted.

## Conclusion

This project connects a prospective randomized design, power analysis, transparent simulation, data-quality gates, ITT causal estimation and an uncertainty-aware operational decision. The recommendation above follows the single fixed-seed result and all pre-specified gates. Its real-world contribution is a reproducible experimental blueprint, not proof that SMS reminders work in a particular healthcare organization.
