"""Generate evaluator-facing results from the same machine-readable calculations."""
from pathlib import Path


def write_reports(root: Path, b: dict, q: dict) -> None:
    d,r,g = b['design'],b['analysis']['primary'],b['analysis']['guardrails']
    business,decision = b['business'],b['decision']
    results = f'''| Primary outcome | Control | SMS assignment |
|---|---:|---:|
| Randomized patients | {r['control']['n']:,} | {r['treatment']['n']:,} |
| No-shows | {r['control']['events']:,} | {r['treatment']['events']:,} |
| No-show rate | {r['control']['rate']:.2%} | {r['treatment']['rate']:.2%} |

**Treatment − control: {r['effect_pp']:.2f} percentage points**; relative change **{r['relative_effect_pct']:.2f}%**.
Matching 95% confidence interval: **[{100*r['ci'][0]:.2f}, {100*r['ci'][1]:.2f}] percentage points**.
Two-sided p-value: **{r['p_value']:.6g}**.
Statistically significant improvement: **{b['analysis']['statistically_significant_improvement']}**.
Business point-estimate threshold met: **{b['analysis']['practically_significant_point_estimate']}**.

| Guardrail | Control | SMS | Change (pp) | Safety upper bound (pp) | Margin (pp) | Pass |
|---|---:|---:|---:|---:|---:|---|
'''
    for key,label in [('cancelled','Cancellation'),('complaint','Complaint')]:
        x=g[key]
        results+=f"| {label} | {x['control']['events']}/{x['control']['n']} ({x['control']['rate']:.2%}) | {x['treatment']['events']}/{x['treatment']['n']} ({x['treatment']['rate']:.2%}) | {100*x['effect']:.3f} | {100*x['upper_bound']:.3f} | {100*x['margin']:.2f} | {x['passed']} |\n"
    f=g['delivery_failure'];c=g['cost']
    results+=f"\nTreatment-only delivery failures: **{f['events']}/{f['n']} ({f['rate']:.2%})**, 95% Wilson CI [{f['ci'][0]:.2%}, {f['ci'][1]:.2%}]; upper limit below {f['limit']:.0%}: **{f['passed']}**. No comparison with control is made.\n\n"
    results+=f"Observed incremental SMS expense per appointment: control SAR {c['observed_control_mean_sar']:.2f}, treatment SAR {c['observed_treatment_mean_sar']:.2f}. Assumed rollout unit cost including fixed cost: **SAR {c['rollout_cost_per_appointment_sar']:.2f}**, limit SAR {c['limit']:.2f}; pass: **{c['passed']}**.\n"
    a=business['avoided_no_shows_low_point_high'];net=business['net_value_low_point_high_sar']
    impact=f'''At **{d['monthly_volume']:,} eligible appointments/month**, the estimated avoided no-shows are **{a[1]:.1f}** (primary-CI propagation: {a[0]:.1f} to {a[2]:.1f}).
The separate attendance point estimate corresponds to **{business['potential_attended_slots_point']:.1f}** additional attended slots; it accounts for the estimated cancellation change and is descriptive, without a separate confirmatory claim.

Assume **SAR {d['sms_cost']:.2f}/attempt**, **SAR {d['monthly_fixed_cost']:,.0f}/month** fixed expense, **SAR {d['capacity_value']:.0f}** value per usable slot and **{d['realization']:.0%}** capacity realization. Total monthly incremental cost is **SAR {business['sms_and_fixed_cost_sar']:,.0f}**.
Illustrative net value = avoided no-shows × realization × slot value − cost = **SAR {net[1]:,.0f}/month**, with **SAR {net[0]:,.0f} to {net[2]:,.0f}** when only primary sampling uncertainty is propagated.
These are scenario values, not revenue, observed savings, or a forecast confidence interval. A cancellation may free a slot only if it can be reused; the realization factor captures this imperfect conversion. Fixed costs, implementation effort, traffic, slot value and realization require local validation.
'''
    planning=f'''| Parameter | Prospective value |
|---|---:|
| Assumed control no-show probability | {d['baseline']:.0%} |
| MDE (absolute reduction) | {100*d['mde']:.1f} pp |
| Assumed treatment rate under planning alternative | {d['baseline']-d['mde']:.0%} |
| Alpha / target power | {d['alpha']:.2f} / {d['power']:.0%} |
| Expected sample per group | {d['expected_n_per_arm']:,} |
| Fixed total randomized sample | {d['total_n']:,} |
| Assumed eligible traffic | {d['daily_traffic']} unique patients/calendar day |
| Enrollment duration | {d['enrollment_calendar_days']} calendar days |
| Maximum follow-up after last enrollment | {d['maximum_followup_days']} days |
| Conservative enrollment + follow-up budget | {d['enrollment_calendar_days']+d['maximum_followup_days']} calendar days |
'''
    quality=f"**PASS**: {q['rows']:,} records, no missing required values or duplicate patients. Pearson SRM p = **{q['srm_p_value']:.4f}** (alarm threshold {q['srm_alarm_threshold']}). Maximum absolute covariate SMD = **{max(abs(x['smd']) for x in q['covariate_balance']):.3f}**. Balance warning fields: {', '.join(q['balance_warnings']) or 'none'}.\n"
    summary=f"**Simulated decision: {decision['simulated_decision']}.** {decision['rationale']}\n\n**Real-world action:** {decision['real_world_recommendation']}"
    replacements={'RESULTS':results,'IMPACT':impact,'PLAN':planning,'QUALITY':quality,'DECISION':summary}
    template=Path(__file__).resolve().parents[1]/'docs'/'README.template.md'
    text=template.read_text(encoding='utf-8')
    for key,value in replacements.items():
        text=text.replace('{{'+key+'}}',value)
    (root/'README.md').write_text(text,encoding='utf-8')
    (root/'outputs'/'results'/'summary.md').write_text('# Simulated experiment results\n\n'+summary+'\n\n'+results+'\n'+impact,encoding='utf-8')
    lines=['# Data quality report','',quality,'| Integrity check | Result |','|---|---|']
    lines += [f"| {key} | {'PASS' if value else 'FAIL'} |" for key,value in q['checks'].items()]
    lines+=['',q['interpretation'],'','Full pre-treatment balance: [covariate_balance.csv](covariate_balance.csv).']
    (root/'outputs'/'results'/'data_quality.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
