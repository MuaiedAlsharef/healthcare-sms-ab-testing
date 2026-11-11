# Data quality report

**PASS**: 5,258 records, no missing required values or duplicate patients. Pearson SRM p = **0.3075** (alarm threshold 0.001). Maximum absolute covariate SMD = **0.046**. Balance warning fields: none.

| Integrity check | Result |
|---|---|
| eligible_adults | PASS |
| valid_covariates | PASS |
| one_exclusive_outcome | PASS |
| assignment_at_scheduling | PASS |
| valid_enrollment_window | PASS |
| consistent_lead_time | PASS |
| reminder_24_hours_before | PASS |
| reminder_after_assignment | PASS |
| outcomes_complete | PASS |
| attempts_match_assignment | PASS |
| delivery_requires_attempt | PASS |
| cost_consistent | PASS |

SRM and SMD are diagnostics, not proof of valid randomization; no outcome-based exclusions.

Full pre-treatment balance: [covariate_balance.csv](covariate_balance.csv).
