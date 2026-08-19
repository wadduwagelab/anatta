"""Download benchmark datasets used by the harness.

Sources:
  - FalseQA (Hu et al., ACL 2023): false-premise questions with gold rebuttals.
    https://github.com/thunlp/FalseQA (data/*.csv: question,answer,label; label 1 = false premise)
  - MMLU-Pro (TIGER-Lab): factual MCQs, used both as the capability control and
    as the objective question base for the SycoBench-style pressure protocol.
    Fetched via the Hugging Face datasets-server rows API (no auth needed).
  - SYCON-Bench (Hong et al., EMNLP 2025): multi-turn debate-stance topics.
    https://github.com/JiseungHong/SYCON-Bench (optional; the pressure protocol
    below does not require it, but we fetch topics if reachable).

Run: python3 scripts/download_data.py
"""

import csv
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "anatta-eval/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def save_bytes(path, blob):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    print("saved %s (%d bytes)" % (os.path.relpath(path, ROOT), len(blob)))


def download_falseqa():
    """Prefer the vendored checkout (data/_vendor/FalseQA-main), else fetch raw."""
    vendor = os.path.join(DATA, "_vendor", "FalseQA-main", "dataset")
    for split in ("train.csv", "valid.csv", "test.csv"):
        src = os.path.join(vendor, split)
        if os.path.exists(src):
            with open(src, "rb") as f:
                save_bytes(os.path.join(DATA, "falseqa", split), f.read())
            continue
        try:
            blob = fetch("https://raw.githubusercontent.com/thunlp/FalseQA/main/dataset/" + split)
        except urllib.error.HTTPError as e:
            print("FalseQA %s: HTTP %s -- skipping" % (split, e.code))
            continue
        save_bytes(os.path.join(DATA, "falseqa", split), blob)


def download_mmlu_pro(n_rows=200):
    """Fetch a fixed slice of MMLU-Pro test split via the datasets-server API."""
    rows = []
    offset = 0
    while len(rows) < n_rows:
        length = min(100, n_rows - len(rows))
        url = ("https://datasets-server.huggingface.co/rows?"
               "dataset=TIGER-Lab%%2FMMLU-Pro&config=default&split=test"
               "&offset=%d&length=%d" % (offset, length))
        blob = fetch(url)
        payload = json.loads(blob.decode("utf-8"))
        batch = payload.get("rows", [])
        if not batch:
            break
        for entry in batch:
            row = entry["row"]
            rows.append({
                "question": row["question"],
                "options": row["options"],
                "answer": row["answer"],          # letter
                "answer_index": row["answer_index"],
                "category": row.get("category", ""),
            })
        offset += length
    out = os.path.join(DATA, "mmlu_pro", "subset.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)
    print("saved %s (%d questions)" % (os.path.relpath(out, ROOT), len(rows)))


def download_sycon_topics():
    """Copy SYCON-Bench debate questions/stances from the vendored checkout."""
    vendor = os.path.join(DATA, "_vendor", "SYCON-Bench-master", "debate_setting", "data")
    copied = False
    for fname in ("questions.txt", "arguments.txt"):
        src = os.path.join(vendor, fname)
        if os.path.exists(src):
            with open(src, "rb") as f:
                save_bytes(os.path.join(DATA, "sycon", fname), f.read())
            copied = True
    if not copied:
        print("SYCON-Bench data not found in data/_vendor (optional; "
              "the pressure protocol does not need it).")


def verify_falseqa():
    path = os.path.join(DATA, "falseqa", "test.csv")
    if not os.path.exists(path):
        return
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    fpq = sum(1 for r in rows if str(r.get("label", "")).strip() == "1")
    print("FalseQA test.csv: %d rows (%d false-premise, %d true-premise)"
          % (len(rows), fpq, len(rows) - fpq))


if __name__ == "__main__":
    ok = True
    for step in (download_falseqa, download_mmlu_pro, download_sycon_topics):
        try:
            step()
        except Exception as e:
            ok = False
            print("ERROR in %s: %s" % (step.__name__, e), file=sys.stderr)
    verify_falseqa()
    sys.exit(0 if ok else 1)
