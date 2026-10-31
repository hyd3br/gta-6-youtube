#!/usr/bin/env bash
set -euo pipefail
cd /workspace/gta-6-youtube
export XDG_CACHE_HOME=/workspace/.cache/gta-6-youtube
export PIP_CACHE_DIR="$XDG_CACHE_HOME/pip"
mkdir -p "$XDG_CACHE_HOME/fontconfig" "$PIP_CACHE_DIR"
command -v python3 >/dev/null
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
test -f /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
test -f /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
python3 -m venv /workspace/.venvs/gta-6-youtube
/workspace/.venvs/gta-6-youtube/bin/python -m pip install -r requirements.txt
/workspace/.venvs/gta-6-youtube/bin/python -m pip check
python3 - <<'PYSETUP'
from pathlib import Path
root = Path.cwd()
# Local-only layout adapters; never modify tracked sources or media.
for directory, sources in (
    ('demo_audio', [f'cena_{i:02d}.wav' for i in range(1, 6)]),
    ('demo_audio_long', ['manifest.json'] + [f'cena_{i:02d}.mp3' for i in range(1, 11)]),
):
    folder = root / directory
    folder.mkdir(exist_ok=True)
    for name in sources:
        source = root / name
        if not source.is_file():
            raise SystemExit(f'Missing bundled asset: {source}')
        target = folder / name
        if target.is_symlink():
            if target.resolve() != source.resolve():
                raise SystemExit(f'Conflicting local symlink: {target}')
        elif target.exists():
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                raise SystemExit(f'Conflicting local asset: {target}')
        else:
            target.symlink_to(Path('..') / name)
# Exclusions are local Git configuration, not a tracked .gitignore change.
import subprocess
exclude = Path(subprocess.check_output(['git', 'rev-parse', '--git-path', 'info/exclude'], text=True).strip())
exclude.parent.mkdir(parents=True, exist_ok=True)
existing = exclude.read_text() if exclude.exists() else ''
patterns = ['/demo_audio/', '/demo_audio_long/', '/work/', '/output/', '/__pycache__/', '/.env', '/.env.local']
missing = [p for p in patterns if p not in existing.splitlines()]
if missing:
    with exclude.open('a') as f:
        if existing and not existing.endswith('\n'):
            f.write('\n')
        f.write('# Cloud onboarding: local assets and generated outputs\n' + '\n'.join(missing) + '\n')
PYSETUP
/workspace/.venvs/gta-6-youtube/bin/python make_long.py --tts bundled --dry-run
