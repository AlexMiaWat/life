"""
Raw Data Access for Life System Observability.

Provides access to raw observation data without interpretation or derived metrics.
Only raw counters and basic data access functionality.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RawDataAccess:
    """
    Raw data access for Life system observability.

    Provides access to raw observation data without any interpretation,
    analysis, or derived metrics. Only raw counters and basic data loading.
    """

    def __init__(self, data_directory: str = "data"):
        """
        Initialize raw data access.

        Args:
            data_directory: Directory containing observation data
        """
        self.data_dir = Path(data_directory)

    def get_raw_observation_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get raw observation data without interpretation.

        Args:
            hours: Hours to look back for data

        Returns:
            List of raw observation records
        """
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

    def get_raw_snapshot_data(self) -> Optional[Dict[str, Any]]:
        """
        Get raw snapshot data without analysis.

        Returns:
            Latest snapshot data or None if not available
        """
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

    def get_data_collection_status(self) -> Dict[str, Any]:
        """
        Get basic data collection status without interpretation.

        Returns:
            Status information about data collection
        """
        data_file = self.data_dir / "passive_observations.jsonl"

        status = {
            "generated_at": time.time(),
            "observation_file_exists": data_file.exists()
        }

        if data_file.exists():
            try:
                file_age_seconds = time.time() - data_file.stat().st_mtime
                status["observation_file_age_seconds"] = file_age_seconds
                status["observation_file_size_bytes"] = data_file.stat().st_size
            except Exception as e:
                logger.warning(f"Failed to get file stats: {e}")
                status["file_stats_error"] = str(e)

        return status

    def export_raw_data(self, hours: int = 24, output_path: Optional[Path] = None) -> Path:
        """
        Export raw observation data to JSON file.

        Args:
            hours: Hours of data to export
            output_path: Output file path (auto-generated if None)

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"raw_export_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.get_raw_observation_data(hours)
        snapshot = self.get_raw_snapshot_data()
        status = self.get_data_collection_status()

        export_data = {
            "export_timestamp": time.time(),
            "export_period_hours": hours,
            "observation_records": data,
            "latest_snapshot": snapshot,
            "data_collection_status": status
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Raw data exported to {output_path}")
        return output_path


# Backward compatibility alias
DeveloperReports = RawDataAccess