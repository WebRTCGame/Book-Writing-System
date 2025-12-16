import os
import time
import json
import glob
import shutil
import subprocess
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REQUEST_DIR = os.path.join(ROOT, ".copilot", "requests")
PROCESSED_DIR = os.path.join(ROOT, ".copilot", "processed")
BACKUP_DIR = os.path.join(ROOT, ".copilot", "backups")
AGENT_LOG = os.path.join(ROOT, ".copilot", "agent.log")
ALLOWED_CMDS = {
    "run_checks": {
        "script": os.path.join(ROOT, "tools", "run_checks.py"),
        "allowed_args": ["--full", "--auto-rewrite"]
    }
}

def ensure_dirs():
    for d in (REQUEST_DIR, PROCESSED_DIR, BACKUP_DIR, os.path.dirname(AGENT_LOG)):
        os.makedirs(d, exist_ok=True)

def log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}\n"
    with open(AGENT_LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="")

def load_jsonc(path):
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    s = "\n".join([l for l in s.splitlines() if not l.strip().startswith("//")])
    return json.loads(s)

def run_request(path):
    try:
        req = load_jsonc(path)
    except Exception as e:
        log(f"Failed to parse request {path}: {e}")
        shutil.move(path, os.path.join(PROCESSED_DIR, os.path.basename(path)))
        return
    req_id = req.get("id") or os.path.splitext(os.path.basename(path))[0]
    cmd = req.get("command")
    args = req.get("args", [])
    token = req.get("token")
    # optional basic token check
    token_file = os.path.join(ROOT, ".copilot", "agent_token")
    if os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as tf:
            expected = tf.read().strip()
        if expected and expected != token:
            log(f"Rejected request {req_id}: invalid token")
            shutil.move(path, os.path.join(PROCESSED_DIR, os.path.basename(path)))
            return
    # validate command
    if cmd not in ALLOWED_CMDS:
        log(f"Rejected request {req_id}: command '{cmd}' not allowed")
        shutil.move(path, os.path.join(PROCESSED_DIR, os.path.basename(path)))
        return
    entry = ALLOWED_CMDS[cmd]
    script = entry["script"]
    allowed_args = entry["allowed_args"]
    safe_args = []
    for a in args:
        if a in allowed_args:
            safe_args.append(a)
    # build execution
    run_cmd = ["python", script] + safe_args
    log(f"Executing request {req_id}: {' '.join(run_cmd)}")
    try:
        proc = subprocess.run(run_cmd, cwd=ROOT, capture_output=True, text=True, timeout=3600)
        exit_code = proc.returncode
        out = proc.stdout
        err = proc.stderr
    except Exception as e:
        exit_code = 2
        out = ""
        err = str(e)
    result = {
        "id": req_id,
        "command": cmd,
        "args": safe_args,
        "exit_code": exit_code,
        "stdout": out[:20000],
        "stderr": err[:20000],
        "processed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    result_path = os.path.join(PROCESSED_DIR, f"{req_id}-result.jsonc")
    with open(result_path, "w", encoding="utf-8") as rf:
        json.dump(result, rf, indent=2)
    log(f"Request {req_id} processed; exit_code={exit_code}; result written to {result_path}")
    shutil.move(path, os.path.join(PROCESSED_DIR, os.path.basename(path)))

def main(poll_interval=5):
    ensure_dirs()
    log("Assistant agent started (polling .copilot/requests/)")
    while True:
        files = sorted(glob.glob(os.path.join(REQUEST_DIR, "*.jsonc")))
        for f in files:
            run_request(f)
        time.sleep(poll_interval)

if __name__ == "__main__":
    main()
