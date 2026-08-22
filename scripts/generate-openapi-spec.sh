#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python -c "
import yaml
from app.main import app
spec = app.openapi()
with open('openapi.yml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False, default_flow_style=False)
"
echo "openapi.yml regenerated"
