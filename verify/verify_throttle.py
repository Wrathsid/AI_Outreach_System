from backend.services.throttle import throttle_service
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

import sys
sys.path.append(".")

# Mock datetime to always return 10 AM
class MockDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 2, 10, 10, 0, 0)

@patch('backend.services.throttle.datetime', MockDateTime)
async def test_throttle_logic():
    print("--- Verifying Adaptive Throttle Logic ---")
    
    # 1. Reset State
    throttle_service._recent_errors = []
    throttle_service._recent_bounces = []
    throttle_service._last_429 = None
    
    # Mock Supabase
    mock_supabase = MagicMock()
    
    # Create the execute result object that has .data
    mock_execute_result = MagicMock()
    mock_execute_result.data = [{
        "emails_sent": 10,
        "linkedin_sent": 5
    }]
    
    # Chain: throttle sends -> table("dashboard_stats").select("*").eq(..., ...).execute()
    # Note: select("*") returns a builder, .eq() returns a builder, .execute() returns result
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_execute_result
    
    
    
    # 2. Baseline Check (Health 100)
    print("\n1. Baseline Check (Health 100)")
    status = throttle_service.is_safe_to_send(mock_supabase, "email")
    print(f"Health: {throttle_service.calculate_health_score()}")
    print(f"Status: {status}")
    assert status["allowed"] == True
    assert throttle_service.calculate_health_score() == 100
    
    # 3. Simulate Errors (Health Drop)
    print("\n2. Simulate 5 Errors (-25 points)")
    for _ in range(5):
        throttle_service.record_outcome("error")
        
    health = throttle_service.calculate_health_score()
    print(f"Health: {health}")
    assert health == 75
    
    # Check Limits (Should be Mild Throttle 0.8x)
    limits = throttle_service.get_dynamic_limits()
    print(f"Dynamic Limits: {limits}")
    assert limits["email"] == 40 # 50 * 0.8
    
    # 4. Simulate Bounces (Critical Drop)
    print("\n3. Simulate 3 Bounces (-30 points)")
    for _ in range(3):
        throttle_service.record_outcome("bounce")
        
    health = throttle_service.calculate_health_score()
    print(f"Health: {health}") # 75 - 30 = 45
    assert health == 45
    
    # Check Status (Should be PAUSED)
    status = throttle_service.is_safe_to_send(mock_supabase, "email")
    print(f"Status: {status}")
    assert status["allowed"] == False
    assert "Health Critical" in status["reason"]
    
    # 5. Simulate 429 (Immediate Cool-down)
    print("\n4. Simulate Rate Limit (429)")
    throttle_service._recent_errors = [] # Reset to clear health pause
    throttle_service._recent_bounces = []
    throttle_service.record_outcome("429")
    
    status = throttle_service.is_safe_to_send(mock_supabase, "email")
    print(f"Status: {status}")
    assert status["allowed"] == False
    assert "Cooling down" in status["reason"]
    
    print("\n✅ Adaptive Throttle Logic Verified!")

if __name__ == "__main__":
    try:
        asyncio.run(test_throttle_logic())
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
