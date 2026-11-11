"""Independent checks on committed CSV, JSON and rendered report."""
import json
from pathlib import Path
from math import erfc, sqrt
import pandas as pd


def verify(root: Path) -> None:
    df = pd.read_csv(root/'data'/'appointments.csv')
    b = json.loads((root/'outputs/results/analysis.json').read_text())
    r = b['analysis']['primary']
    rates = []
    for arm,label in [(0,'control'),(1,'treatment')]:
        group = df[df.treatment == arm]
        rate = group.no_show.sum()/len(group)
        assert r[label]['n'] == len(group)
        assert r[label]['events'] == int(group.no_show.sum())
        assert abs(rate-r[label]['rate']) < 1e-12
        rates.append(rate)
    effect = rates[1]-rates[0]
    variance = rates[0]*(1-rates[0])/r['control']['n']+rates[1]*(1-rates[1])/r['treatment']['n']
    assert abs(effect-r['effect']) < 1e-12
    assert abs(erfc(abs(effect)/sqrt(2*variance))-r['p_value']) < 1e-12
    text=(root/'README.md').read_text()
    for value in [f"{rates[0]:.2%}",f"{rates[1]:.2%}",f"{100*effect:.2f}",f"{r['p_value']:.6g}",f"{100*r['ci'][0]:.2f}",f"{100*r['ci'][1]:.2f}"]:
        assert value in text, f'Readme missing actual result {value}'
    assert '{{' not in text
    charts=list((root/'outputs/charts').glob('*.png'))
    assert len(charts)==6
    for path in charts:
        assert path.stat().st_size>10000
        assert path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
    print('Verified CSV counts, risk difference, independent p-value, README values and six PNGs.')

if __name__=='__main__':
    verify(Path(__file__).resolve().parents[1])
