from backend.services.followup_scheduler import FollowUpScheduler
from backend.services.throttle import throttle_service
from datetime import datetime
from unittest.mock import MagicMock, patch
import asyncio

# Mock datetime to always return 10 AM
class MockDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 2, 10, 10, 0, 0)

@patch('backend.services.followup_scheduler.datetime', MockDateTime)
async def verify_scheduler():
    print("--- Verifying Asymmetric Scheduling (Humanness) ---")
    
    # Mock Supabase
    mock_supabase = MagicMock()
    # Mock insert return
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": 1}]
    
    scheduler = FollowUpScheduler(mock_supabase)
    
    # Test 1: Schedule from 10 AM (Safe Time)
    initial_sent = datetime(2023, 10, 25, 10, 0, 0) # Wed 10 AM
    print(f"\n1. Initial Sent: {initial_sent}")
    
    scheduled = await scheduler.schedule_follow_ups(1, initial_sent)
    
    print("\nScheduled Follow-ups:")
    for item in scheduler.supabase.table.return_value.insert.call_args_list:
        args = item[0][0] # dict
        scheduled_for = datetime.fromisoformat(args["scheduled_for"])
        print(f"  - Day {args['follow_up_number']}: {scheduled_for} (Hour: {scheduled_for.hour})")
        
        # Verify Safe Hours
        assert 9 <= scheduled_for.hour < 18, f"Error: Scheduled time {scheduled_for} outside safe hours!"
        
        # Verify Jitter (Should not be exactly +3 days at 10:00)
        # Note: This is probabilistic but highly likely to not be exact
        if args['follow_up_number'] == 1:
            exact_3_days = initial_sent.replace(day=initial_sent.day + 3)
            assert scheduled_for != exact_3_days, "Error: Time is exactly 3 days later (No jitter?)"
            
    print("\n✅ Asymmetric Scheduling Verified!")

if __name__ == "__main__":
    asyncio.run(verify_scheduler())
