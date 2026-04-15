#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from app.services.deploy_ops import DeploymentOpsService


def main() -> None:
    result = DeploymentOpsService().preflight()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['overall_status'] == 'error':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
