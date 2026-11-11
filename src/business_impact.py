"""Scenario values, not observed healthcare revenue or deployment authorization."""
from .experiment_design import Design


def impact(results: dict, d: Design) -> dict:
    r = results["primary"]
    avoided = [-r["ci"][1]*d.monthly_volume, -r["effect"]*d.monthly_volume, -r["ci"][0]*d.monthly_volume]
    costs = d.monthly_volume*d.sms_cost+d.monthly_fixed_cost
    net = [a*d.capacity_value*d.realization-costs for a in avoided]
    cancellation = results["guardrails"]["cancelled"]
    # Not all avoided no-shows become attended appointments; some become cancellations.
    attendance_change = -r["effect"]-cancellation["effect"]
    return {"monthly_volume":d.monthly_volume,"avoided_no_shows_low_point_high":avoided,
            "estimated_attendance_change_pp":100*attendance_change,
            "potential_attended_slots_point":attendance_change*d.monthly_volume,
            "sms_and_fixed_cost_sar":costs,"value_per_recovered_slot_sar":d.capacity_value,
            "capacity_realization_fraction":d.realization,"net_value_low_point_high_sar":net,
            "interpretation":"CI propagates primary sampling uncertainty only; scenario inputs are assumed."}


def decide(results: dict, business: dict, d: Design) -> dict:
    guards = results["guardrails"]
    if not all(g["passed"] for g in guards.values()):
        decision,reason = "Modify and rerun the experiment", "At least one safety or operational gate is not established."
    elif results["primary"]["ci"][0] > 0:
        decision,reason = "Do not launch", "Evidence indicates increased no-shows."
    elif (results["statistically_significant_improvement"]
          and results["practically_significant_point_estimate"]
          and business["net_value_low_point_high_sar"][0] > 0):
        decision,reason = "Launch", "All pre-specified efficacy, guardrail and conservative scenario-value gates pass."
    else:
        decision,reason = "Inconclusive / collect more evidence", "Evidence does not satisfy all efficacy and value gates."
    return {"simulated_decision":decision,"rationale":reason,
            "real_world_recommendation":"Conduct a prospectively registered real-world randomized pilot; synthetic evidence does not authorize deployment."}
