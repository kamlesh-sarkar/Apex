import traceback

def main():
    try:
        from fraud_tracing.orchestrator import FraudTracingOrchestrator
        print("Initializing Fraud Origin Tracing Engine...")
        
        orchestrator = FraudTracingOrchestrator(use_mock=True)
        suspicious_node = "F1"
        result = orchestrator.run_pipeline(fraud_node=suspicious_node)
        
        with open("result.txt", "w") as f:
            f.write(result)
    except Exception as e:
        with open("result.txt", "w") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    main()
