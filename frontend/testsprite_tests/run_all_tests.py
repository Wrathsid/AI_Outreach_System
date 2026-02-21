import glob
import subprocess
import sys
import time

def run_tests():
    test_files = sorted(glob.glob("TC*.py"))
    results = []

    print(f"Found {len(test_files)} tests.")
    print("-" * 50)

    for test_file in test_files:
        print(f"Running {test_file}...", end=" ", flush=True)
        start_time = time.time()
        
        try:
            # Run the test script
            result = subprocess.run(
                ["python", test_file],
                capture_output=True,
                text=True,
                timeout=60 # 1 minute timeout per test
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"PASSED ({duration:.2f}s)")
                status = "PASS"
            else:
                print(f"FAILED ({duration:.2f}s)")
                status = "FAIL"
                # Print stderr for failure
                print(f"Error output:\n{result.stderr}")
                # Also stdout might contain info
                print(f"Standard output:\n{result.stdout}")

        except subprocess.TimeoutExpired:
            print(f"TIMEOUT ({time.time() - start_time:.2f}s)")
            status = "TIMEOUT"
        except Exception as e:
            print(f"ERROR: {e}")
            status = "ERROR"
            
        results.append((test_file, status))
        print("-" * 50)

    print("\nSummary:")
    print("=" * 50)
    passed = 0
    for name, status in results:
        print(f"{name}: {status}")
        if status == "PASS":
            passed += 1
            
    print("=" * 50)
    print(f"Total: {len(test_files)}, Passed: {passed}, Failed: {len(test_files) - passed}")

if __name__ == "__main__":
    run_tests()
