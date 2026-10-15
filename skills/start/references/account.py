#!/usr/bin/env python3
"""The accounts the claude CLI can run the audit session on, and the project's choice among them.

  python3 account.py list                       one JSON line per configuration folder: dir, loggedIn, email, org,
                                                current (the one the CLI uses here, from CLAUDE_CONFIG_DIR or the default)
  python3 account.py remember <project> <dir>   make <dir> the project's default: env.CLAUDE_CONFIG_DIR in
                                                <project>/.claude/settings.local.json, the rest of the file kept, and
                                                the file kept out of git (.git/info/exclude) if nothing ignores it yet
  python3 account.py clean-env                  the variables to remove from the environment of a `claude -p` so that
                                                it runs on its CLAUDE_CONFIG_DIR's account, as `-u NAME` arguments of
                                                `env` (nothing when there are none)
  python3 account.py check <dir> <email>        before every resume or relaunch: whether <dir> is still logged in as
                                                <email>, the account the register records. Exit 0 if so; 1 if not,
                                                with one JSON line: expected, found, loggedIn, and `elsewhere`, the
                                                other folders logged in as <email>
  python3 account.py check --session <email>    the same for an `--in-session` audit, against the account of the
                                                session that runs this (CLAUDE_CODE_USER_EMAIL): 0 the same, 1 another,
                                                3 unknown (no such variable: the check cannot be made)

An audit is billed to the account that launched it, and to no other: a resume, automatic, scheduled or by hand, goes on
only on that account. `check` is how the launcher holds it, since a folder's login may change while an audit waits.

A session started by another (the Claude desktop app, an Agent SDK host, a `claude` session) hands its children its own
credentials: a local proxy (ANTHROPIC_BASE_URL, with CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH or CLAUDE_CODE_ACCOUNT_UUID),
or a token (ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, CLAUDE_CODE_OAUTH_TOKEN). Any of them wins over CLAUDE_CONFIG_DIR,
so a `claude -p` launched with them is billed to the parent's account whatever folder it is given, while
`claude auth status` still names the folder's. `clean-env` lists them; the launcher removes them.

The configuration folders are ~/.claude, the CLI's default, and every ~/.claude-* folder, where another account may
be logged in (CLAUDE_CONFIG_DIR="$HOME/.claude-<name>" claude auth login). Nothing here logs in, logs out, or changes
the default: that stays the user's.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


HOST_AUTH = ("CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH", "CLAUDE_CODE_ACCOUNT_UUID", "CLAUDE_CODE_ORGANIZATION_UUID",
             "CLAUDE_CODE_USER_EMAIL", "CLAUDE_CODE_OAUTH_SCOPES")
TOKENS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")


def inherited_auth(environ=os.environ):
    """The variables through which a parent session's credentials reach a child `claude`."""
    names = [n for n in HOST_AUTH + TOKENS if n in environ]
    # A base URL is the parent's proxy only when the parent says it holds the auth; set by the user, it is kept.
    if "ANTHROPIC_BASE_URL" in environ and any(n in environ for n in HOST_AUTH):
        names.append("ANTHROPIC_BASE_URL")
    return names


def clean_env(environ=os.environ):
    return {k: v for k, v in environ.items() if k not in inherited_auth(environ)}


def status(config):
    env = dict(clean_env(), CLAUDE_CONFIG_DIR=str(config))
    try:
        r = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, env=env, timeout=60)
        return json.loads(r.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"loggedIn": False}


def norm(path):
    return os.path.normcase(os.path.abspath(os.path.expanduser(str(path))))


def folders():
    """~/.claude, every ~/.claude-* folder, and the current one first if it is neither."""
    home = Path.home()
    current = norm(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude")
    dirs = [home / ".claude"] + sorted(p for p in home.glob(".claude-*") if p.is_dir())
    if current not in {norm(d) for d in dirs}:
        dirs.insert(0, Path(current))
    return dirs, current


def same(a, b):
    return bool(a) and bool(b) and a.strip().lower() == b.strip().lower()


def check(config, email):
    s = status(Path(os.path.expanduser(config)))
    if s.get("loggedIn") and same(s.get("email"), email):
        return 0
    elsewhere = [Path(d).as_posix() for d in folders()[0]
                 if norm(d) != norm(config) and same(status(d).get("email"), email)]
    print(json.dumps({"dir": Path(config).as_posix(), "expected": email, "found": s.get("email"),
                      "loggedIn": bool(s.get("loggedIn")), "elsewhere": elsewhere}, ensure_ascii=False))
    return 1


def check_session(email, environ=os.environ):
    found = environ.get("CLAUDE_CODE_USER_EMAIL")
    if not found:
        print(json.dumps({"expected": email, "found": None}))
        return 3
    if same(found, email):
        return 0
    print(json.dumps({"expected": email, "found": found}, ensure_ascii=False))
    return 1


def list_accounts():
    dirs, current = folders()
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
    if len(sys.argv) == 2 and sys.argv[1] == "clean-env":
        print(" ".join(f"-u {n}" for n in inherited_auth()))
        return 0
    if len(sys.argv) == 4 and sys.argv[1] == "remember":
        return remember(sys.argv[2], sys.argv[3])
    if len(sys.argv) == 4 and sys.argv[1] == "check":
        return check_session(sys.argv[3]) if sys.argv[2] == "--session" else check(sys.argv[2], sys.argv[3])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
