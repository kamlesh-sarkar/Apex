import sys, traceback, time

log = open("test_output.txt", "w", encoding="utf-8")

def p(msg):
    print(msg, flush=True)
    log.write(msg + "\n")
    log.flush()

try:
    p("=== Fraud Tracing Engine Test ===")

    t0 = time.time()
    p("Importing orchestrator...")
    from fraud_tracing.orchestrator import FraudTracingOrchestrator
    p(f"  Import OK ({time.time()-t0:.2f}s)")

    t1 = time.time()
    p("Creating orchestrator (mock=True)...")
    o = FraudTracingOrchestrator(use_mock=True)
    p(f"  Orchestrator ready ({time.time()-t1:.2f}s)")

    t2 = time.time()
    p("Running pipeline for F1...")
    result = o.run_pipeline(fraud_node="F1")
    p(f"  Pipeline done ({time.time()-t2:.2f}s)")

    p("\n--- RESULT ---")
    p(result)
    p(f"\nTotal elapsed: {time.time()-t0:.2f}s")

except Exception as e:
    msg = traceback.format_exc()
    p("ERROR:\n" + msg)

log.close()
