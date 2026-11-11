"""Run from the repository root: python main.py."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
from src.experiment_design import Design, plan
from src.generate_data import generate_data
from src.data_quality import validate
from src.statistical_analysis import analyze
from src.business_impact import impact, decide
from src.visualization import charts
from src.reporting import write_reports


def run(root: Path, input_csv: Path | None = None) -> dict:
    d = Design()
    result_dir = root/'outputs'/'results'
    result_dir.mkdir(parents=True,exist_ok=True)
    def dump(name, value):
        (result_dir/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    # Freeze planning parameters before any outcomes are generated or read.
    design = plan(d)
    dump('design.json',design)
    data_dir = root/'data'
    data_dir.mkdir(exist_ok=True)
    if input_csv is None:
        df = generate_data(d)
        df.to_csv(data_dir/'appointments.csv',index=False)
        source_path = data_dir/'appointments.csv'
    else:
        source_path = input_csv
        df = pd.read_csv(source_path)
    try:
        quality = validate(df,d)
    except ValueError as exc:
        dump('data_quality.json',{'status':'FAIL','error':str(exc)})
        raise
    dump('data_quality.json',quality)
    results = analyze(df,d)
    business = impact(results,d)
    decision = decide(results,business,d)
    bundle = {'design':design,'analysis':results,'business':business,'decision':decision,
              'data_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest()}
    dump('analysis.json',bundle)
    pd.DataFrame(quality['covariate_balance']).to_csv(result_dir/'covariate_balance.csv',index=False)
    charts(results,quality,business,d,root/'outputs'/'charts')
    write_reports(root,bundle,quality)
    print(json.dumps({'decision':decision,'primary':results['primary'],'data_quality':quality['status']},indent=2))
    return bundle

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-csv',type=Path,help='Validate and analyze an existing schema-compatible dataset; never regenerate it.')
    args = parser.parse_args()
    run(Path(__file__).resolve().parent,args.input_csv)
