"""
Predictive Analysis for Life system semantic monitoring.

Provides predictive modeling and forecasting capabilities for system behavior,
anomaly prediction, and proactive recommendations.
"""

import json
import logging
import statistics
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import time
import math

logger = logging.getLogger(__name__)


@dataclass
class PredictionModel:
    """Predictive model for system behavior."""
    model_id: str
    target_metric: str
    model_type: str  # 'linear_trend', 'seasonal', 'pattern_based'
    parameters: Dict[str, Any]
    accuracy_history: List[float] = field(default_factory=list)
    last_trained: float = 0.0
    confidence: float = 0.0


@dataclass
class BehaviorPrediction:
    """Prediction of future system behavior."""
    prediction_id: str
    target_metric: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_horizon: int  # Number of intervals ahead
    timestamp: float
    model_used: str
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskPrediction:
    """Prediction of system risks."""
    risk_type: str
    probability: float
    severity: str
    timeframe: str
    indicators: List[str]
    mitigation_actions: List[str]
    timestamp: float


class PredictiveAnalysisEngine:
    """
    Engine for predictive analysis of Life system behavior.

    Uses historical semantic data to predict future system states,
    identify risk patterns, and provide proactive recommendations.
    """

    def __init__(self, history_window: int = 1000, prediction_horizon: int = 10):
        """
        Initialize predictive analysis engine.

        Args:
            history_window: Number of historical data points to maintain
            prediction_horizon: Default prediction horizon (intervals)
        """
        self.history_window = history_window
        self.prediction_horizon = prediction_horizon

        # Historical data storage
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_window))
        self.event_sequences: deque = deque(maxlen=history_window)
        self.state_transitions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Prediction models
        self.prediction_models: Dict[str, PredictionModel] = {}

        # Predictions and risks
        self.active_predictions: List[BehaviorPrediction] = []
        self.risk_predictions: List[RiskPrediction] = []

        # Model training intervals
        self.last_model_training = time.time()
        self.model_training_interval = 300  # Retrain every 5 minutes

        logger.info("PredictiveAnalysisEngine initialized")

    def update_historical_data(self, semantic_data: Dict[str, Any]):
        """
        Update historical data with new semantic analysis results.

        Args:
            semantic_data: Results from semantic analysis
        """
        timestamp = semantic_data.get('timestamp', time.time())

        # Update metric histories
        if 'anomaly_score' in semantic_data:
            self.metric_history['anomaly_score'].append(semantic_data['anomaly_score'])

        if 'behavioral_context' in semantic_data:
            context = semantic_data['behavioral_context']
            self.metric_history['processing_completeness'].append(
                context.get('processing_completeness', 0.0)
            )
            self.metric_history['response_efficiency'].append(
                context.get('response_efficiency', 0.0)
            )

        if 'impact_profile' in semantic_data:
            for param, value in semantic_data['impact_profile'].items():
                self.metric_history[f'impact_{param}'].append(value)

        # Update event sequences
        event_types = semantic_data.get('event_types', [])
        if event_types:
            self.event_sequences.append({
                'timestamp': timestamp,
                'event_types': event_types,
                'decision_patterns': semantic_data.get('decision_patterns', []),
                'anomaly_score': semantic_data.get('anomaly_score', 0.0)
            })

        # Update state transitions
        if len(event_types) >= 2:
            for i in range(len(event_types) - 1):
                current_state = event_types[i]
                next_state = event_types[i + 1]
                self.state_transitions[current_state][next_state] += 1

        # Retrain models periodically
        if time.time() - self.last_model_training > self.model_training_interval:
            self._train_prediction_models()
            self.last_model_training = time.time()

    def predict_system_behavior(self, target_metrics: List[str] = None,
                              horizon: int = None) -> Dict[str, Any]:
        """
        Predict future system behavior for specified metrics.

        Args:
            target_metrics: List of metrics to predict (if None, predict all available)
            horizon: Prediction horizon (if None, use default)

        Returns:
            Dictionary with behavior predictions
        """
        if target_metrics is None:
            target_metrics = list(self.metric_history.keys())

        if horizon is None:
            horizon = self.prediction_horizon

        predictions = {}

        for metric in target_metrics:
            if metric in self.prediction_models and metric in self.metric_history:
                model = self.prediction_models[metric]
                history = list(self.metric_history[metric])

                if len(history) >= 3:
                    prediction = self._generate_prediction(model, history, horizon)
                    if prediction:
                        predictions[metric] = prediction

        return {
            'predictions': predictions,
            'prediction_horizon': horizon,
            'timestamp': time.time(),
            'models_used': len(predictions)
        }

    def predict_anomaly_risks(self, risk_threshold: float = 0.7) -> List[RiskPrediction]:
        """
        Predict potential anomaly risks based on current trends.

        Args:
            risk_threshold: Threshold for considering a risk significant

        Returns:
            List of predicted risks
        """
        risks = []

        # Analyze anomaly score trends
        if 'anomaly_score' in self.metric_history:
            anomaly_history = list(self.metric_history['anomaly_score'])
            if len(anomaly_history) >= 5:
                # Check for increasing trend
                recent_avg = sum(anomaly_history[-5:]) / 5
                overall_avg = sum(anomaly_history) / len(anomaly_history)

                if recent_avg > overall_avg * 1.5 and recent_avg > risk_threshold:
                    risk = RiskPrediction(
                        risk_type='anomaly_spike',
                        probability=min(0.9, recent_avg),
                        severity='high' if recent_avg > 0.8 else 'medium',
                        timeframe='next_few_intervals',
                        indicators=['increasing_anomaly_scores', 'above_average_recent_activity'],
                        mitigation_actions=[
                            'Увеличить мониторинг',
                            'Подготовить дополнительные ресурсы',
                            'Проверить конфигурацию системы'
                        ],
                        timestamp=time.time()
                    )
                    risks.append(risk)

        # Analyze processing efficiency trends
        if 'processing_completeness' in self.metric_history:
            completeness_history = list(self.metric_history['processing_completeness'])
            if len(completeness_history) >= 5:
                recent_avg = sum(completeness_history[-5:]) / 5

                if recent_avg < 0.7:
                    risk = RiskPrediction(
                        risk_type='processing_degradation',
                        probability=1.0 - recent_avg,
                        severity='medium',
                        timeframe='immediate',
                        indicators=['low_processing_completeness', 'potential_system_strain'],
                        mitigation_actions=[
                            'Оптимизировать обработку событий',
                            'Проверить ресурсы системы',
                            'Рассмотреть упрощение алгоритмов'
                        ],
                        timestamp=time.time()
                    )
                    risks.append(risk)

        # Analyze state impact volatility
        volatile_impacts = []
        for metric_name, history in self.metric_history.items():
            if metric_name.startswith('impact_') and len(history) >= 5:
                values = list(history)
                if len(values) >= 2:
                    volatility = self._calculate_volatility(values)
                    if volatility > 0.8:
                        volatile_impacts.append(metric_name.replace('impact_', ''))

        if volatile_impacts:
            risk = RiskPrediction(
                risk_type='state_instability',
                probability=min(0.8, len(volatile_impacts) / 3.0),
                severity='medium',
                timeframe='ongoing',
                indicators=[f'high_volatility_in_{impact}' for impact in volatile_impacts],
                mitigation_actions=[
                    'Стабилизировать параметры состояния',
                    'Проверить адаптационные алгоритмы',
                    'Уменьшить интенсивность внешних воздействий'
                ],
                timestamp=time.time()
            )
            risks.append(risk)

        # Update risk predictions
        self.risk_predictions = risks

        return risks

    def forecast_event_patterns(self, forecast_steps: int = 5) -> Dict[str, Any]:
        """
        Forecast likely event patterns based on historical sequences.

        Args:
            forecast_steps: Number of steps to forecast

        Returns:
            Event pattern forecasts
        """
        if len(self.event_sequences) < 10:
            return {'forecast': 'insufficient_data'}

        # Analyze recent patterns
        recent_sequences = list(self.event_sequences)[-20:]  # Last 20 sequences

        # Simple Markov chain approach for event prediction
        transition_probabilities = self._calculate_transition_probabilities()

        # Start from most recent state
        if recent_sequences:
            current_state = recent_sequences[-1]['event_types'][-1] if recent_sequences[-1]['event_types'] else 'unknown'
        else:
            current_state = 'unknown'

        forecast = [current_state]
        probabilities = [1.0]

        # Generate forecast
        for step in range(forecast_steps):
            next_states = transition_probabilities.get(current_state, {})
            if next_states:
                # Choose most probable next state
                next_state = max(next_states.items(), key=lambda x: x[1])[0]
                probability = next_states[next_state]

                forecast.append(next_state)
                probabilities.append(probability)
                current_state = next_state
            else:
                break

        return {
            'forecast_sequence': forecast,
            'probabilities': probabilities,
            'confidence': statistics.mean(probabilities) if probabilities else 0.0,
            'steps_forecasted': len(forecast) - 1,
            'timestamp': time.time()
        }

    def _train_prediction_models(self):
        """Train or update prediction models for available metrics."""
        for metric_name, history in self.metric_history.items():
            if len(history) < 10:
                continue

            history_list = list(history)

            # Simple linear trend model
            if len(history_list) >= 3:
                model = PredictionModel(
                    model_id=f"{metric_name}_linear",
                    target_metric=metric_name,
                    model_type='linear_trend',
                    parameters=self._fit_linear_model(history_list),
                    last_trained=time.time()
                )

                # Calculate model accuracy on historical data
                accuracy = self._evaluate_model_accuracy(model, history_list)
                model.accuracy_history.append(accuracy)
                model.confidence = min(1.0, accuracy / 0.8)  # Normalize accuracy to confidence

                self.prediction_models[metric_name] = model

    def _fit_linear_model(self, values: List[float]) -> Dict[str, Any]:
        """Fit a simple linear regression model."""
        n = len(values)
        if n < 2:
            return {'slope': 0.0, 'intercept': values[0] if values else 0.0}

        x = list(range(n))
        y = values

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = sum((xi - mean_x) ** 2 for xi in x)

        slope = numerator / denominator if denominator != 0 else 0.0
        intercept = mean_y - slope * mean_x

        return {
            'slope': slope,
            'intercept': intercept,
            'mean_x': mean_x,
            'mean_y': mean_y
        }

    def _generate_prediction(self, model: PredictionModel, history: List[float],
                           horizon: int) -> Optional[BehaviorPrediction]:
        """Generate prediction using trained model."""
        if model.model_type == 'linear_trend':
            params = model.parameters
            slope = params.get('slope', 0.0)
            intercept = params.get('intercept', 0.0)

            # Predict future value
            last_index = len(history) - 1
            predicted_value = intercept + slope * (last_index + horizon)

            # Calculate confidence interval (simplified)
            confidence_radius = abs(slope) * horizon * 0.5  # Rough estimate
            confidence_interval = (
                max(0.0, predicted_value - confidence_radius),
                predicted_value + confidence_radius
            )

            prediction = BehaviorPrediction(
                prediction_id=f"pred_{model.target_metric}_{int(time.time())}",
                target_metric=model.target_metric,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                prediction_horizon=horizon,
                timestamp=time.time(),
                model_used=model.model_id,
                confidence=model.confidence,
                evidence={
                    'model_accuracy': model.accuracy_history[-1] if model.accuracy_history else 0.0,
                    'historical_trend': slope,
                    'data_points': len(history)
                }
            )

            return prediction

        return None

    def _evaluate_model_accuracy(self, model: PredictionModel, history: List[float]) -> float:
        """Evaluate prediction model accuracy using cross-validation."""
        if len(history) < 5:
            return 0.0

        # Simple validation: predict each point from previous points
        predictions = []
        actuals = []

        for i in range(3, len(history)):
            train_data = history[:i]
            actual_next = history[i]

            if len(train_data) >= 3:
                temp_model = PredictionModel(
                    model_id='temp',
                    target_metric=model.target_metric,
                    model_type=model.model_type,
                    parameters=self._fit_linear_model(train_data)
                )

                prediction = self._generate_prediction(temp_model, train_data, 1)
                if prediction:
                    predictions.append(prediction.predicted_value)
                    actuals.append(actual_next)

        if not predictions:
            return 0.0

        # Calculate mean absolute percentage error
        mape = sum(abs(p - a) / max(abs(a), 0.001) for p, a in zip(predictions, actuals)) / len(predictions)

        # Convert to accuracy (lower MAPE = higher accuracy)
        accuracy = max(0.0, 1.0 - mape)

        return accuracy

    def _calculate_transition_probabilities(self) -> Dict[str, Dict[str, float]]:
        """Calculate state transition probabilities for event types."""
        transition_probs = {}

        for current_state, transitions in self.state_transitions.items():
            total_transitions = sum(transitions.values())
            if total_transitions > 0:
                transition_probs[current_state] = {
                    next_state: count / total_transitions
                    for next_state, count in transitions.items()
                }

        return transition_probs

    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation as volatility measure."""
        if len(values) < 2:
            return 0.0

        try:
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                return 0.0

            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5

            return std_dev / abs(mean_val)
        except:
            return 0.0

    def get_predictive_insights(self) -> Dict[str, Any]:
        """
        Get comprehensive predictive insights.

        Returns:
            Dictionary with all predictive insights
        """
        behavior_predictions = self.predict_system_behavior()
        anomaly_risks = self.predict_anomaly_risks()
        event_forecast = self.forecast_event_patterns()

        return {
            'behavior_predictions': behavior_predictions,
            'risk_predictions': [
                {
                    'risk_type': risk.risk_type,
                    'probability': risk.probability,
                    'severity': risk.severity,
                    'timeframe': risk.timeframe,
                    'indicators': risk.indicators,
                    'mitigation_actions': risk.mitigation_actions
                }
                for risk in anomaly_risks
            ],
            'event_forecast': event_forecast,
            'model_performance': {
                model_name: {
                    'accuracy': model.accuracy_history[-1] if model.accuracy_history else 0.0,
                    'confidence': model.confidence,
                    'last_trained': model.last_trained
                }
                for model_name, model in self.prediction_models.items()
            },
            'data_quality': {
                'metrics_available': len(self.metric_history),
                'sequences_available': len(self.event_sequences),
                'models_trained': len(self.prediction_models)
            },
            'timestamp': time.time()
        }

    def reset_predictions(self):
        """Reset prediction state for fresh analysis."""
        self.metric_history.clear()
        self.event_sequences.clear()
        self.state_transitions.clear()
        self.prediction_models.clear()
        self.active_predictions.clear()
        self.risk_predictions.clear()
        self.last_model_training = 0.0
        logger.info("Predictive analysis state reset")