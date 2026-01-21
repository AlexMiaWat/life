#!/usr/bin/env python3
"""
Developer Reports Generator for Life System.

Generates useful monitoring reports from observability data.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from observability.developer_reports import DeveloperReports


def main():
    """Main function for generating developer reports."""
    print("🔍 Generating Developer Reports for Life System")
    print("=" * 50)

    reports = DeveloperReports()

    # Generate health check
    print("📊 Generating system health check...")
    health_report = reports.generate_system_health_check()
    reports.save_report(health_report, "health_check_report.json")

    print("✅ Health check report saved")

    # Generate performance report
    print("⚡ Generating performance report (24h)...")
    perf_report = reports.generate_performance_report(hours=24)
    reports.save_report(perf_report, "performance_report_24h.json")

    print("✅ Performance report saved")

    # Generate behavior summary
    print("🧠 Generating behavior summary (24h)...")
    behavior_report = reports.generate_behavior_summary(hours=24)
    reports.save_report(behavior_report, "behavior_summary_24h.json")

    print("✅ Behavior summary saved")

    # Print summary
    print("\n📋 Report Summary:")
    print(f"  - Health Check: {health_report.get('snapshot_found', False)}")
    print(f"  - State Observations: {perf_report.get('data_points', {}).get('state_snapshots', 0)}")
    print(f"  - Component Stats: {perf_report.get('data_points', {}).get('component_stats', 0)}")

    print("\n✨ Reports generated successfully!")
    print("📁 Check data/reports/ directory for output files")


if __name__ == "__main__":
    main()