"""
tests/test_client.py
====================
End-to-end integration test against the running Flask server.
Run the server first, then:

    python run.py test
    python tests/test_client.py --url http://localhost:5000
    python tests/test_client.py --url http://localhost:5000 --n 10   # batch
    python tests/test_client.py --url http://localhost:5000 --assert  # exit 1 on any non-2xx
"""

import argparse
import json
import random
import sys

import requests

# A real 'normal' record (row 3 from the NSL-KDD sample used throughout the
# project) and a real 'neptune' (SYN-scan) record, so the demo shows both
# a normal and an anomalous prediction out of the box.
SAMPLE_NORMAL = {
    "duration": 0, "protocoltype": "tcp", "service": "http", "flag": "SF",
    "srcbytes": 232, "dstbytes": 8153, "land": 0, "wrongfragment": 0, "urgent": 0,
    "hot": 0, "numfailedlogins": 0, "loggedin": 1, "numcompromised": 0, "rootshell": 0,
    "suattempted": 0, "numroot": 0, "numfilecreations": 0, "numshells": 0,
    "numaccessfiles": 0, "ishostlogin": 0, "isguestlogin": 0, "count": 5, "srvcount": 5,
    "serrorrate": 0.2, "srvserrorrate": 0.2, "rerrorrate": 0, "srvrerrorrate": 0,
    "samesrvrate": 1.0, "diffsrvrate": 0, "srvdiffhostrate": 0, "dsthostcount": 30,
    "dsthostsrvcount": 255, "dsthostsamesrvrate": 1.0, "dsthostdiffsrvrate": 0,
    "dsthostsamesrcportrate": 0.03, "dsthostsrvdiffhostrate": 0.04,
    "dsthostserrorrate": 0.03, "dsthostsrvserrorrate": 0.01, "dsthostrerrorrate": 0,
    "dsthostsrvrerrorrate": 0.01,
}

SAMPLE_NEPTUNE = {
    "duration": 0, "protocoltype": "tcp", "service": "private", "flag": "S0",
    "srcbytes": 0, "dstbytes": 0, "land": 0, "wrongfragment": 0, "urgent": 0,
    "hot": 0, "numfailedlogins": 0, "loggedin": 0, "numcompromised": 0, "rootshell": 0,
    "suattempted": 0, "numroot": 0, "numfilecreations": 0, "numshells": 0,
    "numaccessfiles": 0, "ishostlogin": 0, "isguestlogin": 0, "count": 123, "srvcount": 6,
    "serrorrate": 1.0, "srvserrorrate": 1.0, "rerrorrate": 0, "srvrerrorrate": 0,
    "samesrvrate": 0.05, "diffsrvrate": 0.07, "srvdiffhostrate": 0, "dsthostcount": 255,
    "dsthostsrvcount": 26, "dsthostsamesrvrate": 0.10, "dsthostdiffsrvrate": 0.05,
    "dsthostsamesrcportrate": 0.0, "dsthostsrvdiffhostrate": 0.0,
    "dsthostserrorrate": 1.0, "dsthostsrvserrorrate": 1.0, "dsthostrerrorrate": 0,
    "dsthostsrvrerrorrate": 0.0,
}


def pretty(label, response):
    print(f"\n--- {label} (HTTP {response.status_code}) ---")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)


def assert_status(label, response, expected=200):
    if response.status_code != expected:
        print(f"\n[FAIL] {label}: expected HTTP {expected}, got {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except ValueError:
            print(response.text)
        return False
    return True


def run_edge_cases(base, strict=False):
    """Exercise validation and edge-case paths."""
    failures = []

    def check(label, resp, expected):
        ok = assert_status(label, resp, expected)
        if not ok:
            failures.append(label)
        else:
            print(f"  [OK] {label}: HTTP {resp.status_code}")

    print("\n=== Edge-case / validation tests ===")

    # 1. Empty body → 400
    check("POST /predict (empty body)",
          requests.post(f"{base}/predict", json={}), 400)

    # 2. Missing required field → 400
    bad_missing = {k: v for k, v in SAMPLE_NORMAL.items() if k != "duration"}
    check("POST /predict (missing 'duration')",
          requests.post(f"{base}/predict", json=bad_missing), 400)

    # 3. Non-numeric value for numeric field → 400
    bad_type = {**SAMPLE_NORMAL, "srcbytes": "not_a_number"}
    check("POST /predict (srcbytes='not_a_number')",
          requests.post(f"{base}/predict", json=bad_type), 400)

    # 4. Rate feature out of range → 400
    bad_rate = {**SAMPLE_NORMAL, "serrorrate": 1.5}
    check("POST /predict (serrorrate=1.5)",
          requests.post(f"{base}/predict", json=bad_rate), 400)

    # 5. Negative bytes → 400
    bad_neg = {**SAMPLE_NORMAL, "srcbytes": -1}
    check("POST /predict (srcbytes=-1)",
          requests.post(f"{base}/predict", json=bad_neg), 400)

    # 6. Unknown protocoltype → 400
    bad_proto = {**SAMPLE_NORMAL, "protocoltype": "ftp"}
    check("POST /predict (protocoltype='ftp')",
          requests.post(f"{base}/predict", json=bad_proto), 400)

    # 7. Unknown flag → 400
    bad_flag = {**SAMPLE_NORMAL, "flag": "BADVAL"}
    check("POST /predict (flag='BADVAL')",
          requests.post(f"{base}/predict", json=bad_flag), 400)

    # 8. Unseen service (should succeed — freq encoding fallback handles it)
    unseen_svc = {**SAMPLE_NORMAL, "service": "totally_unknown_service_xyz"}
    check("POST /predict (unseen service — fallback freq)",
          requests.post(f"{base}/predict", json=unseen_svc), 200)

    # 9. All-zero numeric record (valid)
    zero_record = {**SAMPLE_NORMAL, "srcbytes": 0, "dstbytes": 0,
                   "serrorrate": 0.0, "samesrvrate": 0.0}
    check("POST /predict (all-zero numeric)",
          requests.post(f"{base}/predict", json=zero_record), 200)

    # 10. Large batch (100 records)
    large_batch = [random.choice([SAMPLE_NORMAL, SAMPLE_NEPTUNE]) for _ in range(100)]
    check("POST /predict/full (batch of 100)",
          requests.post(f"{base}/predict/full", json={"data": large_batch}), 200)

    # 11. GET /api/stats
    check("GET /api/stats", requests.get(f"{base}/api/stats"), 200)

    # 12. 404 on unknown route
    check("GET /nonexistent", requests.get(f"{base}/nonexistent_route_xyz"), 404)

    if failures:
        print(f"\n  {len(failures)} edge-case check(s) FAILED: {failures}")
        return False
    print(f"\n  All {12} edge-case checks passed.")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",    default="http://localhost:5000")
    parser.add_argument("--n",      type=int, default=0,
                        help="if > 0, also send a batch of N random-mixed records")
    parser.add_argument("--assert", dest="strict", action="store_true",
                        help="exit with code 1 if any check fails")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    pretty("GET /health",     requests.get(f"{base}/health"))
    pretty("GET /model/info", requests.get(f"{base}/model/info"))

    pretty("POST /predict (normal record)",
           requests.post(f"{base}/predict", json=SAMPLE_NORMAL))
    pretty("POST /predict (neptune/scan record)",
           requests.post(f"{base}/predict", json=SAMPLE_NEPTUNE))

    pretty("POST /predict/attack-type (neptune/scan record)",
           requests.post(f"{base}/predict/attack-type", json=SAMPLE_NEPTUNE))

    pretty("POST /predict/reconstruction (neptune/scan record)",
           requests.post(f"{base}/predict/reconstruction", json=SAMPLE_NEPTUNE))

    pretty("POST /predict/full (normal record)",
           requests.post(f"{base}/predict/full", json=SAMPLE_NORMAL))

    if args.n > 0:
        batch = [random.choice([SAMPLE_NORMAL, SAMPLE_NEPTUNE]) for _ in range(args.n)]
        pretty(f"POST /predict/full (batch of {args.n})",
               requests.post(f"{base}/predict/full", json={"data": batch}))

    all_ok = run_edge_cases(base, strict=args.strict)

    if args.strict and not all_ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
