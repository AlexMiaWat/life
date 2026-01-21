"""
ComparisonAPI - REST API для системы сравнения жизней

Предоставляет HTTP интерфейс для:
- Управления инстансами Life
- Запуска и остановки сравнения
- Получения результатов анализа
- Мониторинга состояния системы
"""

import json
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from .comparison_manager import ComparisonManager, ComparisonConfig
from .pattern_analyzer import PatternAnalyzer
from .comparison_metrics import ComparisonMetrics
from src.logging_config import get_logger

logger = get_logger(__name__)


# Pydantic модели для запросов/ответов
class CreateInstanceRequest(BaseModel):
    instance_id: str = Field(..., description="Уникальный идентификатор инстанса")
    tick_interval: Optional[float] = Field(1.0, description="Интервал между тиками")
    snapshot_period: Optional[int] = Field(10, description="Период сохранения snapshots")
    dev_mode: Optional[bool] = Field(False, description="Режим разработки")
    enable_profiling: Optional[bool] = Field(False, description="Включить профилирование")


class ComparisonConfigRequest(BaseModel):
    max_instances: Optional[int] = Field(5, description="Максимальное количество инстансов")
    default_tick_interval: Optional[float] = Field(1.0, description="Интервал по умолчанию")
    default_snapshot_period: Optional[int] = Field(10, description="Период по умолчанию")
    data_collection_interval: Optional[float] = Field(5.0, description="Интервал сбора данных")


class StartComparisonRequest(BaseModel):
    instance_ids: List[str] = Field(..., description="Идентификаторы инстансов для сравнения")
    duration: Optional[float] = Field(None, description="Длительность сравнения в секундах")


class ComparisonAPI:
    """
    REST API для управления системой сравнения жизней.

    Предоставляет эндпоинты для:
    - Создания и управления инстансами Life
    - Управления процессом сравнения
    - Получения результатов анализа
    """

    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port

        # Инициализация компонентов
        self.comparison_manager = ComparisonManager()
        self.pattern_analyzer = PatternAnalyzer()
        self.comparison_metrics = ComparisonMetrics()

        # Состояние сравнения
        self.comparison_running = False
        self.comparison_results = {}
        self.comparison_thread = None

        # Создание FastAPI приложения
        self.app = FastAPI(
            title="Life Comparison API",
            description="API для сравнения разных инстансов Life",
            version="1.0.0",
        )

        self._setup_routes()

    def _setup_routes(self):
        """Настраивает маршруты API."""

        @self.app.get("/status")
        async def get_status():
            """Получить общий статус системы сравнения."""
            return {
                "comparison_running": self.comparison_running,
                "manager_stats": self.comparison_manager.get_comparison_stats(),
                "last_comparison_timestamp": (
                    self.comparison_results.get("timestamp") if self.comparison_results else None
                ),
            }

        @self.app.post("/instances")
        async def create_instance(request: CreateInstanceRequest):
            """Создать новый инстанс Life."""
            try:
                instance = self.comparison_manager.create_instance(
                    instance_id=request.instance_id,
                    tick_interval=request.tick_interval,
                    snapshot_period=request.snapshot_period,
                    dev_mode=request.dev_mode,
                    enable_profiling=request.enable_profiling,
                )

                if instance:
                    return {
                        "success": True,
                        "instance_id": request.instance_id,
                        "config": instance.config.__dict__,
                    }
                else:
                    raise HTTPException(status_code=400, detail="Failed to create instance")

            except Exception as e:
                logger.error(f"Error creating instance '{request.instance_id}': {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/instances")
        async def list_instances():
            """Получить список всех инстансов."""
            return self.comparison_manager.get_all_instances_status()

        @self.app.post("/instances/{instance_id}/start")
        async def start_instance(instance_id: str):
            """Запустить указанный инстанс."""
            if instance_id not in self.comparison_manager.instances:
                raise HTTPException(status_code=404, detail=f"Instance '{instance_id}' not found")

            success = self.comparison_manager.start_instance(instance_id)
            if success:
                return {"success": True, "message": f"Instance '{instance_id}' started"}
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to start instance '{instance_id}'"
                )

        @self.app.post("/instances/{instance_id}/stop")
        async def stop_instance(instance_id: str):
            """Остановить указанный инстанс."""
            if instance_id not in self.comparison_manager.instances:
                raise HTTPException(status_code=404, detail=f"Instance '{instance_id}' not found")

            success = self.comparison_manager.stop_instance(instance_id)
            if success:
                return {"success": True, "message": f"Instance '{instance_id}' stopped"}
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to stop instance '{instance_id}'"
                )

        @self.app.delete("/instances/{instance_id}")
        async def delete_instance(instance_id: str):
            """Удалить инстанс."""
            if instance_id not in self.comparison_manager.instances:
                raise HTTPException(status_code=404, detail=f"Instance '{instance_id}' not found")

            # Сначала останавливаем
            self.comparison_manager.stop_instance(instance_id)

            # Удаляем из менеджера
            with self.comparison_manager.lock:
                if instance_id in self.comparison_manager.instances:
                    del self.comparison_manager.instances[instance_id]

            return {"success": True, "message": f"Instance '{instance_id}' deleted"}

        @self.app.get("/instances/{instance_id}/status")
        async def get_instance_status(instance_id: str):
            """Получить статус указанного инстанса."""
            status = self.comparison_manager.get_instance_status(instance_id)
            if status is None:
                raise HTTPException(status_code=404, detail=f"Instance '{instance_id}' not found")

            return status

        @self.app.get("/instances/{instance_id}/snapshot")
        async def get_instance_snapshot(instance_id: str):
            """Получить последний snapshot инстанса."""
            instance = self.comparison_manager.instances.get(instance_id)
            if not instance:
                raise HTTPException(status_code=404, detail=f"Instance '{instance_id}' not found")

            snapshot = instance.get_latest_snapshot()
            if snapshot is None:
                raise HTTPException(
                    status_code=404, detail=f"No snapshot available for instance '{instance_id}'"
                )

            return snapshot

        @self.app.get("/instances/{instance_id}/logs")
        async def get_instance_logs(instance_id: str, limit: Optional[int] = None):
            """Получить логи инстанса."""
            instance = self.comparison_manager.instances.get(instance_id)
            if not instance:
                raise HTTPException(status_code=404, detail=f"Instance '{instance_id}' not found")

            logs = instance.get_structured_logs(limit=limit)
            return {"instance_id": instance_id, "logs": logs}

        @self.app.post("/comparison/start")
        async def start_comparison(
            request: StartComparisonRequest, background_tasks: BackgroundTasks
        ):
            """Начать сравнение указанных инстансов."""
            if self.comparison_running:
                raise HTTPException(status_code=400, detail="Comparison already running")

            # Проверяем, что все инстансы существуют
            missing_instances = []
            for instance_id in request.instance_ids:
                if instance_id not in self.comparison_manager.instances:
                    missing_instances.append(instance_id)

            if missing_instances:
                raise HTTPException(
                    status_code=400, detail=f"Instances not found: {missing_instances}"
                )

            # Запускаем сравнение в фоне
            background_tasks.add_task(self._run_comparison, request.instance_ids, request.duration)

            return {
                "success": True,
                "message": f"Comparison started for instances: {request.instance_ids}",
                "duration": request.duration,
            }

        @self.app.post("/comparison/stop")
        async def stop_comparison():
            """Остановить текущее сравнение."""
            if not self.comparison_running:
                raise HTTPException(status_code=400, detail="No comparison running")

            self.comparison_running = False
            self.comparison_manager.stop_data_collection()

            return {"success": True, "message": "Comparison stopped"}

        @self.app.get("/comparison/results")
        async def get_comparison_results():
            """Получить результаты последнего сравнения."""
            if not self.comparison_results:
                raise HTTPException(status_code=404, detail="No comparison results available")

            return self.comparison_results

        @self.app.get("/comparison/analysis")
        async def get_comparison_analysis():
            """Получить анализ паттернов сравнения."""
            if not self.comparison_results:
                raise HTTPException(status_code=404, detail="No comparison data available")

            # Анализируем данные
            analysis = self.pattern_analyzer.analyze_comparison_data(self.comparison_results)

            return analysis

        @self.app.get("/comparison/metrics")
        async def get_comparison_metrics():
            """Получить метрики сравнения."""
            if not self.comparison_results:
                raise HTTPException(status_code=404, detail="No comparison data available")

            # Вычисляем метрики
            instances_data = self.comparison_results.get("instances", {})
            metrics = self.comparison_metrics.get_summary_report(instances_data)

            return metrics

        @self.app.get("/")
        async def root():
            """Корневой эндпоинт с информацией о API."""
            return {
                "message": "Life Comparison API",
                "version": "1.0.0",
                "endpoints": {
                    "GET /": "This information",
                    "GET /dashboard": "Web dashboard for comparison visualization",
                    "GET /status": "General status",
                    "POST /instances": "Create new instance",
                    "GET /instances": "List all instances",
                    "POST /instances/{instance_id}/start": "Start instance",
                    "POST /instances/{instance_id}/stop": "Stop instance",
                    "GET /instances/{instance_id}/status": "Instance status",
                    "POST /comparison/start": "Start comparison",
                    "POST /comparison/stop": "Stop comparison",
                    "GET /comparison/results": "Comparison results",
                    "GET /comparison/analysis": "Pattern analysis",
                    "GET /comparison/metrics": "Comparison metrics",
                },
            }

        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard():
            """Веб-dashboard для визуализации сравнения."""
            html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Life Comparison Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .status {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 15px;
            background: #e8f4fd;
            border-radius: 5px;
        }
        .controls {
            margin: 20px 0;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .chart-container {
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .instances-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .instance-card {
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #fafafa;
        }
        .instance-card h3 {
            margin-top: 0;
            color: #333;
        }
        .metrics-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .metrics-table th, .metrics-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .metrics-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Life Comparison Dashboard</h1>

        <div class="status">
            <div id="system-status">
                <h3>System Status</h3>
                <p id="status-text">Loading...</p>
            </div>
            <div id="comparison-status">
                <h3>Comparison Status</h3>
                <p id="comparison-text">No active comparison</p>
            </div>
        </div>

        <div class="controls">
            <h3>Controls</h3>
            <button class="btn-primary" onclick="createInstances()">Create Test Instances</button>
            <button class="btn-success" onclick="startAllInstances()">Start All Instances</button>
            <button class="btn-danger" onclick="stopAllInstances()">Stop All Instances</button>
            <button class="btn-secondary" onclick="startComparison()">Start Comparison (30s)</button>
            <button class="btn-secondary" onclick="stopComparison()">Stop Comparison</button>
            <button class="btn-primary" onclick="refreshData()">Refresh Data</button>
        </div>

        <div id="instances-container">
            <h3>Life Instances</h3>
            <div id="instances-list" class="loading">Loading instances...</div>
        </div>

        <div class="chart-container">
            <h3>Comparison Results</h3>
            <canvas id="comparisonChart" width="400" height="200"></canvas>
        </div>

        <div class="chart-container">
            <h3>Pattern Analysis</h3>
            <canvas id="patternChart" width="400" height="200"></canvas>
        </div>

        <div class="chart-container">
            <h3>Detailed Metrics</h3>
            <div id="metrics-table"></div>
        </div>
    </div>

    <script>
        let statusChart = null;
        let patternChart = null;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            setInterval(refreshData, 5000); // Auto-refresh every 5 seconds
        });

        async function apiCall(endpoint, options = {}) {
            try {
                const response = await fetch(endpoint, options);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('API call failed:', error);
                return null;
            }
        }

        async function refreshData() {
            // Update system status
            const status = await apiCall('/status');
            if (status) {
                document.getElementById('status-text').innerHTML =
                    `Active instances: ${status.active_instances || 0}<br>` +
                    `Total instances: ${status.total_instances || 0}<br>` +
                    `Collecting: ${status.is_collecting ? 'Yes' : 'No'}`;
            }

            // Update comparison status
            const comparisonStatus = status && status.comparison_running ?
                'Comparison running...' : 'No active comparison';
            document.getElementById('comparison-text').textContent = comparisonStatus;

            // Update instances list
            updateInstancesList();

            // Update charts if comparison data available
            updateCharts();
        }

        async function updateInstancesList() {
            const instances = await apiCall('/instances');
            const container = document.getElementById('instances-list');

            if (!instances) {
                container.innerHTML = '<p class="loading">Failed to load instances</p>';
                return;
            }

            if (Object.keys(instances).length === 0) {
                container.innerHTML = '<p>No instances created yet</p>';
                return;
            }

            const html = Object.entries(instances).map(([id, data]) => `
                <div class="instance-card">
                    <h3>${id}</h3>
                    <p><strong>Status:</strong> ${data.is_running ? 'Running' : 'Stopped'}</p>
                    <p><strong>Alive:</strong> ${data.is_alive ? 'Yes' : 'No'}</p>
                    <p><strong>Uptime:</strong> ${data.uptime ? data.uptime.toFixed(1) + 's' : 'N/A'}</p>
                    <p><strong>Port:</strong> ${data.port || 'N/A'}</p>
                    <button class="btn-success" onclick="startInstance('${id}')">Start</button>
                    <button class="btn-danger" onclick="stopInstance('${id}')">Stop</button>
                </div>
            `).join('');

            container.innerHTML = `<div class="instances-grid">${html}</div>`;
        }

        async function updateCharts() {
            const results = await apiCall('/comparison/results');
            const analysis = await apiCall('/comparison/analysis');
            const metrics = await apiCall('/comparison/metrics');

            if (results && Object.keys(results.instances || {}).length > 0) {
                updateComparisonChart(results);
            }

            if (analysis) {
                updatePatternChart(analysis);
            }

            if (metrics) {
                updateMetricsTable(metrics);
            }
        }

        function updateComparisonChart(results) {
            const ctx = document.getElementById('comparisonChart').getContext('2d');
            const instances = results.instances || {};

            const labels = Object.keys(instances);
            const energyData = labels.map(id => instances[id].snapshot?.energy || 0);
            const stabilityData = labels.map(id => instances[id].snapshot?.stability || 0);
            const integrityData = labels.map(id => instances[id].snapshot?.integrity || 0);

            if (statusChart) {
                statusChart.destroy();
            }

            statusChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Energy',
                            data: energyData,
                            backgroundColor: 'rgba(255, 99, 132, 0.5)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Stability',
                            data: stabilityData,
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Integrity',
                            data: integrityData,
                            backgroundColor: 'rgba(75, 192, 192, 0.5)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Current State Comparison'
                        }
                    }
                }
            });
        }

        function updatePatternChart(analysis) {
            const ctx = document.getElementById('patternChart').getContext('2d');
            const instances = analysis.instances_analysis || {};

            const labels = Object.keys(instances);
            const datasets = [];

            // Collect all unique patterns
            const allPatterns = new Set();
            labels.forEach(id => {
                const patterns = instances[id].decision_patterns?.patterns || {};
                Object.keys(patterns).forEach(p => allPatterns.add(p));
            });

            // Create datasets for each pattern
            Array.from(allPatterns).forEach(pattern => {
                datasets.push({
                    label: pattern,
                    data: labels.map(id => {
                        const patterns = instances[id].decision_patterns?.patterns || {};
                        return patterns[pattern] || 0;
                    }),
                    backgroundColor: `hsl(${Math.random() * 360}, 70%, 50%)`,
                    borderWidth: 1
                });
            });

            if (patternChart) {
                patternChart.destroy();
            }

            patternChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Decision Pattern Analysis'
                        }
                    }
                }
            });
        }

        function updateMetricsTable(metrics) {
            const container = document.getElementById('metrics-table');

            let html = '<table class="metrics-table">';
            html += '<tr><th>Metric</th><th>Value</th></tr>';

            // Similarity metrics
            const similarity = metrics.similarity_metrics?.overall_similarity || {};
            Object.entries(similarity).forEach(([pair, value]) => {
                html += `<tr><td>Similarity ${pair}</td><td>${value.toFixed(3)}</td></tr>`;
            });

            // Performance metrics
            const performance = metrics.performance_metrics || {};
            Object.entries(performance.survival_rates || {}).forEach(([id, data]) => {
                html += `<tr><td>${id} Survival Rate</td><td>${data.is_alive ? 'Alive' : 'Dead'}</td></tr>`;
                html += `<tr><td>${id} Uptime</td><td>${data.uptime?.toFixed(1) || 0}s</td></tr>`;
            });

            // Diversity metrics
            const diversity = metrics.diversity_metrics || {};
            html += `<tr><td>Pattern Diversity</td><td>${diversity.pattern_diversity || 0}</td></tr>`;
            html += `<tr><td>Diversity Score</td><td>${diversity.diversity_score?.toFixed(3) || 0}</td></tr>`;

            html += '</table>';
            container.innerHTML = html;
        }

        // Control functions
        async function createInstances() {
            alert('Creating test instances...');
            for (let i = 1; i <= 2; i++) {
                await apiCall('/instances', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        instance_id: `life_${i}`,
                        tick_interval: 1.0,
                        snapshot_period: 5
                    })
                });
            }
            refreshData();
        }

        async function startAllInstances() {
            const instances = await apiCall('/instances');
            if (instances) {
                for (const id of Object.keys(instances)) {
                    await apiCall(`/instances/${id}/start`, {method: 'POST'});
                }
            }
            refreshData();
        }

        async function stopAllInstances() {
            const instances = await apiCall('/instances');
            if (instances) {
                for (const id of Object.keys(instances)) {
                    await apiCall(`/instances/${id}/stop`, {method: 'POST'});
                }
            }
            refreshData();
        }

        async function startInstance(id) {
            await apiCall(`/instances/${id}/start`, {method: 'POST'});
            refreshData();
        }

        async function stopInstance(id) {
            await apiCall(`/instances/${id}/stop`, {method: 'POST'});
            refreshData();
        }

        async function startComparison() {
            const instances = await apiCall('/instances');
            if (instances && Object.keys(instances).length > 0) {
                await apiCall('/comparison/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        instance_ids: Object.keys(instances),
                        duration: 30
                    })
                });
            }
            refreshData();
        }

        async function stopComparison() {
            await apiCall('/comparison/stop', {method: 'POST'});
            refreshData();
        }
    </script>
</body>
</html>
            """
            return HTMLResponse(content=html_content)

        @self.app.post("/config")
        async def update_config(config: ComparisonConfigRequest):
            """Обновить конфигурацию системы сравнения."""
            try:
                new_config = ComparisonConfig(
                    max_instances=config.max_instances
                    or self.comparison_manager.config.max_instances,
                    default_tick_interval=config.default_tick_interval
                    or self.comparison_manager.config.default_tick_interval,
                    default_snapshot_period=config.default_snapshot_period
                    or self.comparison_manager.config.default_snapshot_period,
                    data_collection_interval=config.data_collection_interval
                    or self.comparison_manager.config.data_collection_interval,
                )

                self.comparison_manager.config = new_config

                return {
                    "success": True,
                    "config": {
                        "max_instances": new_config.max_instances,
                        "default_tick_interval": new_config.default_tick_interval,
                        "default_snapshot_period": new_config.default_snapshot_period,
                        "data_collection_interval": new_config.data_collection_interval,
                    },
                }

            except Exception as e:
                logger.error(f"Error updating config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _run_comparison(self, instance_ids: List[str], duration: Optional[float]):
        """Запускает процесс сравнения в фоне."""
        import time
        import threading

        logger.info(f"Starting comparison for instances: {instance_ids}")

        self.comparison_running = True
        start_time = time.time()

        try:
            # Запускаем сбор данных
            def data_callback(data):
                self.comparison_results = data
                logger.debug(
                    f"Comparison data collected: {len(data.get('instances', {}))} instances"
                )

            self.comparison_manager.start_data_collection(callback=data_callback)

            # Ждем указанное время или пока не остановят
            while self.comparison_running:
                if duration and (time.time() - start_time) >= duration:
                    break
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error during comparison: {e}")

        finally:
            # Останавливаем сбор данных
            self.comparison_manager.stop_data_collection()
            self.comparison_running = False

            logger.info(f"Comparison finished for instances: {instance_ids}")

    def start_server(self):
        """Запустить API сервер."""
        logger.info(f"Starting Comparison API server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")

    def run_in_background(self):
        """Запустить сервер в отдельном потоке."""
        import threading

        thread = threading.Thread(target=self.start_server, daemon=True, name="comparison-api")
        thread.start()

        logger.info(f"Comparison API started in background on {self.host}:{self.port}")
        return thread


# Функция для запуска API сервера из командной строки
def run_comparison_api(host: str = "localhost", port: int = 8001):
    """Запустить API сервер системы сравнения."""
    api = ComparisonAPI(host=host, port=port)
    api.start_server()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Life Comparison API Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")

    args = parser.parse_args()
    run_comparison_api(host=args.host, port=args.port)
