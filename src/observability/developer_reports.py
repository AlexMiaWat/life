"""
Developer Reports for Life System Observability.

Simplified automated report generation for system monitoring.
Generates daily health reports and basic text reports.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class DeveloperReports:
    """
    Simplified developer reports generator.

    Generates automated daily reports and basic health checks.
    """

    def __init__(self, data_directory: str = "data"):
        """
        Initialize developer reports.

        Args:
            data_directory: Directory containing observation data
        """
        self.data_dir = Path(data_directory)
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_automated_report(self, report_type: str = "daily", hours: int = 24) -> Dict[str, Any]:
        """
        Generate automated report based on type.

        Args:
            report_type: Type of report ("daily", "health")
            hours: Hours to analyze for the report

        Returns:
            Automated report data
        """
        if report_type == "daily":
            return self._generate_daily_report(hours)
        elif report_type == "health":
            return self.generate_system_health_check()
        else:
            raise ValueError(f"Unknown report type: {report_type}. Use 'daily' or 'health'")

    def _generate_daily_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate simple daily report."""
        report = {
            "report_type": "daily_report",
            "generated_at": time.time(),
            "analysis_period_hours": hours,
            "timestamp": datetime.now().isoformat(),
        }

        # System health
        health = self.generate_system_health_check()
        report["health"] = health

        # Basic metrics summary
        metrics = self._get_basic_metrics(hours)
        report["metrics"] = metrics

        # Simple insights
        report["insights"] = self._generate_simple_insights(health, metrics)

        return report

    def generate_system_health_check(self) -> Dict[str, Any]:
        """
        Generate system health check report.

        Returns:
            Health check report
        """
        # Check latest snapshot
        latest_snapshot = self._find_latest_snapshot()

        report = {
            "report_type": "health_check",
            "generated_at": time.time(),
            "snapshot_found": latest_snapshot is not None
        }

        if latest_snapshot:
            report["snapshot_analysis"] = self._analyze_snapshot_health(latest_snapshot)
        else:
            report["issues"] = ["No recent snapshots found"]

        # Check data collection status
        data_file = self.data_dir / "passive_observations.jsonl"
        if data_file.exists():
            # Check file age
            file_age_hours = (time.time() - data_file.stat().st_mtime) / 3600
            report["data_collection"] = {
                "file_exists": True,
                "file_age_hours": file_age_hours,
                "is_recent": file_age_hours < 1.0  # Less than 1 hour old
            }
        else:
            report["data_collection"] = {
                "file_exists": False,
                "issues": ["No observation data file found"]
            }

        return report

    def generate_text_report(self, hours: int = 24) -> str:
        """
        Generate a comprehensive text-based report with visualizations.

        Args:
            hours: Hours to analyze

        Returns:
            Formatted text report with ASCII charts
        """
        data = self._load_observation_data(hours)

        if not data:
            return f"No observation data available for the last {hours} hours."

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("SYSTEM OBSERVABILITY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Analysis Period: Last {hours} hours")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Data points: {len(data)}")
        report_lines.append("")

        # System Health Overview
        report_lines.append("SYSTEM HEALTH OVERVIEW:")
        report_lines.append("-" * 40)

        energies = [r.get('system_state', {}).get('energy', 0) for r in data]
        stabilities = [r.get('system_state', {}).get('stability', 0) for r in data]
        integrities = [r.get('system_state', {}).get('integrity', 0) for r in data]

        if energies:
            avg_energy = statistics.mean(energies)
            min_energy = min(energies)
            max_energy = max(energies)
            report_lines.append(f"Energy:     {avg_energy:.2f} (min: {min_energy:.2f}, max: {max_energy:.2f})")

        if stabilities:
            avg_stability = statistics.mean(stabilities)
            min_stability = min(stabilities)
            max_stability = max(stabilities)
            report_lines.append(f"Stability:  {avg_stability:.2f} (min: {min_stability:.2f}, max: {max_stability:.2f})")

        if integrities:
            avg_integrity = statistics.mean(integrities)
            min_integrity = min(integrities)
            max_integrity = max(integrities)
            report_lines.append(f"Integrity:  {avg_integrity:.2f} (min: {min_integrity:.2f}, max: {max_integrity:.2f})")

        # Memory Usage
        memory_sizes = [r.get('memory', {}).get('episodic_size', 0) +
                       r.get('memory', {}).get('archive_size', 0) for r in data]
        if memory_sizes:
            avg_memory = statistics.mean(memory_sizes)
            max_memory = max(memory_sizes)
            report_lines.append(f"Memory:     {avg_memory:.0f} entries (peak: {max_memory:.0f})")

        report_lines.append("")

        # Trend Analysis
        report_lines.append("TREND ANALYSIS:")
        report_lines.append("-" * 40)

        # Energy trend
        if len(energies) > 5:
            energy_trend = self._analyze_trend(energies)
            report_lines.append(f"Energy Trend:    {energy_trend}")

        # Stability trend
        if len(stabilities) > 5:
            stability_trend = self._analyze_trend(stabilities)
            report_lines.append(f"Stability Trend: {stability_trend}")

        report_lines.append("")

        # ASCII Charts
        report_lines.append("ENERGY LEVELS OVER TIME:")
        report_lines.append("-" * 40)
        if energies:
            report_lines.extend(self._create_ascii_chart("Energy", energies, width=60))

        report_lines.append("")
        report_lines.append("STABILITY OVER TIME:")
        report_lines.append("-" * 40)
        if stabilities:
            report_lines.extend(self._create_ascii_chart("Stability", stabilities, width=60))

        # Health Assessment
        report_lines.append("")
        report_lines.append("HEALTH ASSESSMENT:")
        report_lines.append("-" * 40)

        health_score = self._calculate_health_score(data)
        report_lines.append(f"Overall Health Score: {health_score:.1f}/10")

        if health_score >= 8:
            report_lines.append("Status: EXCELLENT - System performing optimally")
        elif health_score >= 6:
            report_lines.append("Status: GOOD - Minor issues, monitoring recommended")
        elif health_score >= 4:
            report_lines.append("Status: FAIR - Some concerns, review recommended")
        else:
            report_lines.append("Status: POOR - Immediate attention required")

        return "\n".join(report_lines)

    def _load_observation_data(self, hours: int) -> List[Dict[str, Any]]:
        """Load observation data from passive observations file."""
        cutoff_time = time.time() - (hours * 3600)
        data_file = self.data_dir / "passive_observations.jsonl"

        if not data_file.exists():
            return []

        data = []
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if record.get('timestamp', 0) >= cutoff_time:
                            data.append(record)
        except Exception as e:
            logger.warning(f"Failed to load observation data: {e}")

        return data

    def _get_basic_metrics(self, hours: int) -> Dict[str, Any]:
        """Get basic metrics summary."""
        data = self._load_observation_data(hours)

        if not data:
            return {"error": "No data available"}

        metrics = {
            "data_points": len(data),
            "time_range_hours": hours
        }

        # Energy stats
        energies = [r.get('system_state', {}).get('energy', 0) for r in data]
        if energies:
            metrics["energy"] = {
                "mean": statistics.mean(energies),
                "min": min(energies),
                "max": max(energies)
            }

        # Stability stats
        stabilities = [r.get('system_state', {}).get('stability', 0) for r in data]
        if stabilities:
            metrics["stability"] = {
                "mean": statistics.mean(stabilities),
                "min": min(stabilities),
                "max": max(stabilities)
            }

        # Memory stats
        memory_sizes = [r.get('memory', {}).get('episodic_size', 0) +
                       r.get('memory', {}).get('archive_size', 0) for r in data]
        if memory_sizes:
            metrics["memory"] = {
                "mean": statistics.mean(memory_sizes),
                "max": max(memory_sizes)
            }

        return metrics

    def _generate_simple_insights(self, health: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Generate simple insights based on health and metrics."""
        insights = []

        # Health insights
        if health.get("snapshot_found"):
            insights.append("System snapshot is available")
        else:
            insights.append("No recent snapshots found - system may not be running")

        data_collection = health.get("data_collection", {})
        if data_collection.get("is_recent"):
            insights.append("Data collection is active and recent")
        elif data_collection.get("file_exists"):
            age = data_collection.get("file_age_hours", 0)
            insights.append(f"Data collection is stale ({age:.1f} hours old)")

        # Metrics insights
        energy = metrics.get("energy", {})
        if energy and energy.get("mean", 0) < 0.5:
            insights.append("System energy levels are below optimal")

        stability = metrics.get("stability", {})
        if stability and stability.get("mean", 0) < 0.5:
            insights.append("System stability is below optimal")

        return insights

    def _find_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Find the latest snapshot file."""
        snapshots_dir = self.data_dir / "snapshots"
        if not snapshots_dir.exists():
            return None

        try:
            snapshot_files = list(snapshots_dir.glob("*.json"))
            if not snapshot_files:
                return None

            # Find most recent by modification time
            latest_file = max(snapshot_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.warning(f"Failed to load latest snapshot: {e}")
            return None

    def _analyze_snapshot_health(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze snapshot for health indicators."""
        health = {
            "has_timestamp": "timestamp" in snapshot,
            "has_vitals": all(k in snapshot for k in ["energy", "stability", "integrity"]),
            "vital_ranges": {},
            "issues": []
        }

        # Check vital parameter ranges
        vitals = ["energy", "stability", "integrity", "fatigue", "tension"]
        for vital in vitals:
            if vital in snapshot:
                value = snapshot[vital]
                health["vital_ranges"][vital] = value

                # Check for concerning values
                if vital in ["energy", "stability", "integrity"] and value < 0.1:
                    health["issues"].append(f"Very low {vital}: {value}")
                elif vital == "fatigue" and value > 0.9:
                    health["issues"].append(f"High fatigue: {value}")

        return health

    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze trend direction from value series."""
        if len(values) < 5:
            return "insufficient_data"

        # Split into first and second half
        mid = len(values) // 2
        first_half = values[:mid]
        second_half = values[mid:]

        first_avg = statistics.mean(first_half) if first_half else 0
        second_avg = statistics.mean(second_half) if second_half else 0

        diff = second_avg - first_avg
        threshold = abs(first_avg) * 0.05 if first_avg != 0 else 0.01  # 5% change threshold

        if diff > threshold:
            return "INCREASING ↑"
        elif diff < -threshold:
            return "DECREASING ↓"
        else:
            return "STABLE →"

    def _create_ascii_chart(self, label: str, values: List[float], width: int = 60) -> List[str]:
        """Create ASCII chart for values."""
        if not values:
            return [f"{label}: No data"]

        lines = []
        min_val = min(values)
        max_val = max(values)
        avg_val = statistics.mean(values)

        lines.append(f"{label}: {avg_val:.2f} (range: {min_val:.2f} - {max_val:.2f})")

        if max_val > min_val:
            # Create histogram
            bins = [0] * 20
            for val in values:
                if max_val > min_val:
                    bin_idx = int((val - min_val) / (max_val - min_val) * 19)
                    bin_idx = min(bin_idx, 19)
                    bins[bin_idx] += 1

            max_count = max(bins) if bins else 1

            # Draw chart
            for i in range(10, -1, -1):  # From top to bottom
                line = "2.2f"
                if i == 5:  # Middle line for average
                    line += " ┼───" + "─" * 50
                else:
                    line += " │" + "".join("█" if count >= max_count * (i+1) / 11 else " " for count in bins)
                lines.append(line)

            # X-axis labels
            lines.append("0.00" + " " * 55 + f"{max_val:.2f}")
        else:
            lines.append("All values constant: " + "█" * 30)

        return lines

    def _calculate_health_score(self, data: List[Dict[str, Any]]) -> float:
        """Calculate overall health score (0-10)."""
        if not data:
            return 0.0

        score = 0.0
        factors = 0

        # Energy factor (40% weight)
        energies = [r.get('system_state', {}).get('energy', 0) for r in data]
        if energies:
            avg_energy = statistics.mean(energies)
            energy_score = min(10, max(0, avg_energy * 10))  # Scale 0-1 to 0-10
            score += energy_score * 0.4
            factors += 0.4

        # Stability factor (30% weight)
        stabilities = [r.get('system_state', {}).get('stability', 0) for r in data]
        if stabilities:
            avg_stability = statistics.mean(stabilities)
            stability_score = min(10, max(0, avg_stability * 10))
            score += stability_score * 0.3
            factors += 0.3

        # Integrity factor (20% weight)
        integrities = [r.get('system_state', {}).get('integrity', 0) for r in data]
        if integrities:
            avg_integrity = statistics.mean(integrities)
            integrity_score = min(10, max(0, avg_integrity * 10))
            score += integrity_score * 0.2
            factors += 0.2

        # Data freshness factor (10% weight)
        if data:
            latest_timestamp = max(r.get('timestamp', 0) for r in data)
            hours_old = (time.time() - latest_timestamp) / 3600
            freshness_score = max(0, 10 - hours_old)  # Deduct 1 point per hour
            score += freshness_score * 0.1
            factors += 0.1

        return score if factors > 0 else 0.0

    def save_report(self, report: Dict[str, Any], filename: str) -> Path:
        """
        Save report to file.

        Args:
            report: Report dictionary
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.reports_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved to {output_path}")
        return output_path