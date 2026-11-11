"""One fixed-seed synthetic experiment; never search across seeds for significance."""
import numpy as np
import pandas as pd
from .experiment_design import Design, plan


def generate_data(d: Design) -> pd.DataFrame:
    n = plan(d)["total_n"]
    rng = np.random.default_rng(d.seed)
    age = rng.integers(18, 81, n)
    prior = rng.binomial(1, 0.25, n)
    lead = rng.integers(2, 31, n)
    distance = rng.uniform(1, 50, n).round(2)
    specialty = rng.choice(["Primary care", "Dental", "Specialist"], n, p=[.5,.2,.3])
    assignment = pd.Timestamp(d.start_date) + pd.to_timedelta(np.arange(n)//d.daily_traffic, unit="D")
    appointment = assignment + pd.to_timedelta(lead, unit="D") + pd.Timedelta(hours=10)
    treatment = rng.binomial(1, .5, n)  # Independent allocation, not rebalanced after seeing draws.
    delivered = treatment * rng.binomial(1, d.delivery_probability, n)
    # Centered baseline covariates: population-average control risk approximately 20%.
    risk0 = d.baseline + .10*(prior-.25) + .002*(lead-16) + .0008*(distance-25.5) - .0005*(age-49)
    risk = risk0 - d.delivered_reduction*delivered
    cancellation_probability = .06 + .003*delivered
    if np.any(risk < 0) or np.any(risk+cancellation_probability > 1):
        raise ValueError("Simulation probabilities outside the valid simplex")
    outcome_draw = rng.random(n)
    no_show = (outcome_draw < risk).astype(int)
    cancelled = ((outcome_draw >= risk) & (outcome_draw < risk+cancellation_probability)).astype(int)
    complaint = (rng.random(n) < (.003 + .001*delivered)).astype(int)
    reminder = appointment - pd.Timedelta(hours=24)
    df = pd.DataFrame({
        "patient_id": [f"SYN-{i:06d}" for i in range(1,n+1)],
        "treatment": treatment, "age": age, "prior_no_show": prior,
        "lead_days": lead, "distance_km": distance, "specialty": specialty,
        "scheduled_at": assignment, "assigned_at": assignment,
        "appointment_at": appointment, "outcome_observed_at": appointment+pd.Timedelta(days=1),
        "reminder_due_at": reminder, "sms_attempted": treatment, "sms_delivered": delivered,
        "no_show": no_show, "cancelled": cancelled, "attended": 1-no_show-cancelled,
        "complaint": complaint, "sms_cost_sar": treatment*d.sms_cost,
        "eligible": np.ones(n,dtype=int)})
    return df
