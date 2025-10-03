"""
Schedule Module - Practical Examples
Demonstrates various scheduling patterns for MicroPython IoT devices
"""

from cyberfly_sdk import schedule
import time

# =============================================================================
# Example 1: Basic Periodic Tasks
# =============================================================================

def example_basic_periodic():
    """Simple periodic task scheduling"""
    print("\n=== Example 1: Basic Periodic Tasks ===")
    
    def say_hello():
        print(f"Hello! Current time: {time.time()}")
    
    def check_status():
        print("Checking system status...")
    
    # Schedule tasks
    schedule.every(5).seconds.do(say_hello)
    schedule.every(10).seconds.do(check_status)
    
    print("Running for 30 seconds...")
    start = time.time()
    while time.time() - start < 30:
        schedule.run_pending()
        time.sleep(1)
    
    schedule.clear()
    print("✓ Basic periodic example complete\n")


# =============================================================================
# Example 2: Time-of-Day Scheduling
# =============================================================================

def example_time_of_day():
    """Schedule tasks at specific times"""
    print("\n=== Example 2: Time-of-Day Scheduling ===")
    
    def morning_routine():
        print("Good morning! Starting daily routine...")
    
    def hourly_summary():
        print("Hourly summary report")
    
    # Get current time and schedule for 1 minute from now
    current = time.localtime()
    next_minute = (current[4] + 1) % 60
    next_hour = current[3] if next_minute > current[4] else (current[3] + 1) % 24
    
    time_str = f"{next_hour:02d}:{next_minute:02d}"
    print(f"Scheduling job for {time_str}")
    
    schedule.every().day.at(time_str).do(morning_routine)
    schedule.every().hour.at(":00").do(hourly_summary)
    
    # Show scheduled jobs
    print("\nScheduled jobs:")
    for job in schedule.jobs():
        print(f"  {job}")
    
    schedule.clear()
    print("✓ Time-of-day example complete\n")


# =============================================================================
# Example 3: Sensor Monitoring System
# =============================================================================

def example_sensor_monitoring():
    """Simulate a sensor monitoring system"""
    print("\n=== Example 3: Sensor Monitoring System ===")
    
    # Simulated sensor readings
    sensor_data = {
        'temperature': 25.0,
        'humidity': 60.0,
        'pressure': 1013.25
    }
    
    def read_temperature():
        # Simulate temperature fluctuation
        import random
        sensor_data['temperature'] += random.uniform(-0.5, 0.5)
        print(f"Temperature: {sensor_data['temperature']:.1f}°C")
    
    def read_humidity():
        import random
        sensor_data['humidity'] += random.uniform(-1, 1)
        print(f"Humidity: {sensor_data['humidity']:.1f}%")
    
    def read_pressure():
        import random
        sensor_data['pressure'] += random.uniform(-0.1, 0.1)
        print(f"Pressure: {sensor_data['pressure']:.2f} hPa")
    
    def generate_report():
        print("\n--- Sensor Report ---")
        print(f"Temperature: {sensor_data['temperature']:.1f}°C")
        print(f"Humidity: {sensor_data['humidity']:.1f}%")
        print(f"Pressure: {sensor_data['pressure']:.2f} hPa")
        print("-------------------\n")
    
    # Schedule sensor readings
    schedule.every(2).seconds.do(read_temperature)
    schedule.every(5).seconds.do(read_humidity)
    schedule.every(10).seconds.do(read_pressure)
    schedule.every(15).seconds.do(generate_report)
    
    print("Monitoring sensors for 30 seconds...")
    start = time.time()
    while time.time() - start < 30:
        schedule.run_pending()
        time.sleep(0.5)
    
    schedule.clear()
    print("✓ Sensor monitoring example complete\n")


# =============================================================================
# Example 4: Data Collection and Batching
# =============================================================================

def example_data_batching():
    """Collect data and batch save"""
    print("\n=== Example 4: Data Collection and Batching ===")
    
    data_buffer = []
    
    def collect_data():
        reading = {
            'timestamp': int(time.time()),
            'value': len(data_buffer)
        }
        data_buffer.append(reading)
        print(f"Collected data point {len(data_buffer)}")
    
    def save_batch():
        if data_buffer:
            print(f"\n→ Saving batch of {len(data_buffer)} records")
            # Simulate saving to file/database
            data_buffer.clear()
            print("✓ Batch saved\n")
        else:
            print("No data to save")
    
    # Collect every 2 seconds, save every 10 seconds
    schedule.every(2).seconds.do(collect_data)
    schedule.every(10).seconds.do(save_batch)
    
    print("Running data collection for 25 seconds...")
    start = time.time()
    while time.time() - start < 25:
        schedule.run_pending()
        time.sleep(0.5)
    
    schedule.clear()
    print("✓ Data batching example complete\n")


# =============================================================================
# Example 5: Job Cancellation Patterns
# =============================================================================

def example_job_cancellation():
    """Demonstrate job cancellation patterns"""
    print("\n=== Example 5: Job Cancellation Patterns ===")
    
    counter = [0]
    max_count = 3
    
    # Pattern 1: Self-canceling job
    def limited_job():
        counter[0] += 1
        print(f"Limited job executed: {counter[0]}/{max_count}")
        if counter[0] >= max_count:
            print("→ Job self-canceling")
            return schedule.CancelJob
    
    # Pattern 2: Conditional cancellation
    def conditional_job():
        print("Conditional job running")
        if counter[0] >= 2:
            print("→ Condition met, canceling")
            return schedule.CancelJob
    
    schedule.every(2).seconds.do(limited_job)
    schedule.every(3).seconds.do(conditional_job)
    
    print(f"Jobs scheduled: {len(schedule.jobs())}")
    print("Running for 15 seconds...")
    
    start = time.time()
    while time.time() - start < 15:
        schedule.run_pending()
        time.sleep(0.5)
    
    print(f"Jobs remaining: {len(schedule.jobs())}")
    schedule.clear()
    print("✓ Job cancellation example complete\n")


# =============================================================================
# Example 6: Energy-Efficient Scheduling
# =============================================================================

def example_energy_efficient():
    """Demonstrate energy-efficient scheduling with adaptive sleep"""
    print("\n=== Example 6: Energy-Efficient Scheduling ===")
    
    wake_count = [0]
    sleep_time = [0.0]
    
    def infrequent_task():
        print("Infrequent task executed")
    
    # Schedule infrequent task
    schedule.every(5).seconds.do(infrequent_task)
    
    print("Running with adaptive sleep for 20 seconds...")
    start = time.time()
    
    while time.time() - start < 20:
        idle = schedule.idle_seconds()
        
        if idle is None:
            print("No jobs scheduled")
            break
        elif idle > 1:
            # Sleep until next job (or max 5 seconds)
            sleep_duration = min(idle - 0.5, 5)
            print(f"Sleeping for {sleep_duration:.1f}s (next job in {idle}s)")
            time.sleep(sleep_duration)
            sleep_time[0] += sleep_duration
        else:
            # Job is due soon or overdue
            schedule.run_pending()
            wake_count[0] += 1
            time.sleep(0.1)
    
    print(f"\nEfficiency metrics:")
    print(f"  Wake cycles: {wake_count[0]}")
    print(f"  Total sleep time: {sleep_time[0]:.1f}s")
    print(f"  Sleep ratio: {sleep_time[0]/20*100:.1f}%")
    
    schedule.clear()
    print("✓ Energy-efficient example complete\n")


# =============================================================================
# Example 7: Error Handling
# =============================================================================

def example_error_handling():
    """Demonstrate robust error handling"""
    print("\n=== Example 7: Error Handling ===")
    
    success_count = [0]
    error_count = [0]
    
    def reliable_job():
        success_count[0] += 1
        print(f"✓ Reliable job #{success_count[0]} succeeded")
    
    def risky_job():
        error_count[0] += 1
        print(f"✗ Risky job #{error_count[0]} attempting...")
        if error_count[0] % 2 == 0:
            raise ValueError("Simulated error!")
        print("  → Succeeded this time")
    
    schedule.every(2).seconds.do(reliable_job)
    schedule.every(3).seconds.do(risky_job)
    
    print("Running for 15 seconds (some jobs will fail)...")
    start = time.time()
    while time.time() - start < 15:
        schedule.run_pending()
        time.sleep(0.5)
    
    print(f"\nResults:")
    print(f"  Successful jobs: {success_count[0]}")
    print(f"  Failed jobs: {error_count[0] // 2}")
    print(f"  Jobs still scheduled: {len(schedule.jobs())}")
    
    schedule.clear()
    print("✓ Error handling example complete\n")


# =============================================================================
# Example 8: Multiple Schedulers
# =============================================================================

def example_multiple_schedulers():
    """Use multiple independent schedulers"""
    print("\n=== Example 8: Multiple Schedulers ===")
    
    from cyberfly_sdk.schedule import Scheduler
    
    # Create separate schedulers for different systems
    sensor_scheduler = Scheduler()
    network_scheduler = Scheduler()
    
    def read_sensor():
        print("📊 Reading sensor")
    
    def send_data():
        print("📡 Sending data")
    
    def check_network():
        print("🌐 Checking network")
    
    # Schedule on different schedulers
    sensor_scheduler.every(2).seconds.do(read_sensor)
    network_scheduler.every(3).seconds.do(send_data)
    network_scheduler.every(5).seconds.do(check_network)
    
    print(f"Sensor jobs: {len(sensor_scheduler.jobs)}")
    print(f"Network jobs: {len(network_scheduler.jobs)}")
    print("\nRunning both schedulers for 15 seconds...")
    
    start = time.time()
    while time.time() - start < 15:
        sensor_scheduler.run_pending()
        network_scheduler.run_pending()
        time.sleep(0.5)
    
    print("\n✓ Multiple schedulers example complete\n")


# =============================================================================
# Main Demo Runner
# =============================================================================

def run_all_examples():
    """Run all examples"""
    print("\n" + "="*60)
    print("SCHEDULE MODULE - PRACTICAL EXAMPLES")
    print("="*60)
    
    examples = [
        example_basic_periodic,
        example_time_of_day,
        example_sensor_monitoring,
        example_data_batching,
        example_job_cancellation,
        example_energy_efficient,
        example_error_handling,
        example_multiple_schedulers,
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            print(f"\n[{i}/{len(examples)}] Running {example.__name__}...")
            example()
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Error in {example.__name__}: {e}")
    
    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run all examples
    run_all_examples()
    
    # Or run individual examples:
    # example_basic_periodic()
    # example_sensor_monitoring()
    # example_energy_efficient()
