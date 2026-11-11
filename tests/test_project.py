"""Behavioral and numerical tests, including corrupt data and alternative decisions."""
from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from main import run
from src.experiment_design import Design,plan,sample_size
from src.generate_data import generate_data
from src.data_quality import validate
from src.statistical_analysis import compare,analyze,wilson
from src.business_impact import impact,decide
from src.verify_outputs import verify

@pytest.fixture
def data():
    return generate_data(Design())


def test_planning_benchmark_and_sensitivity():
    assert sample_size()==2629
    assert sample_size(mde=.02)>sample_size(mde=.03)
    assert sample_size(power=.9)>sample_size(power=.8)
    assert plan(Design())['total_n']==5258

@pytest.mark.parametrize('kwargs',[{'mde':0},{'mde':.3},{'alpha':1},{'power':.4}])
def test_invalid_planning(kwargs):
    with pytest.raises(ValueError):
        sample_size(**kwargs)


def test_reproducible_randomization_and_population(data):
    pd.testing.assert_frame_equal(data,generate_data(Design()))
    assert len(data)==5258
    assert data.patient_id.is_unique
    assert set(data.treatment)=={0,1}
    assert .45<data.treatment.mean()<.55
    assert data.sms_attempted.equals(data.treatment)
    assert validate(data,Design())['status']=='PASS'

@pytest.mark.parametrize('column,value',[
    ('no_show',2),('age',17),('treatment',3),('sms_cost_sar',-1),
    ('assigned_at','bad-date'),('eligible',0),('specialty','Unknown'),
    ('outcome_observed_at','2000-01-01'),('lead_days',1),('patient_id',None)])
def test_corrupt_records_fail(data,column,value):
    broken=data.copy()
    broken[column]=broken[column].astype(object)
    broken.loc[0,column]=value
    with pytest.raises(ValueError,match='Data quality failure'):
        validate(broken,Design())


def test_duplicate_and_missing_column_fail(data):
    data.loc[1,'patient_id']=data.loc[0,'patient_id']
    with pytest.raises(ValueError,match='Duplicate'):
        validate(data,Design())
    with pytest.raises(ValueError,match='missing columns'):
        validate(data.drop(columns=['no_show']),Design())


def test_sample_loss_fails(data):
    with pytest.raises(ValueError,match='number'):
        validate(data.iloc[:-1],Design())


def test_srm_detects_invalid_assignment(data):
    data['treatment']=0
    data.loc[:3999,'treatment']=1
    data['sms_attempted']=data.treatment
    data['sms_delivered']=data.treatment
    data['sms_cost_sar']=data.treatment*.2
    with pytest.raises(ValueError,match='SRM'):
        validate(data,Design())


def test_comparison_known_counts_and_direction():
    df=pd.DataFrame({'treatment':[0]*1000+[1]*1000,'y':[1]*200+[0]*800+[1]*150+[0]*850})
    r=compare(df,'y')
    assert r['effect']==pytest.approx(-.05)
    assert r['relative_effect_pct']==pytest.approx(-25)
    assert r['standard_error']==pytest.approx(np.sqrt(.2*.8/1000+.15*.85/1000))
    assert r['ci'][0]<r['effect']<r['ci'][1]<0
    assert 0<r['p_value']<.05
    swapped=compare(df.assign(treatment=1-df.treatment),'y')
    assert swapped['effect']==pytest.approx(-r['effect'])
    assert swapped['p_value']==pytest.approx(r['p_value'])


def test_equal_rates_not_significant():
    df=pd.DataFrame({'treatment':[0]*100+[1]*100,'y':([1]*20+[0]*80)*2})
    r=compare(df,'y')
    assert r['p_value']==pytest.approx(1)
    assert r['ci'][0]<0<r['ci'][1]


def test_wilson_boundary_behavior():
    low,high=wilson(0,100)
    assert low==pytest.approx(0)
    assert high==pytest.approx(.0369934982)
    assert wilson(100,100)[1]==pytest.approx(1)


def test_decision_gates_and_economics(data):
    d=Design();r=analyze(data,d);b=impact(r,d)
    assert b['sms_and_fixed_cost_sar']==3000
    assert b['net_value_low_point_high_sar'][1]==pytest.approx(-r['primary']['effect']*10000*50-3000)
    assert decide(r,b,d)['simulated_decision']=='Launch'
    failed=deepcopy(r);failed['guardrails']['complaint']['passed']=False
    assert decide(failed,b,d)['simulated_decision']=='Modify and rerun the experiment'
    uncertain=deepcopy(r);uncertain['statistically_significant_improvement']=False
    assert decide(uncertain,b,d)['simulated_decision']=='Inconclusive / collect more evidence'
    harm=deepcopy(r);harm['primary']['ci']=[.01,.03]
    assert decide(harm,b,d)['simulated_decision']=='Do not launch'
    expensive=deepcopy(b);expensive['net_value_low_point_high_sar'][0]=-1
    assert decide(r,expensive,d)['simulated_decision']=='Inconclusive / collect more evidence'


def test_complete_pipeline_and_persisted_input(tmp_path):
    bundle=run(tmp_path)
    verify(tmp_path)
    before=(tmp_path/'data/appointments.csv').read_bytes()
    reproduced=run(tmp_path,tmp_path/'data/appointments.csv')
    assert bundle==reproduced
    assert before==(tmp_path/'data/appointments.csv').read_bytes()
    quality=json.loads((tmp_path/'outputs/results/data_quality.json').read_text())
    assert quality['status']=='PASS'
    corrupt=pd.read_csv(tmp_path/'data/appointments.csv').iloc[:-1]
    corrupt.to_csv(tmp_path/'bad.csv',index=False)
    with pytest.raises(ValueError):
        run(tmp_path,tmp_path/'bad.csv')
    assert json.loads((tmp_path/'outputs/results/data_quality.json').read_text())['status']=='FAIL'
