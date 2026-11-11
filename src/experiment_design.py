"""Prospective assumptions: no observed outcomes are used to choose these values."""
from dataclasses import asdict, dataclass
from math import ceil, sqrt
from scipy.stats import norm

@dataclass(frozen=True)
class Design:
    seed: int = 20261111
    alpha: float = 0.05
    power: float = 0.80
    baseline: float = 0.20
    mde: float = 0.03
    daily_traffic: int = 100
    start_date: str = "2026-01-05"
    minimum_business_reduction: float = 0.02
    cancellation_margin: float = 0.02
    complaint_margin: float = 0.005
    maximum_failure_rate: float = 0.08
    maximum_cost_per_appointment: float = 0.50
    sms_cost: float = 0.20
    monthly_fixed_cost: float = 1000.0
    monthly_volume: int = 10000
    capacity_value: float = 100.0
    realization: float = 0.50
    delivery_probability: float = 0.96
    delivered_reduction: float = 0.04


def sample_size(baseline: float = 0.20, mde: float = 0.03,
                alpha: float = 0.05, power: float = 0.80) -> int:
    """Normal two-proportion approximation, equal expected allocation, two-sided."""
    if not (0 < mde < baseline < 1 and 0 < alpha < 1 and 0.5 < power < 1):
        raise ValueError("Invalid planning probabilities")
    p1, p2 = baseline, baseline - mde
    mean = (p1 + p2) / 2
    numerator = (norm.ppf(1-alpha/2)*sqrt(2*mean*(1-mean))
                 + norm.ppf(power)*sqrt(p1*(1-p1)+p2*(1-p2)))**2
    return ceil(numerator / mde**2)


def plan(d: Design) -> dict:
    per_arm = sample_size(d.baseline, d.mde, d.alpha, d.power)
    return {**asdict(d), "expected_n_per_arm": per_arm, "total_n": 2*per_arm,
            "enrollment_calendar_days": ceil(2*per_arm/d.daily_traffic),
            "maximum_followup_days": 31}
