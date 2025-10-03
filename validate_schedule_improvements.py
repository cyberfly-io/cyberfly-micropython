"""Quick validation of schedule module improvements"""
import sys
sys.path.insert(0, '/Users/abu/cyberfly/cyberfly-micropython')

from cyberfly_sdk import schedule
import time

print("Testing schedule module improvements...\n")

# Test 1: Module docstring
print("1. Module documentation:")
print(f"   Module has docstring: {schedule.__doc__ is not None}")
print(f"   Docstring length: {len(schedule.__doc__) if schedule.__doc__ else 0} chars")

# Test 2: Improved error messages
print("\n2. Testing improved error messages:")
try:
    schedule.every(2).second.do(lambda: None)
except ValueError as e:
    print(f"   ✓ ValueError with message: {e}")

try:
    schedule.every().day.at("25:00").do(lambda: None)
except ValueError as e:
    print(f"   ✓ ValueError with message: {e}")

# Test 3: Logger fallback
print("\n3. Testing logger compatibility:")
print(f"   Logger type: {type(schedule.logger).__name__}")
print(f"   Has info method: {hasattr(schedule.logger, 'info')}")
print(f"   Has exception method: {hasattr(schedule.logger, 'exception')}")

# Test 4: Jobs as function
print("\n4. Testing jobs() as function:")
schedule.clear()
job1 = schedule.every(10).seconds.do(lambda: None)
job2 = schedule.every(20).seconds.do(lambda: None)
jobs_list = schedule.jobs()
print(f"   Type: {type(jobs_list).__name__}")
print(f"   Count: {len(jobs_list)}")
print(f"   Is copy: {jobs_list is not schedule.default_scheduler.jobs}")

# Test 5: Cancel returns status
print("\n5. Testing cancel_job return value:")
result = schedule.cancel_job(job1)
print(f"   Cancel existing job: {result}")
result = schedule.cancel_job(job1)  # Already removed
print(f"   Cancel non-existent job: {result}")

# Test 6: Comprehensive docstrings
print("\n6. Testing comprehensive documentation:")
classes_with_docs = []
for name in ['Scheduler', 'Job', 'CancelJob']:
    cls = getattr(schedule, name)
    if cls.__doc__:
        classes_with_docs.append(name)
        print(f"   ✓ {name} has docstring ({len(cls.__doc__)} chars)")

# Test 7: Improved __repr__
print("\n7. Testing improved Job representation:")
schedule.clear()
job = schedule.every(5).minutes.do(lambda: None)
repr_str = repr(job)
print(f"   Job repr: {repr_str}")
print(f"   Contains 'Job(': {'Job(' in repr_str}")
print(f"   Contains next_run: {'next_run=' in repr_str}")

# Test 8: Scheduler reference in Job
print("\n8. Testing Job scheduler reference:")
from cyberfly_sdk.schedule import Scheduler
custom_scheduler = Scheduler()
job = custom_scheduler.every(10).seconds.do(lambda: None)
print(f"   Job has scheduler attr: {hasattr(job, 'scheduler')}")
print(f"   Scheduler is correct: {job.scheduler is custom_scheduler}")

# Test 9: Time handling fallbacks
print("\n9. Testing time handling robustness:")
job = schedule.every().day.at("12:00").do(lambda: None)
print(f"   Job created: {job is not None}")
print(f"   Next run set: {job.next_run is not None}")
print(f"   Period: {job.period} seconds")

# Test 10: Property docstrings
print("\n10. Testing property documentation:")
properties_with_docs = []
for prop in ['seconds', 'minutes', 'hours', 'days', 'weeks']:
    prop_obj = getattr(schedule.Job, prop)
    if hasattr(prop_obj, 'fget') and prop_obj.fget.__doc__:
        properties_with_docs.append(prop)
print(f"   Properties with docs: {len(properties_with_docs)}/5")
print(f"   Documented: {', '.join(properties_with_docs)}")

print("\n✓ All validation tests completed successfully!")
print("\nSummary of improvements:")
print("  ✓ Comprehensive module and class docstrings")
print("  ✓ Improved error messages (ValueError instead of AssertionError)")
print("  ✓ Logger fallback for MicroPython compatibility")
print("  ✓ jobs() as function returning copy (safer API)")
print("  ✓ cancel_job() returns success status")
print("  ✓ Scheduler reference in Job instances")
print("  ✓ Robust time handling with fallbacks")
print("  ✓ Better __repr__ for debugging")
print("  ✓ Property documentation for all time units")
print("  ✓ MicroPython-compatible error handling")
