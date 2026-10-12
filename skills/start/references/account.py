#!/usr/bin/env python3
"""The accounts the claude CLI can run the audit session on, and the project's choice among them.

  python3 account.py list                       one JSON line per configuration folder: dir, loggedIn, email, org,
                                                current (the one the CLI uses here, from CLAUDE_CONFIG_DIR or the default)
  python3 account.py remember <project> <dir>   make <dir> the project's default: env.CLAUDE_CONFIG_DIR in
                                                <project>/.claude/settings.local.json, the rest of the file kept, and
                                                the file kept out of git (.git/info/exclude) if nothing ignores it yet

The configuration folders are ~/.claude, the CLI's default, and every ~/.claude-* folder, where another account may
be logged in (CLAUDE_CONFIG_DIR="$HOME/.claude-<name>" claude auth login). Nothing here logs in, logs out, or changes
the default: that stays the user's.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def status(config):
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config))
    try:
        r = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, env=env, timeout=60)
        return json.loads(r.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"loggedIn": False}


def norm(path):
    return os.path.normcase(os.path.abspath(os.path.expanduser(str(path))))


def list_accounts():
    home = Path.home()
    current = norm(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude")
    dirs = [home / ".claude"] + sorted(p for p in home.glob(".claude-*") if p.is_dir())
    if current not in {norm(d) for d in dirs}:
        dirs.insert(0, Path(current))
    for d in dirs:
        s = status(d)
        print(json.dumps({"dir": Path(d).as_posix(), "loggedIn": bool(s.get("loggedIn")), "email": s.get("email"),
                          "org": s.get("orgName"), "current": norm(d) == current}, ensure_ascii=False))
    return 0


def remember(project, config):
    project, config = Path(project), Path(os.path.expanduser(config))
    if not status(config).get("loggedIn"):
        print(f"account: {config.as_posix()} is not logged in; nothing written", file=sys.stderr)
        return 1
    settings = project / ".claude" / "settings.local.json"
    data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    data.setdefault("env", {})["CLAUDE_CONFIG_DIR"] = config.as_posix()
    settings.parent.mkdir(exist_ok=True)
    settings.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    git = ["git", "-C", str(project)]
    if subprocess.run(git + ["check-ignore", "-q", ".claude/settings.local.json"]).returncode != 0:
        exclude = subprocess.run(git + ["rev-parse", "--git-path", "info/exclude"],
                                 capture_output=True, text=True).stdout.strip()
        if exclude:
            exclude = Path(exclude) if Path(exclude).is_absolute() else project / exclude
            exclude.parent.mkdir(parents=True, exist_ok=True)
            with exclude.open("a", encoding="utf-8") as f:
                f.write("\n.claude/settings.local.json\n")
    print(f"account: {settings.as_posix()} now sets CLAUDE_CONFIG_DIR={config.as_posix()}")
    return 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "list":
        return list_accounts()
    if len(sys.argv) == 4 and sys.argv[1] == "remember":
        return remember(sys.argv[2], sys.argv[3])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
