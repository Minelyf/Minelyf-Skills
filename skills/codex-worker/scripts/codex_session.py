#!/usr/bin/env python3
"""Run Codex CLI and keep a local task-to-session index."""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path


FULL_ACCESS = "--dangerously-bypass-approvals-and-sandbox"
SESSION_LINE = re.compile(
    r"session id:\s*([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def session_uuid(value):
    try:
        return str(uuid.UUID(value))
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a session UUID") from error


def parse_args():
    state_option = argparse.ArgumentParser(add_help=False)
    state_option.add_argument(
        "--state-file",
        type=Path,
        default=argparse.SUPPRESS,
        help="override the local session index (default: ${TMPDIR:-/tmp}/codex-worker-sessions.json)",
    )
    parser = argparse.ArgumentParser(description=__doc__, parents=[state_option])
    subcommands = parser.add_subparsers(dest="action", required=True)
    for action in ("start", "resume", "list", "show", "clear"):
        command = subcommands.add_parser(action, parents=[state_option])
        if action != "list":
            command.add_argument("--task", required=True, help="name used to look up the session")
        if action == "start":
            command.add_argument("--cwd", type=Path, help="workspace for the new session")
        if action == "resume":
            command.add_argument("--session-id", type=session_uuid, help="override the saved UUID")
        if action in ("start", "resume"):
            command.add_argument("--skip-git-repo-check", action="store_true")
            command.add_argument("--model")
            command.add_argument("--dry-run", action="store_true", help="print the command without running it")
            prompt = command.add_mutually_exclusive_group()
            prompt.add_argument("--prompt", help="task instructions, or use stdin if omitted")
            prompt.add_argument("--prompt-file", type=Path, help="UTF-8 file containing the instructions")
    return parser.parse_args()


def load_sessions(state_file):
    try:
        with state_file.open(encoding="utf-8") as source:
            sessions = json.load(source)
    except FileNotFoundError:
        return {}
    if not isinstance(sessions, dict):
        raise ValueError("the state file must contain a JSON object")
    for task, record in sessions.items():
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("session_id"), str)
            or not SESSION_LINE.fullmatch("session id: " + record["session_id"])
            or not isinstance(record.get("cwd"), str)
            or not isinstance(record.get("skip_git_repo_check"), bool)
        ):
            raise ValueError(f"invalid session record for task {task!r}")
    return sessions


@contextmanager
def edit_sessions(state_file):
    """Serialize writers and replace the index atomically for concurrent readers."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file = state_file.with_name(state_file.name + ".lock")
    with lock_file.open("a+b") as lock:
        if os.name == "nt":
            import msvcrt

            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock, fcntl.LOCK_EX)
        sessions = load_sessions(state_file)
        yield sessions
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=state_file.parent, delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(sessions, temporary, ensure_ascii=False, indent=2, sort_keys=True)
                temporary.write("\n")
            temporary_path.replace(state_file)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def task_record(sessions, task):
    if task not in sessions:
        raise ValueError(f"no session saved for task {task!r}")
    return sessions[task]


def require_new_task(sessions, task):
    if task in sessions:
        raise ValueError(f"task {task!r} already has a session; use resume or choose a new task name")


def read_prompt(args):
    if args.prompt_file is not None:
        prompt = args.prompt_file.expanduser().read_text(encoding="utf-8")
    elif args.prompt is not None:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()
    else:
        prompt = ""
    if not prompt.strip():
        raise ValueError("provide a prompt with --prompt, --prompt-file or stdin")
    return prompt


def run_codex(command, run_directory, expected_id, save_session):
    saved = False
    with subprocess.Popen(
        command,
        cwd=run_directory,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    ) as process:
        try:
            for line in process.stdout:
                print(line, end="", flush=True)
                match = SESSION_LINE.fullmatch(line.strip()) if not saved else None
                if match:
                    session_id = match.group(1).lower()
                    if expected_id is None or session_id == expected_id:
                        save_session(session_id)
                        saved = True
        except BaseException:
            process.terminate()
            raise
        result = process.wait()
    if not saved:
        print("codex-worker: Codex did not report a matching session ID.", file=sys.stderr)
        return result or 1
    return result


def main():
    args = parse_args()
    default_state_file = Path(os.environ.get("TMPDIR") or "/tmp") / "codex-worker-sessions.json"
    state_file = getattr(args, "state_file", default_state_file).expanduser()
    action = args.action
    try:
        if action == "clear":
            with edit_sessions(state_file) as sessions:
                task_record(sessions, args.task)
                del sessions[args.task]
            return 0

        sessions = load_sessions(state_file)
        if action == "list":
            for task, record in sorted(sessions.items()):
                print(f"{task}\t{record['session_id']}\t{record['cwd']}")
            return 0
        if action == "show":
            print(json.dumps(task_record(sessions, args.task), ensure_ascii=False, indent=2))
            return 0

        command = ["codex", "exec"]
        cwd = Path.cwd()
        run_directory = cwd
        session_id = None
        skip_git_repo_check = args.skip_git_repo_check
        if action == "start":
            require_new_task(sessions, args.task)
            if args.cwd is not None:
                cwd = args.cwd.expanduser().resolve()
        else:
            command.append("resume")
            session_id = args.session_id or task_record(sessions, args.task)["session_id"].lower()
            record = sessions.get(args.task)
            if record and record["session_id"].lower() == session_id:
                cwd = run_directory = Path(record["cwd"])
                skip_git_repo_check = skip_git_repo_check or record["skip_git_repo_check"]

        command.append(FULL_ACCESS)
        if action == "start" and args.cwd is not None:
            command.extend(["-C", str(cwd)])
        if skip_git_repo_check:
            command.append("--skip-git-repo-check")
        if args.model:
            command.extend(["--model", args.model])
        if session_id is not None:
            command.append(session_id)
        prompt = read_prompt(args)
        if prompt.startswith("-") or (action == "start" and prompt in {"resume", "fork", "review", "help"}):
            command.append("--")
        command.append(prompt)

        if args.dry_run:
            displayed = shlex.join(command)
            if run_directory != Path.cwd():
                displayed = f"cd {shlex.quote(str(run_directory))} && {displayed}"
            print(displayed)
            return 0

        def save_session(reported_id):
            with edit_sessions(state_file) as latest:
                if action == "start":
                    require_new_task(latest, args.task)
                latest[args.task] = {
                    "session_id": reported_id,
                    "cwd": str(cwd),
                    "skip_git_repo_check": skip_git_repo_check,
                }

        return run_codex(command, run_directory, session_id, save_session)
    except (OSError, ValueError) as error:
        print(f"codex-worker: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
