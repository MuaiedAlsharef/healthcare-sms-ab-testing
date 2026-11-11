"""Write or check hashes for reproducible numerical artifacts (PNG metadata excluded)."""
import argparse
import hashlib
import json
from pathlib import Path


def manifest(root: Path) -> dict:
    paths=[root/'README.md',root/'data/appointments.csv']
    paths+=sorted(p for p in (root/'outputs/results').glob('*') if p.name not in ['manifest.json','verification.txt'])
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    path=root/'outputs/results/manifest.json'
    current=manifest(root)
    if args.check:
        assert current==json.loads(path.read_text()),'Reproduced artifacts differ from committed manifest'
        print('All reproducibility hashes match.')
    else:
        path.write_text(json.dumps(current,indent=2)+'\n')
