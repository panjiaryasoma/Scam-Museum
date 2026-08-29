from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from app.core.service import ScamAnalysisService

src = Path("tests/fixtures/realistic_chat_cases.json")
dst = Path("reports/realistic_chat_v05_audit.json")
cases = json.loads(src.read_text(encoding="utf-8"))["cases"]
svc = ScamAnalysisService()
rows = []
for case in cases:
    out = svc.analyze_message(case["message"])
    rows.append({
        "id": case["id"],
        "kind": case["kind"],
        "family": case["family"],
        "format": case["format"],
        "review_target": case["review_target"],
        "actual_verdict": out["verdict"],
        "target_match": out["verdict"] == case["review_target"],
        "ml_signal": out["ml_signal"],
        "evidence_ids": [x["id"] for x in out["evidence"]],
        "protective_evidence_ids": [x["id"] for x in out["protective_evidence"]],
        "message": case["message"],
    })
report = {
    "version":"0.1",
    "model":"v0.5",
    "n":len(rows),
    "review_target_matches":sum(r["target_match"] for r in rows),
    "review_target_match_rate":sum(r["target_match"] for r in rows)/len(rows),
    "actual_verdict_counts":dict(Counter(r["actual_verdict"] for r in rows)),
    "results":rows,
}
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({k:report[k] for k in ["n","review_target_matches","review_target_match_rate","actual_verdict_counts"]}, indent=2))
print("output:", dst)
