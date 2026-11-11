# Simulated experiment results

**Simulated decision: Launch.** All pre-specified efficacy, guardrail and conservative scenario-value gates pass.

**Real-world action:** Conduct a prospectively registered real-world randomized pilot; synthetic evidence does not authorize deployment.

| Primary outcome | Control | SMS assignment |
|---|---:|---:|
| Randomized patients | 2,592 | 2,666 |
| No-shows | 520 | 440 |
| No-show rate | 20.06% | 16.50% |

**Treatment − control: -3.56 percentage points**; relative change **-17.73%**.
Matching 95% confidence interval: **[-5.65, -1.47] percentage points**.
Two-sided p-value: **0.000842478**.
Statistically significant improvement: **True**.
Business point-estimate threshold met: **True**.

| Guardrail | Control | SMS | Change (pp) | Safety upper bound (pp) | Margin (pp) | Pass |
|---|---:|---:|---:|---:|---:|---|
| Cancellation | 151/2592 (5.83%) | 167/2666 (6.26%) | 0.438 | 1.731 | 2.00 | True |
| Complaint | 9/2592 (0.35%) | 10/2666 (0.38%) | 0.028 | 0.382 | 0.50 | True |

Treatment-only delivery failures: **108/2666 (4.05%)**, 95% Wilson CI [3.37%, 4.87%]; upper limit below 8%: **True**. No comparison with control is made.

Observed incremental SMS expense per appointment: control SAR 0.00, treatment SAR 0.20. Assumed rollout unit cost including fixed cost: **SAR 0.30**, limit SAR 0.50; pass: **True**.

At **10,000 eligible appointments/month**, the estimated avoided no-shows are **355.8** (primary-CI propagation: 146.9 to 564.6).
The separate attendance point estimate corresponds to **311.9** additional attended slots; it accounts for the estimated cancellation change and is descriptive, without a separate confirmatory claim.

Assume **SAR 0.20/attempt**, **SAR 1,000/month** fixed expense, **SAR 100** value per usable slot and **50%** capacity realization. Total monthly incremental cost is **SAR 3,000**.
Illustrative net value = avoided no-shows × realization × slot value − cost = **SAR 14,788/month**, with **SAR 4,345 to 25,231** when only primary sampling uncertainty is propagated.
These are scenario values, not revenue, observed savings, or a forecast confidence interval. A cancellation may free a slot only if it can be reused; the realization factor captures this imperfect conversion. Fixed costs, implementation effort, traffic, slot value and realization require local validation.
