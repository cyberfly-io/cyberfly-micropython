"""Test schedule module to identify issues"""
import sys
sys.path.insert(0, '/Users/abu/cyberfly/cyberfly-micropython')

from cyberfly_sdk import schedule
import time

print("Testing schedule module...")

# Test 1: Simple periodic job
print("\n1. Testing simple periodic job (every 2 seconds)")
def job1():
    print(f"  Job 1 executed at {time.time()}")
    return "job1 done"

schedule.every(2).seconds.do(job1)
print(f"  Next run scheduled at: {schedule.next_run()}")
print(f"  Idle seconds: {schedule.idle_seconds()}")

# Test 2: Job with specific time
print("\n2. Testing daily job at specific time")
def job2():
    print(f"  Job 2 executed at {time.time()}")

# This should schedule for today or tomorrow
current_time = time.localtime()
test_hour = (current_time[3]) % 24
test_minute = (current_time[4] + 1) % 60
time_str = f"{test_hour:02d}:{test_minute:02d}"
print(f"  Scheduling for {time_str}")
schedule.every().day.at(time_str).do(job2)

# Test 3: Weekly job
print("\n3. Testing weekly job")
def job3():
    print(f"  Job 3 executed at {time.time()}")

schedule.every().monday.at("10:00").do(job3)

# Test 4: Multiple intervals
print("\n4. Testing multiple interval types")
def job4():
    print(f"  Job 4 executed at {time.time()}")

schedule.every(5).minutes.do(job4)
schedule.every(1).hour.do(job4)

# Show all scheduled jobs
print(f"\n5. All scheduled jobs:")
for i, job in enumerate(schedule.jobs(), 1):
    print(f"  Job {i}: {job}")
    print(f"    Next run: {job.next_run}")
    print(f"    Should run: {job.should_run}")
    print(f"    Period: {job.period}")

# Test 6: Run pending
print("\n6. Testing run_pending")
time.sleep(1)
schedule.run_pending()

# Test 7: Test job cancellation
print("\n7. Testing job cancellation")
job_to_cancel = schedule.every(10).seconds.do(job1)
print(f"  Jobs before cancel: {len(schedule.jobs())}")
result = schedule.cancel_job(job_to_cancel)
print(f"  Jobs after cancel: {len(schedule.jobs())}")
print(f"  Cancel result: {result}")

# Test 8: Clear all jobs
print("\n8. Testing clear")
schedule.clear()
print(f"  Jobs after clear: {len(schedule.jobs())}")

# Test 9: Test edge cases
print("\n9. Testing edge cases")
try:
    # Test with interval > 1 for .second (should fail)
    schedule.every(2).second.do(job1)
    print("  ERROR: Should have failed for .second with interval > 1")
except (AssertionError, ValueError) as e:
    print(f"  ✓ Correctly rejected .second with interval > 1: {e}")

try:
    # Test invalid time format
    schedule.every().day.at("25:00").do(job1)
    print("  ERROR: Should have failed for invalid hour")
except (ValueError, AssertionError) as e:
    print(f"  ✓ Correctly rejected invalid time format: {e}")

print("\n10. Testing actual execution")
schedule.clear()
counter = [0]
def counting_job():
    counter[0] += 1
    print(f"  Counting job executed: count = {counter[0]}")

schedule.every(1).seconds.do(counting_job)
print(f"  Scheduled job, waiting 3 seconds...")
start = time.time()
while time.time() - start < 3.5:
    schedule.run_pending()
    time.sleep(0.1)
print(f"  Final count: {counter[0]} (expected: 3)")

# Test 11: Test CancelJob return
print("\n11. Testing CancelJob functionality")
schedule.clear()
def self_canceling_job():
    print("  Self-canceling job executed")
    return schedule.CancelJob

schedule.every(1).seconds.do(self_canceling_job)
print(f"  Jobs before run: {len(schedule.jobs())}")
time.sleep(1.1)
schedule.run_pending()
print(f"  Jobs after run: {len(schedule.jobs())} (should be 0)")

print("\n✓ All tests completed!")
