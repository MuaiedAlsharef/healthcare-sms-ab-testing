"""Fail-fast integrity checks; diagnostics never select or remove observations."""
import numpy as np
import pandas as pd
from scipy.stats import chisquare
from .experiment_design import Design, plan

REQUIRED = ['patient_id','treatment','age','prior_no_show','lead_days','distance_km','specialty',
            'scheduled_at','assigned_at','appointment_at','outcome_observed_at','reminder_due_at',
            'sms_attempted','sms_delivered','no_show','cancelled','attended','complaint','sms_cost_sar','eligible']
DATES = ['scheduled_at','assigned_at','appointment_at','outcome_observed_at','reminder_due_at']


def validate(df: pd.DataFrame, d: Design) -> dict:
    errors = []
    missing = sorted(set(REQUIRED)-set(df.columns))
    if missing:
        raise ValueError(f"Data quality failure: missing columns {missing}")
    if df[REQUIRED].isna().any().any():
        errors.append('Missing values in required fields')
    if len(df) != plan(d)['total_n']:
        errors.append('Unexpected number of randomized patients')
    if df.patient_id.duplicated().any():
        errors.append('Duplicate patient / assignment')
    for col in ['treatment','prior_no_show','sms_attempted','sms_delivered','no_show','cancelled','attended','complaint','eligible']:
        if not df[col].isin([0,1]).all():
            errors.append(f'Invalid binary values: {col}')
    if errors:
        raise ValueError('Data quality failure: '+ '; '.join(errors))
    dates = {col:pd.to_datetime(df[col],errors='coerce',format='mixed') for col in DATES}
    if any(s.isna().any() for s in dates.values()):
        raise ValueError('Data quality failure: invalid dates')
    checks = {
        'eligible_adults':df.eligible.eq(1).all() and df.age.between(18,80).all(),
        'valid_covariates':df.lead_days.between(2,30).all() and df.distance_km.between(1,50).all()
            and df.specialty.isin(['Primary care','Dental','Specialist']).all(),
        'one_exclusive_outcome':df[['no_show','cancelled','attended']].sum(axis=1).eq(1).all(),
        'assignment_at_scheduling':dates['assigned_at'].eq(dates['scheduled_at']).all(),
        'valid_enrollment_window':dates['assigned_at'].between(pd.Timestamp(d.start_date),pd.Timestamp(d.start_date)+pd.Timedelta(days=plan(d)['enrollment_calendar_days']-1)).all(),
        'consistent_lead_time':((dates['appointment_at']-dates['scheduled_at']).dt.total_seconds()/86400).eq(df.lead_days+10/24).all(),
        'reminder_24_hours_before':(dates['appointment_at']-dates['reminder_due_at']).eq(pd.Timedelta(hours=24)).all(),
        'reminder_after_assignment':(dates['reminder_due_at']>dates['assigned_at']).all(),
        'outcomes_complete':(dates['outcome_observed_at']-dates['appointment_at']).eq(pd.Timedelta(days=1)).all(),
        'attempts_match_assignment':df.sms_attempted.eq(df.treatment).all(),
        'delivery_requires_attempt':(df.sms_delivered<=df.sms_attempted).all(),
        'cost_consistent':np.isclose(df.sms_cost_sar,df.sms_attempted*d.sms_cost).all(),
    }
    errors.extend(name for name,passed in checks.items() if not passed)
    counts = df.treatment.value_counts().reindex([0,1],fill_value=0)
    if counts.min() == 0:
        errors.append('An arm is empty')
    srm = float(chisquare(counts.to_numpy(),[len(df)/2]*2).pvalue)
    if srm < .001:
        errors.append('SRM p < 0.001: investigate assignment or missingness before analysis')
    if errors:
        raise ValueError('Data quality failure: '+ '; '.join(errors))
    covariates = df[['age','prior_no_show','lead_days','distance_km']].copy()
    covariates = pd.concat([covariates,pd.get_dummies(df.specialty,prefix='specialty',dtype=int)],axis=1)
    balance = []
    for col in covariates:
        c,t = covariates.loc[df.treatment==0,col],covariates.loc[df.treatment==1,col]
        denominator = np.sqrt((c.var(ddof=1)+t.var(ddof=1))/2)
        smd = float((t.mean()-c.mean())/denominator) if denominator else 0.
        balance.append({'covariate':col,'control_mean':float(c.mean()),'treatment_mean':float(t.mean()),'smd':smd})
    return {'status':'PASS','rows':len(df),'missing_required_values':0,'duplicate_patients':0,
            'checks':{k:bool(v) for k,v in checks.items()},'control_n':int(counts[0]),'treatment_n':int(counts[1]),
            'srm_p_value':srm,'srm_alarm_threshold':.001,'covariate_balance':balance,
            'balance_warnings':[b['covariate'] for b in balance if abs(b['smd'])>.1],
            'interpretation':'SRM and SMD are diagnostics, not proof of valid randomization; no outcome-based exclusions.'}
