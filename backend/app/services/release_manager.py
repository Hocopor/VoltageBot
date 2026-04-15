from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.journal import JournalEntry
from app.models.system import BotRun, SystemEvent
from app.services.codex_auth import CodexAuthService
from app.services.deepseek import DeepSeekClient
from app.services.deploy_ops import DeploymentOpsService
from app.services.operations import OperationsService


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReleaseManagerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.deploy = DeploymentOpsService(db)
        self.ops = OperationsService(db)

    def _acceptance_dir(self) -> Path:
        release_root = Path(self.settings.release_root)
        acceptance_dir = release_root / 'acceptance'
        acceptance_dir.mkdir(parents=True, exist_ok=True)
        return acceptance_dir

    def build_release_report(self) -> dict[str, Any]:
        preflight = self.deploy.preflight()
        readiness = self.deploy.release_readiness()
        codex_status = CodexAuthService().status()
        deepseek_status = DeepSeekClient().status()
        state = self.ops.system_health()

        journal_entries = int(self.db.scalar(select(func.count()).select_from(JournalEntry)) or 0)
        bot_runs = int(self.db.scalar(select(func.count()).select_from(BotRun)) or 0)
        system_events = int(self.db.scalar(select(func.count()).select_from(SystemEvent)) or 0)
        backup_artifacts = self.deploy.list_backup_artifacts(limit=10)
        release_artifacts = self.list_release_artifacts(limit=10)

        checks: list[dict[str, str]] = []

        def add(name: str, status: str, message: str) -> None:
            checks.append({'name': name, 'status': status, 'message': message})

        add('preflight', preflight['overall_status'], f"Preflight status is {preflight['overall_status']}.")
        add('paper-readiness', 'ok' if readiness['ready_for_paper'] else 'error', 'Paper/historical contour is ready.' if readiness['ready_for_paper'] else 'Paper/historical contour is not ready yet.')
        add('live-readiness', 'ok' if readiness['ready_for_live'] else 'warning', 'Live contour can be enabled.' if readiness['ready_for_live'] else 'Live contour still has outstanding blockers or warnings.')
        add('codex-persistence', 'ok' if codex_status.get('connected') else 'warning', 'Codex browser session is persisted.' if codex_status.get('connected') else 'Codex session is not connected yet.')
        add('deepseek-config', 'ok' if deepseek_status.get('configured') else 'warning', 'DeepSeek key configured.' if deepseek_status.get('configured') else 'DeepSeek key is missing, fallback AI mode only.')
        add('backups', 'ok' if backup_artifacts else 'warning', 'Backup artifacts or manifests already exist.' if backup_artifacts else 'No backup artifacts found yet.')
        add('journal-data', 'ok' if journal_entries > 0 else 'warning', f'Journal entries available: {journal_entries}.')
        add('bot-runtime', 'ok' if bot_runs > 0 else 'warning', f'Bot runs recorded: {bot_runs}.')
        add('event-log', 'ok' if system_events > 0 else 'warning', f'System events recorded: {system_events}.')
        add('kill-switch', 'error' if state['kill_switch_armed'] else 'ok', 'Kill switch is armed.' if state['kill_switch_armed'] else 'Kill switch is not armed.')
        add('startup-integrity', 'ok' if state['boot_count'] > 0 and state['last_startup_at'] else 'warning', 'Startup markers present.' if state['boot_count'] > 0 and state['last_startup_at'] else 'Startup markers are incomplete.')

        overall = 'ok'
        if any(item['status'] == 'error' for item in checks):
            overall = 'error'
        elif any(item['status'] == 'warning' for item in checks):
            overall = 'warning'

        recommended_mode = 'blocked'
        if readiness['ready_for_live']:
            recommended_mode = 'live'
        elif readiness['ready_for_paper']:
            recommended_mode = 'paper'
        elif preflight['overall_status'] != 'error':
            recommended_mode = 'historical'

        next_actions: list[str] = []
        if state['kill_switch_armed']:
            next_actions.append('Disarm kill switch only after verifying there are no unintended live positions or open emergency orders.')
        if not codex_status.get('connected'):
            next_actions.append('Complete Codex browser login and verify that the persisted session survives restart.')
        if not deepseek_status.get('configured'):
            next_actions.append('Add DEEPSEEK_API_KEY to .env to enable full AI review and explainability.')
        if not backup_artifacts:
            next_actions.append('Create at least one runtime backup manifest and one real backup artifact before first live deployment.')
        next_actions.extend(readiness['critical_issues'])
        if not next_actions:
            next_actions.append('No critical blockers detected. Proceed with controlled paper validation, then limited live rollout.')

        return {
            'generated_at': utcnow_iso(),
            'project': self.settings.project_name,
            'version': '1.0.0-rc-final',
            'environment': self.settings.environment,
            'preflight': preflight,
            'readiness': readiness,
            'codex': codex_status,
            'deepseek': deepseek_status,
            'state': state,
            'acceptance_checks': checks,
            'overall_status': overall,
            'recommended_mode': recommended_mode,
            'journal_entries': journal_entries,
            'bot_runs': bot_runs,
            'system_events': system_events,
            'backup_artifacts': backup_artifacts,
            'release_artifacts': release_artifacts,
            'next_actions': next_actions,
        }

    def run_release_acceptance(self, trigger: str = 'manual') -> dict[str, Any]:
        acceptance_dir = self._acceptance_dir()
        report = self.build_release_report()
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        base_name = f'release-acceptance-{timestamp}'
        json_path = acceptance_dir / f'{base_name}.json'
        md_path = acceptance_dir / f'{base_name}.md'

        payload = json.dumps(report, ensure_ascii=False, indent=2)
        json_path.write_text(payload, encoding='utf-8')
        md_path.write_text(self._report_markdown(report, trigger=trigger, json_path=json_path), encoding='utf-8')

        self.ops.log_event(
            'info',
            'release',
            'release-acceptance',
            f"Release acceptance generated: {base_name}",
            payload_json=json.dumps({'trigger': trigger, 'json_path': str(json_path), 'md_path': str(md_path), 'overall_status': report['overall_status']}),
        )

        return {
            'generated_at': report['generated_at'],
            'overall_status': report['overall_status'],
            'recommended_mode': report['recommended_mode'],
            'score': report['readiness']['score'],
            'ready_for_paper': report['readiness']['ready_for_paper'],
            'ready_for_live': report['readiness']['ready_for_live'],
            'json_artifact': self._artifact_record(json_path),
            'markdown_artifact': self._artifact_record(md_path),
            'critical_issues': report['readiness']['critical_issues'],
            'warnings': report['readiness']['warnings'],
            'next_actions': report['next_actions'],
        }

    def list_release_artifacts(self, limit: int = 50) -> list[dict[str, Any]]:
        release_root = Path(self.settings.release_root)
        release_root.mkdir(parents=True, exist_ok=True)
        files = sorted([p for p in release_root.rglob('*') if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
        return [self._artifact_record(path) for path in files[:limit]]

    def _artifact_record(self, path: Path) -> dict[str, Any]:
        return {
            'name': path.name,
            'path': str(path),
            'size_bytes': path.stat().st_size,
            'modified_at': datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            'kind': self._artifact_kind(path),
        }

    @staticmethod
    def _artifact_kind(path: Path) -> str:
        lower = path.name.lower()
        if lower.endswith('.json'):
            return 'json'
        if lower.endswith('.md'):
            return 'markdown'
        if lower.endswith('.zip'):
            return 'zip'
        if lower.endswith('.tar.gz') or lower.endswith('.tgz'):
            return 'archive'
        return 'file'

    def _report_markdown(self, report: dict[str, Any], *, trigger: str, json_path: Path) -> str:
        readiness = report['readiness']
        lines = [
            '# VOLTAGE Release Acceptance Report',
            '',
            f"- Generated at: {report['generated_at']}",
            f"- Trigger: {trigger}",
            f"- Project: {report['project']}",
            f"- Version: {report['version']}",
            f"- Environment: {report['environment']}",
            f"- Overall status: **{report['overall_status']}**",
            f"- Recommended mode: **{report['recommended_mode']}**",
            f"- Readiness score: **{readiness['score']}**",
            f"- Ready for paper: **{'yes' if readiness['ready_for_paper'] else 'no'}**",
            f"- Ready for live: **{'yes' if readiness['ready_for_live'] else 'no'}**",
            f"- JSON artifact: `{json_path}`",
            '',
            '## Acceptance checks',
            '',
        ]
        for item in report['acceptance_checks']:
            lines.append(f"- [{item['status']}] **{item['name']}** — {item['message']}")
        lines.extend(['', '## Critical issues', ''])
        if readiness['critical_issues']:
            lines.extend([f'- {item}' for item in readiness['critical_issues']])
        else:
            lines.append('- None')
        lines.extend(['', '## Warnings', ''])
        if readiness['warnings']:
            lines.extend([f'- {item}' for item in readiness['warnings']])
        else:
            lines.append('- None')
        lines.extend(['', '## Next actions', ''])
        lines.extend([f'- {item}' for item in report['next_actions']])
        lines.extend([
            '',
            '## Runtime data snapshot',
            '',
            f"- Journal entries: {report['journal_entries']}",
            f"- Bot runs: {report['bot_runs']}",
            f"- System events: {report['system_events']}",
        ])
        return '\n'.join(lines) + '\n'
