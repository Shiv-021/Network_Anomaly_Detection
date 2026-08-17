"""
run.py — Network Anomaly Detection CLI Orchestrator
====================================================
A single entry point for the full pipeline.

Usage
-----
    python run.py train           # Blocks 1-3: train models → save artifacts
    python run.py train --no-plots
    python run.py train --data path/to/data.csv

    python run.py serve           # start Flask API at http://localhost:5000
    python run.py serve --port 8080
    python run.py serve --debug

    python run.py all             # train THEN serve (one command, end-to-end)
    python run.py all --no-plots

    python run.py status          # check which model artifacts exist
    python run.py test            # run tests/test_client.py against the server
"""

import argparse
import os
import sys
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from config.settings import MODEL_DIR, REQUIRED_ARTIFACTS  # noqa: E402


def check_status():
    """Print which model artifacts are present / missing."""
    print("\n=== Model artifact status ===")
    all_ok = True
    for name in REQUIRED_ARTIFACTS:
        path   = os.path.join(MODEL_DIR, name)
        exists = os.path.exists(path)
        size   = f"{os.path.getsize(path)/1024:.0f} KB" if exists else "---"
        status = "[OK]" if exists else "[!!] MISSING"
        print(f"  {status:14s}  {name:40s}  {size}")
        if not exists:
            all_ok = False
    if all_ok:
        print("\n  All artifacts present — server is ready to start.")
    else:
        print("\n  Some artifacts are missing. Run:  python run.py train")
    return all_ok


def run_train(extra_args):
    """Run backend/app/train.py (Blocks 1-3)."""
    cmd = [sys.executable, os.path.join(PROJECT_DIR, "backend", "app", "ml_model_pipeline", "train.py")] + extra_args
    print(f"\n>>> Running training pipeline…")
    print(f"    Command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print("\n[ERROR] Training pipeline exited with errors. Check output above.")
        sys.exit(result.returncode)
    print("\n[OK] Training complete. Artifacts saved to ml_model_pipeline/model_artifacts/")


def run_serve(port, debug):
    """Start the Flask app (app.py)."""
    env = os.environ.copy()
    env["PORT"]        = str(port)
    env["FLASK_DEBUG"] = "1" if debug else "0"
    env["MODEL_DIR"]   = MODEL_DIR

    if not any(os.path.exists(os.path.join(MODEL_DIR, a)) for a in REQUIRED_ARTIFACTS):
        print("\n[ERROR] No model artifacts found.")
        print("        Run  python run.py train  first to generate them.")
        sys.exit(1)

    cmd = [sys.executable, os.path.join(PROJECT_DIR, "app.py")]
    print(f"\n>>> Starting Flask API on http://0.0.0.0:{port}")
    print(f"    Debug: {debug}")
    print(f"    Model dir: {MODEL_DIR}")
    print(f"    Command: {' '.join(cmd)}\n")
    print("    Press Ctrl+C to stop.\n")
    result = subprocess.run(cmd, cwd=PROJECT_DIR, env=env)
    if result.returncode not in (0, -2):
        sys.exit(result.returncode)


def run_test(url):
    """Run tests/test_client.py against the running server."""
    cmd = [sys.executable, os.path.join(PROJECT_DIR, "tests", "test_client.py"),
           "--url", url, "--n", "5"]
    print(f"\n>>> Running test client against {url} …\n")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Network Anomaly Detection — end-to-end orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- train ---
    train_parser = subparsers.add_parser("train", help="Run Blocks 1-3 training pipeline")
    train_parser.add_argument("--data",     default=None,
                              help="Path to local CSV (skips Google Drive download)")
    train_parser.add_argument("--no-plots", action="store_true",
                              help="Skip saving plots (headless / faster mode)")

    # --- serve ---
    serve_parser = subparsers.add_parser("serve", help="Start Flask API (Block 4)")
    serve_parser.add_argument("--port",  type=int, default=5000, help="Port (default 5000)")
    serve_parser.add_argument("--debug", action="store_true",    help="Flask debug mode")

    # --- all ---
    all_parser = subparsers.add_parser("all", help="Train then serve (full pipeline)")
    all_parser.add_argument("--data",     default=None, help="Path to local CSV")
    all_parser.add_argument("--no-plots", action="store_true")
    all_parser.add_argument("--port",  type=int, default=5000)
    all_parser.add_argument("--debug", action="store_true")

    # --- status ---
    subparsers.add_parser("status", help="Show which model artifacts are present")

    # --- test ---
    test_parser = subparsers.add_parser("test", help="Run tests/test_client.py against the server")
    test_parser.add_argument("--url", default="http://localhost:5000")

    args = parser.parse_args()

    if args.command == "status":
        check_status()

    elif args.command == "train":
        extra = []
        if args.data:
            extra += ["--data", args.data]
        if args.no_plots:
            extra += ["--no-plots"]
        run_train(extra)

    elif args.command == "serve":
        run_serve(args.port, args.debug)

    elif args.command == "all":
        extra = []
        if args.data:
            extra += ["--data", args.data]
        if args.no_plots:
            extra += ["--no-plots"]
        run_train(extra)
        print("\n" + "=" * 60)
        print("Training done — starting Flask server…")
        print("=" * 60)
        run_serve(args.port, args.debug)

    elif args.command == "test":
        run_test(args.url)


if __name__ == "__main__":
    main()
