"""
Smoke test running the 5-agent pipeline on the OOM scenario.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eka.graph import run_pipeline
from eka.scenarios import get_scenario
from eka.db import init_db


def main():
    init_db()
    scenario = get_scenario("oom")
    assert scenario is not None, "OOM scenario missing"
    
    print(f"[TEST] Running pipeline for scenario: {scenario.name}")
    t0 = time.time()
    state = run_pipeline(
        tenant="acme",
        raw_log=scenario.raw_log,
        incident_id=101,
        title=scenario.name,
    )
    elapsed = time.time() - t0

    print("\n=== PIPELINE EXECUTION COMPLETED ===")
    print(f"Elapsed Time:    {elapsed*1000:.1f} ms")
    print(f"Incident ID:     {state.get('incident_id')}")
    print(f"Status:          {state.get('status')}")
    print(f"Policy Decision: {state.get('policy_decision')}")
    print(f"Top Score:       {state.get('top_score', 0):.3f}")
    print(f"Diagnosis:       {state.get('llm_response', {}).get('diagnosis')}")
    print(f"PR URL:          {state.get('pr_url')}")
    print(f"Events ({len(state.get('events', []))}):")
    for ev in state.get("events", []):
        print(f"  [{ev.get('agent')}] -> {ev.get('action')}: {ev.get('detail')}")

    assert state.get("status") in ("PR_OPENED", "AWAITING_APPROVAL", "ALLOWED"), f"Unexpected status: {state.get('status')}"
    print("\n✓ Pipeline smoke test PASSED successfully!")


if __name__ == "__main__":
    main()
