"""Unadjusted intention-to-treat analysis; effect sign is treatment minus control."""
from math import sqrt
import numpy as np
import pandas as pd
from scipy.stats import norm
from .experiment_design import Design


def wilson(events: int, n: int, alpha: float = .05) -> list[float]:
    if n <= 0 or not 0 <= events <= n:
        raise ValueError("Invalid binomial counts")
    p, z = events/n, norm.ppf(1-alpha/2)
    denominator = 1+z*z/n
    center = (p+z*z/(2*n))/denominator
    half = z*sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return [max(0.,center-half),min(1.,center+half)]


def compare(df: pd.DataFrame, outcome: str, alpha: float = .05) -> dict:
    arms = []
    for arm in (0, 1):
        values = df.loc[df.treatment == arm, outcome]
        if len(values) < 2 or not values.isin([0,1]).all():
            raise ValueError("Need two nonempty valid binary arms")
        events, n = int(values.sum()), len(values)
        arms.append({"n": n, "events": events, "rate": events/n, "rate_ci": wilson(events,n,alpha)})
    c,t = arms
    effect = t["rate"]-c["rate"]
    se = sqrt(sum(a["rate"]*(1-a["rate"])/a["n"] for a in arms))
    if se == 0:
        raise ValueError("Degenerate variance: normal difference inference not valid")
    z = effect/se
    half = norm.ppf(1-alpha/2)*se
    return {"control":c,"treatment":t,"effect":effect,"effect_pp":100*effect,
            "relative_effect_pct":100*effect/c["rate"] if c["rate"] else None,
            "ci":[effect-half,effect+half],"p_value":float(2*norm.sf(abs(z))),
            "standard_error":se,"method":"Unpooled two-sided Wald z test and matching 95% CI"}


def analyze(df: pd.DataFrame, d: Design) -> dict:
    primary = compare(df,"no_show",d.alpha)
    # Joint safety claim: two Bonferroni-adjusted one-sided 97.5% upper bounds.
    guards = {}
    for metric,margin in [("cancelled",d.cancellation_margin),("complaint",d.complaint_margin)]:
        r = compare(df,metric,d.alpha)
        c, t = r["control"], r["treatment"]
        # Newcombe hybrid Wilson interval avoids a sparse-event Wald safety bound.
        low = r["effect"]-sqrt((t["rate"]-t["rate_ci"][0])**2+(c["rate_ci"][1]-c["rate"])**2)
        high = r["effect"]+sqrt((t["rate_ci"][1]-t["rate"])**2+(c["rate"]-c["rate_ci"][0])**2)
        r.update(ci=[low,high], method="Newcombe hybrid Wilson risk-difference CI",
                 margin=margin, upper_bound=high, passed=bool(high < margin))
        # No confirmatory guardrail superiority p-value is used.
        r.pop("p_value")
        guards[metric] = r
    treated = df.loc[df.treatment == 1]
    failures = int((1-treated.sms_delivered).sum())
    failure_ci = wilson(failures,len(treated))
    # A two-sided 95% Wilson upper limit is a conservative one-sided safety gate.
    guards["delivery_failure"] = {"n":len(treated),"events":failures,"rate":failures/len(treated),
        "ci":failure_ci,"limit":d.maximum_failure_rate,"passed":bool(failure_ci[1]<d.maximum_failure_rate)}
    rollout_unit_cost = d.sms_cost+d.monthly_fixed_cost/d.monthly_volume
    guards["cost"] = {"observed_control_mean_sar":float(df.loc[df.treatment==0,"sms_cost_sar"].mean()),
        "observed_treatment_mean_sar":float(treated.sms_cost_sar.mean()),
        "rollout_cost_per_appointment_sar":rollout_unit_cost,
        "limit":d.maximum_cost_per_appointment,"passed":rollout_unit_cost<=d.maximum_cost_per_appointment}
    return {"primary":primary,"guardrails":guards,
            "statistically_significant_improvement":primary["p_value"]<d.alpha and primary["effect"]<0,
            "practically_significant_point_estimate":primary["effect"]<=-d.minimum_business_reduction}
