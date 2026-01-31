import sys
import os
import time

# Ensure backend directory is in path
sys.path.append(os.path.abspath("c:/Users/Siddharth/OneDrive/Desktop/Cold emailing/backend"))

from services.discovery_orchestrator import DiscoveryOrchestrator

def test_orchestrator():
    print("Initializing Orchestrator...")
    orchestrator = DiscoveryOrchestrator()
    
    query = "Recruiter at Apple" # High probability of results
    print(f"Testing stream for query: '{query}'")
    
    count = 0
    for result_json in orchestrator.discover_leads_stream(query, limit=5):
        print(f"Received: {result_json.strip()}")
        if '"type": "result"' in result_json:
            count += 1
            
    print(f"Test Finished. Found {count} leads.")

if __name__ == "__main__":
    test_orchestrator()
