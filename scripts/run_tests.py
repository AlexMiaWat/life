#!/usr/bin/env python3

import subprocess
import sys
import os

def run_tests():
    """Run all tests and capture output"""
    try:
        # Change to project root
        os.chdir('/workspace')

        # Run pytest with XML output
        result = subprocess.run([
            sys.executable, '-m', 'pytest',
            'src/test/',
            '--junitxml=test_results.xml',
            '--tb=short'
        ], capture_output=True, text=True, timeout=120)  # 2 minute timeout

        # Write results to file
        with open('test_execution_output.txt', 'w') as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)
            f.write(f"\n\nReturn code: {result.returncode}")

        print(f"Tests completed with return code: {result.returncode}")
        return result.returncode

    except subprocess.TimeoutExpired:
        print("Tests timed out")
        return -1
    except Exception as e:
        print(f"Error running tests: {e}")
        return -1

if __name__ == "__main__":
    sys.exit(run_tests())