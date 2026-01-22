"""
Semantic Analysis Engine for Life system observability.

Provides deep semantic understanding of system behavior through analysis of:
- Event-meaning-decision-action-feedback chains
- Semantic patterns and relationships
- Behavioral anomalies and trends
- Contextual state analysis
"""

import json
import logging
import math
import random
import statistics
from collections import Counter, defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import time
import hashlib

logger = logging.getLogger(__name__)


class AnalysisPlugin:
    """
    Base class for analysis plugins.

    Plugins can extend the analysis capabilities of SemanticAnalysisEngine
    without modifying the core implementation.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.enabled = True

    def analyze(self, correlation_chain: List[Dict]) -> Dict[str, Any]:
        """
        Analyze a correlation chain.

        Args:
            correlation_chain: List of log entries in the chain

        Returns:
            Dict with analysis results specific to this plugin
        """
        raise NotImplementedError("Subclasses must implement analyze method")

    def get_anomaly_score(self, analysis_result: Dict[str, Any]) -> float:
        """
        Calculate anomaly score from analysis results.

        Args:
            analysis_result: Results from analyze() method

        Returns:
            Anomaly score between 0.0 and 1.0
        """
        raise NotImplementedError("Subclasses must implement get_anomaly_score method")

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about this plugin."""
        return {
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'type': self.__class__.__name__
        }


@dataclass
class SemanticPattern:
    """Semantic pattern identified in event chains."""
    pattern_id: str
    event_types: List[str]
    decision_patterns: List[str]
    impact_profile: Dict[str, float]  # Average impact on state parameters
    frequency: int
    confidence: float  # How confident we are in this pattern
    last_seen: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehavioralAnomaly:
    """Detected behavioral anomaly."""
    anomaly_id: str
    anomaly_type: str  # 'pattern_deviation', 'state_aberration', 'chain_breakage'
    severity: float  # 0.0 to 1.0
    description: str
    timestamp: float
    correlation_ids: List[str]
    evidence: Dict[str, Any]


@dataclass
class SystemHealthProfile:
    """Semantic health profile of the system."""
    energy_stability: float
    cognitive_coherence: float
    adaptation_efficiency: float
    memory_integrity: float
    overall_health: float
    risk_factors: List[str]
    recommendations: List[str]


@dataclass
class NeuralNetwork:
    """Simple recurrent neural network for semantic analysis."""
    input_size: int
    hidden_size: int
    output_size: int
    learning_rate: float = 0.01

    def __post_init__(self):
        # Initialize weights with Xavier initialization
        self.Wxh = [[random.uniform(-1, 1) * math.sqrt(2.0/(self.input_size + self.hidden_size))
                     for _ in range(self.hidden_size)] for _ in range(self.input_size)]
        self.Whh = [[random.uniform(-1, 1) * math.sqrt(2.0/(self.hidden_size + self.hidden_size))
                     for _ in range(self.hidden_size)] for _ in range(self.hidden_size)]
        self.Why = [[random.uniform(-1, 1) * math.sqrt(2.0/(self.hidden_size + self.output_size))
                     for _ in range(self.output_size)] for _ in range(self.hidden_size)]

        # Biases
        self.bh = [0.0] * self.hidden_size
        self.by = [0.0] * self.output_size

        # Memory for backpropagation
        self.memory = deque(maxlen=1000)

    def forward(self, inputs: List[List[float]]) -> List[List[float]]:
        """Forward pass through the network."""
        h = [0.0] * self.hidden_size
        outputs = []

        for x in inputs:
            # Hidden layer
            h_new = []
            for j in range(self.hidden_size):
                sum_input = self.bh[j]
                for i in range(self.input_size):
                    sum_input += x[i] * self.Wxh[i][j]
                for k in range(self.hidden_size):
                    sum_input += h[k] * self.Whh[k][j]
                h_new.append(math.tanh(sum_input))
            h = h_new

            # Output layer
            y = []
            for j in range(self.output_size):
                sum_output = self.by[j]
                for k in range(self.hidden_size):
                    sum_output += h[k] * self.Why[k][j]
                y.append(1.0 / (1.0 + math.exp(-sum_output)))  # Sigmoid
            outputs.append(y)

        return outputs

    def train_step(self, inputs: List[List[float]], targets: List[List[float]]):
        """Single training step with backpropagation through time."""
        # Store for backprop
        self.memory.append((inputs.copy(), targets.copy()))

        if len(self.memory) < 2:
            return  # Need more data for training

        # Simple batch training on recent memory
        batch_inputs, batch_targets = self.memory[-1]

        # Forward pass
        predictions = self.forward(batch_inputs)

        # Compute loss and gradients (simplified)
        total_loss = 0.0
        dWhy = [[0.0] * self.output_size for _ in range(self.hidden_size)]
        dby = [0.0] * self.output_size

        for pred, target in zip(predictions, batch_targets):
            for j in range(self.output_size):
                error = pred[j] - target[j]
                total_loss += error * error

                # Output layer gradients
                for k in range(self.hidden_size):
                    dWhy[k][j] += error * pred[j] * (1 - pred[j])  # Sigmoid derivative
                dby[j] += error

        # Update weights (simplified gradient descent)
        for k in range(self.hidden_size):
            for j in range(self.output_size):
                self.Why[k][j] -= self.learning_rate * dWhy[k][j] / len(batch_inputs)

        for j in range(self.output_size):
            self.by[j] -= self.learning_rate * dby[j] / len(batch_inputs)

        return total_loss / len(batch_inputs)


@dataclass
class SemanticEmbedding:
    """Semantic embedding vector for events and states."""
    vector: List[float]
    dimension: int
    source_type: str  # 'event', 'state', 'pattern'
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def cosine_similarity(self, other: 'SemanticEmbedding') -> float:
        """Calculate cosine similarity between embeddings."""
        if len(self.vector) != len(other.vector):
            return 0.0

        dot_product = sum(a * b for a, b in zip(self.vector, other.vector))
        norm_a = math.sqrt(sum(a * a for a in self.vector))
        norm_b = math.sqrt(sum(b * b for b in other.vector))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def euclidean_distance(self, other: 'SemanticEmbedding') -> float:
        """Calculate Euclidean distance between embeddings."""
        if len(self.vector) != len(other.vector):
            return float('inf')

        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.vector, other.vector)))


@dataclass
class AttentionMechanism:
    """Attention mechanism for focusing on relevant parts of sequences."""
    query_size: int
    key_size: int
    value_size: int

    def __post_init__(self):
        # Attention weights
        self.Wq = [[random.uniform(-0.1, 0.1) for _ in range(self.query_size)] for _ in range(self.query_size)]
        self.Wk = [[random.uniform(-0.1, 0.1) for _ in range(self.key_size)] for _ in range(self.key_size)]
        self.Wv = [[random.uniform(-0.1, 0.1) for _ in range(self.value_size)] for _ in range(self.value_size)]

    def compute_attention(self, query: List[float], keys: List[List[float]], values: List[List[float]]) -> List[float]:
        """Compute attention-weighted output."""
        if not keys or not values:
            return [0.0] * self.value_size

        # Compute attention scores
        scores = []
        for key in keys:
            score = sum(q * k for q, k in zip(query, key))
            scores.append(score)

        # Softmax normalization
        max_score = max(scores)
        exp_scores = [math.exp(s - max_score) for s in scores]
        total = sum(exp_scores)
        attention_weights = [s / total for s in exp_scores]

        # Weighted sum of values
        output = [0.0] * self.value_size
        for weight, value in zip(attention_weights, values):
            for i in range(self.value_size):
                output[i] += weight * value[i]

        return output


class SemanticAnalysisEngine:
    """
    Advanced semantic analysis engine with neural networks and deep learning.

    Provides deep semantic understanding through neural embeddings, attention mechanisms,
    and advanced pattern recognition for Life system behavior analysis.
    """

    # Event type categories for semantic grouping
    EVENT_CATEGORIES = {
        'physiological': ['decay', 'recovery', 'fatigue', 'exhaustion', 'vitality'],
        'cognitive': ['cognitive_doubt', 'cognitive_clarity', 'cognitive_confusion',
                     'insight', 'confusion', 'curiosity', 'meaning_found', 'epiphany',
                     'understanding', 'bewilderment', 'comprehension'],
        'emotional': ['joy', 'sadness', 'fear', 'calm', 'discomfort', 'comfort',
                     'anticipation', 'boredom', 'inspiration', 'anxiety', 'serenity',
                     'agitation', 'contentment', 'apprehension', 'enthusiasm'],
        'existential': ['existential_void', 'existential_purpose', 'existential_finitude',
                       'void', 'acceptance', 'clarity_moment', 'purpose_discovery',
                       'mortality_awareness', 'meaning_crisis', 'existential_peace'],
        'social': ['social_presence', 'social_conflict', 'social_harmony',
                  'connection', 'isolation', 'belonging', 'alienation', 'empathy',
                  'conflict', 'cooperation', 'loneliness', 'companionship'],
        'environmental': ['noise', 'shock', 'idle', 'memory_echo', 'disturbance',
                         'stimulus', 'silence', 'echo', 'disruption', 'calm_environment']
    }

    # Enhanced state parameter relationships with weights
    STATE_RELATIONSHIPS = {
        'energy': {'fatigue': 0.8, 'recovery': 0.9, 'stability': 0.6, 'exhaustion': 0.9},
        'integrity': {'shock': 0.8, 'cognitive_confusion': 0.7, 'cognitive_clarity': 0.8,
                     'bewilderment': 0.6, 'comprehension': 0.7},
        'stability': {'noise': 0.7, 'shock': 0.8, 'cognitive_doubt': 0.6, 'calm': 0.8,
                     'disruption': 0.7, 'calm_environment': 0.6},
        'subjective_time': {'cognitive_clarity': 0.7, 'existential_purpose': 0.8,
                           'boredom': 0.6, 'epiphany': 0.9, 'meaning_crisis': 0.7}
    }

    def __init__(self, max_patterns: int = 100, anomaly_threshold: float = 0.7,
                 embedding_dim: int = 64, enable_neural_network: bool = True):
        """
        Initialize the advanced semantic analysis engine.

        Args:
            max_patterns: Maximum number of semantic patterns to track
            anomaly_threshold: Threshold for anomaly detection (0.0-1.0)
            embedding_dim: Dimension of semantic embeddings
            enable_neural_network: Whether to use neural network for analysis
        """
        self.max_patterns = max_patterns
        self.anomaly_threshold = anomaly_threshold
        self.embedding_dim = embedding_dim
        self.enable_neural_network = enable_neural_network

        # Core analysis data structures
        self.semantic_patterns: Dict[str, SemanticPattern] = {}
        self.behavioral_anomalies: List[BehavioralAnomaly] = []
        self.correlation_chains: Dict[str, List[Dict]] = {}
        self.state_evolution: List[Dict] = []

        # Neural network components
        if self.enable_neural_network:
            self.neural_net = NeuralNetwork(
                input_size=embedding_dim,
                hidden_size=embedding_dim // 2,
                output_size=embedding_dim // 4,
                learning_rate=0.01
            )
            self.attention = AttentionMechanism(
                query_size=embedding_dim,
                key_size=embedding_dim,
                value_size=embedding_dim
            )
        else:
            self.neural_net = None
            self.attention = None

        # Semantic embeddings
        self.event_embeddings: Dict[str, SemanticEmbedding] = {}
        self.state_embeddings: Dict[str, SemanticEmbedding] = {}
        self.pattern_embeddings: Dict[str, SemanticEmbedding] = {}

        # Statistical accumulators
        self.event_type_frequencies: Counter = Counter()
        self.decision_pattern_frequencies: Counter = Counter()
        self.impact_accumulators: Dict[str, List[float]] = defaultdict(list)

        # Advanced analytics
        self.embedding_similarity_matrix: Dict[str, Dict[str, float]] = {}
        self.temporal_patterns: Dict[str, List[Tuple[float, List[float]]]] = defaultdict(list)
        self.causal_relationships: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Pattern learning
        self.pattern_learning_window = 1000
        self.min_pattern_confidence = 0.6
        self.adaptation_rate = 0.1

        # Performance tracking
        self.analysis_times: deque = deque(maxlen=1000)
        self.accuracy_metrics: Dict[str, float] = {
            'anomaly_detection_precision': 0.0,
            'anomaly_detection_recall': 0.0,
            'anomaly_detection_f1_score': 0.0,
            'pattern_recognition_accuracy': 0.0,
            'semantic_coherence_score': 0.0,
            'false_positive_rate': 0.0,
            'false_negative_rate': 0.0,
            'temporal_stability_score': 0.0
        }

        # Advanced metrics tracking
        self.anomaly_detection_history: deque = deque(maxlen=1000)  # (predicted_anomaly, actual_anomaly, confidence)
        self.analysis_quality_history: deque = deque(maxlen=500)   # Analysis quality scores
        self.plugin_performance_metrics: Dict[str, Dict[str, Any]] = {}  # Plugin-specific metrics

        # Plugin system
        self.analysis_plugins: Dict[str, AnalysisPlugin] = {}
        self.plugin_results_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize default plugins
        self._initialize_default_plugins()

        # Initialize semantic embeddings
        self._initialize_semantic_embeddings()

        logger.info(f"Advanced SemanticAnalysisEngine initialized (neural_network={'enabled' if enable_neural_network else 'disabled'})")

    def _initialize_default_plugins(self):
        """Initialize default analysis plugins."""
        # Default plugins are implemented as methods, not separate classes
        # This allows for plugin-like extensibility while keeping the core simple
        pass

    def add_plugin(self, plugin: AnalysisPlugin):
        """
        Add an analysis plugin.

        Args:
            plugin: AnalysisPlugin instance to add
        """
        if plugin.name in self.analysis_plugins:
            logger.warning(f"Plugin {plugin.name} already exists, replacing")
        self.analysis_plugins[plugin.name] = plugin
        logger.info(f"Added analysis plugin: {plugin.name}")

    def remove_plugin(self, plugin_name: str):
        """
        Remove an analysis plugin.

        Args:
            plugin_name: Name of the plugin to remove
        """
        if plugin_name in self.analysis_plugins:
            del self.analysis_plugins[plugin_name]
            if plugin_name in self.plugin_results_cache:
                del self.plugin_results_cache[plugin_name]
            logger.info(f"Removed analysis plugin: {plugin_name}")
        else:
            logger.warning(f"Plugin {plugin_name} not found")

    def get_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered plugins.

        Returns:
            Dict mapping plugin names to plugin info
        """
        return {name: plugin.get_plugin_info() for name, plugin in self.analysis_plugins.items()}

    def _run_plugin_analysis(self, correlation_id: str, chain_entries: List[Dict]) -> Dict[str, Any]:
        """
        Run analysis using all enabled plugins.

        Args:
            correlation_id: Correlation ID for the chain
            chain_entries: List of log entries in the chain

        Returns:
            Dict with plugin analysis results
        """
        plugin_results = {}

        for plugin_name, plugin in self.analysis_plugins.items():
            if not plugin.enabled:
                continue

            try:
                # Check cache first
                cache_key = f"{correlation_id}_{plugin_name}"
                if cache_key in self.plugin_results_cache:
                    cached_result = self.plugin_results_cache[cache_key]
                    plugin_results[plugin_name] = cached_result
                    continue

                # Run plugin analysis
                result = plugin.analyze(chain_entries)
                anomaly_score = plugin.get_anomaly_score(result)

                plugin_result = {
                    'result': result,
                    'anomaly_score': anomaly_score,
                    'timestamp': time.time()
                }

                plugin_results[plugin_name] = plugin_result
                self.plugin_results_cache[cache_key] = plugin_result

                # Update plugin performance metrics
                self.update_plugin_performance_metrics(plugin_name, plugin_result)

            except Exception as e:
                logger.error(f"Error running plugin {plugin_name}: {e}")
                plugin_results[plugin_name] = {
                    'error': str(e),
                    'anomaly_score': 0.0,
                    'timestamp': time.time()
                }

        return plugin_results

    def _initialize_semantic_embeddings(self):
        """Initialize semantic embeddings for events, states, and patterns."""
        # Create embeddings for event types
        for category, events in self.EVENT_CATEGORIES.items():
            for event_type in events:
                embedding_vector = self._create_semantic_embedding(event_type, 'event')
                self.event_embeddings[event_type] = SemanticEmbedding(
                    vector=embedding_vector,
                    dimension=self.embedding_dim,
                    source_type='event',
                    timestamp=time.time(),
                    metadata={'category': category}
                )

        # Create embeddings for state parameters
        state_params = ['energy', 'integrity', 'stability', 'subjective_time']
        for param in state_params:
            embedding_vector = self._create_semantic_embedding(param, 'state')
            self.state_embeddings[param] = SemanticEmbedding(
                vector=embedding_vector,
                dimension=self.embedding_dim,
                source_type='state',
                timestamp=time.time(),
                metadata={'parameter_type': 'core_state'}
            )

    def _create_semantic_embedding(self, text: str, source_type: str) -> List[float]:
        """Create semantic embedding vector from text using hashing and randomization."""
        # Use hash of text as seed for reproducible but distributed vectors
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Create pseudo-random vector using hash as seed
        random.seed(hash_int)
        vector = []

        for i in range(self.embedding_dim):
            # Create distributed values with some semantic clustering
            base_value = random.uniform(-1.0, 1.0)

            # Add semantic clustering based on source type
            if source_type == 'event':
                base_value += random.gauss(0, 0.1)  # Events cluster around origin
            elif source_type == 'state':
                base_value += random.gauss(0.5, 0.1)  # States cluster positive
            elif source_type == 'pattern':
                base_value += random.gauss(-0.5, 0.1)  # Patterns cluster negative

            # Normalize to [-1, 1]
            vector.append(max(-1.0, min(1.0, base_value)))

        return vector

    def _create_chain_embeddings(self, chain_entries: List[Dict]) -> Dict[str, Any]:
        """Create comprehensive embeddings for a correlation chain."""
        embeddings = {
            'event_embeddings': [],
            'state_embeddings': [],
            'decision_embeddings': [],
            'sequence_embedding': [],
            'attention_weights': [],
            'temporal_embedding': []
        }

        # Extract embeddings for different stages
        for entry in chain_entries:
            stage = entry.get('stage', 'unknown')
            timestamp = entry.get('timestamp', time.time())

            if stage == 'event':
                event_type = entry.get('event_type', 'unknown')
                if event_type in self.event_embeddings:
                    emb = self.event_embeddings[event_type]
                    embeddings['event_embeddings'].append((timestamp, emb.vector))

            elif stage == 'meaning':
                # Create embedding from impact profile
                impact = entry.get('data', {}).get('impact', {})
                impact_vector = self._create_impact_embedding(impact)
                embeddings['state_embeddings'].append((timestamp, impact_vector))

            elif stage == 'decision':
                pattern = entry.get('data', {}).get('pattern', 'unknown')
                pattern_vector = self._create_semantic_embedding(pattern, 'pattern')
                embeddings['decision_embeddings'].append((timestamp, pattern_vector))

        # Create sequence embedding using attention
        if embeddings['event_embeddings'] and self.attention:
            sequence_vectors = [emb[1] for emb in embeddings['event_embeddings']]
            query_vector = sequence_vectors[0] if sequence_vectors else [0.0] * self.embedding_dim

            attention_output = self.attention.compute_attention(
                query_vector, sequence_vectors, sequence_vectors
            )
            embeddings['sequence_embedding'] = attention_output
            embeddings['attention_weights'] = [1.0] * len(sequence_vectors)  # Simplified

        # Create temporal embedding
        if chain_entries:
            timestamps = [e.get('timestamp', 0) for e in chain_entries if 'timestamp' in e]
            if timestamps:
                temporal_span = max(timestamps) - min(timestamps)
                temporal_density = len(chain_entries) / max(temporal_span, 1.0)
                embeddings['temporal_embedding'] = [
                    temporal_span / 100.0,  # Normalized span
                    temporal_density,       # Events per second
                    len(chain_entries) / 10.0,  # Normalized length
                    statistics.mean(timestamps) / time.time() if timestamps else 0.0  # Relative timing
                ]

        return embeddings

    def _create_impact_embedding(self, impact: Dict[str, float]) -> List[float]:
        """Create embedding vector from impact profile."""
        base_vector = [0.0] * self.embedding_dim

        for param, value in impact.items():
            if param in self.state_embeddings:
                param_emb = self.state_embeddings[param]
                # Weight the parameter embedding by impact magnitude
                weight = min(1.0, abs(value) / 2.0)  # Normalize impact magnitude
                for i in range(self.embedding_dim):
                    base_vector[i] += param_emb.vector[i] * weight * (1.0 if value >= 0 else -1.0)

        # Normalize vector
        magnitude = math.sqrt(sum(x*x for x in base_vector))
        if magnitude > 0:
            base_vector = [x / magnitude for x in base_vector]

        return base_vector

    def _categorize_chain_advanced(self, events: List[Dict]) -> str:
        """Advanced chain categorization using embeddings and neural analysis."""
        if not events:
            return 'empty'

        event_types = [e.get('event_type', 'unknown') for e in events]
        category_scores = defaultdict(float)

        # Use embedding similarity for categorization
        for event_type in event_types:
            if event_type in self.event_embeddings:
                emb = self.event_embeddings[event_type]
                category = emb.metadata.get('category', 'unknown')

                # Find most similar known embeddings
                similarities = []
                for known_type, known_emb in self.event_embeddings.items():
                    if known_emb.metadata.get('category') == category:
                        sim = emb.cosine_similarity(known_emb)
                        similarities.append(sim)

                avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
                category_scores[category] += avg_similarity

        if not category_scores:
            return 'uncategorized'

        return max(category_scores.items(), key=lambda x: x[1])[0]

    def _analyze_behavioral_context_advanced(self, chain_entries: List[Dict]) -> Dict[str, Any]:
        """Advanced behavioral context analysis with temporal and causal reasoning."""
        context = self._analyze_behavioral_context(chain_entries)  # Use base analysis

        # Add advanced metrics
        context.update({
            'temporal_consistency': self._calculate_temporal_consistency(chain_entries),
            'causal_chain_strength': self._calculate_causal_chain_strength(chain_entries),
            'semantic_flow_efficiency': self._calculate_semantic_flow_efficiency(chain_entries),
            'adaptive_capacity_indicator': self._calculate_adaptive_capacity(chain_entries),
            'processing_depth': self._calculate_processing_depth(chain_entries)
        })

        return context

    def _calculate_anomaly_score_advanced(self, chain_entries: List[Dict],
                                        embeddings: Dict[str, Any]) -> float:
        """Advanced anomaly scoring using embeddings and neural features."""
        base_score = self._calculate_anomaly_score(chain_entries)

        # Neural network anomaly detection
        neural_anomaly = 0.0
        if self.enable_neural_network and embeddings.get('sequence_embedding'):
            sequence_emb = embeddings['sequence_embedding']
            if sequence_emb:
                # Compare with expected patterns
                expected_patterns = list(self.pattern_embeddings.values())
                if expected_patterns:
                    similarities = [self._cosine_similarity(sequence_emb, p.vector)
                                  for p in expected_patterns]
                    max_similarity = max(similarities)
                    neural_anomaly = 1.0 - max_similarity  # Lower similarity = higher anomaly

        # Embedding-based anomaly detection
        embedding_anomaly = 0.0
        if embeddings.get('event_embeddings'):
            event_vectors = [emb[1] for emb in embeddings['event_embeddings']]
            if len(event_vectors) > 1:
                # Check for semantic inconsistency
                inconsistencies = []
                for i in range(1, len(event_vectors)):
                    sim = self._cosine_similarity(event_vectors[i-1], event_vectors[i])
                    if sim < 0.3:  # Low similarity between consecutive events
                        inconsistencies.append(1.0 - sim)
                embedding_anomaly = sum(inconsistencies) / len(inconsistencies) if inconsistencies else 0.0

        # Combine scores with weights
        combined_score = (
            base_score * 0.4 +           # Base analysis
            neural_anomaly * 0.4 +       # Neural network
            embedding_anomaly * 0.2      # Embedding analysis
        )

        return min(1.0, combined_score)

    def _calculate_semantic_coherence(self, embeddings: Dict[str, Any]) -> float:
        """Calculate semantic coherence of the chain using embeddings."""
        coherence_scores = []

        # Event sequence coherence
        event_embs = embeddings.get('event_embeddings', [])
        if len(event_embs) > 1:
            event_vectors = [emb[1] for emb in event_embs]
            for i in range(1, len(event_vectors)):
                sim = self._cosine_similarity(event_vectors[i-1], event_vectors[i])
                coherence_scores.append(sim)

        # State transition coherence
        state_embs = embeddings.get('state_embeddings', [])
        if len(state_embs) > 1:
            state_vectors = [emb[1] for emb in state_embs]
            for i in range(1, len(state_vectors)):
                sim = self._cosine_similarity(state_vectors[i-1], state_vectors[i])
                coherence_scores.append(sim * 1.2)  # Weight state coherence higher

        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.5

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _analyze_temporal_patterns(self, chain_entries: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in the correlation chain."""
        if not chain_entries:
            return {'pattern': 'empty_chain'}

        timestamps = [e.get('timestamp', 0) for e in chain_entries if 'timestamp' in e]
        if len(timestamps) < 2:
            return {'pattern': 'insufficient_data'}

        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]

        return {
            'average_interval': sum(intervals) / len(intervals),
            'interval_variance': statistics.variance(intervals) if len(intervals) > 1 else 0.0,
            'total_duration': max(timestamps) - min(timestamps),
            'processing_rate': len(chain_entries) / max(max(timestamps) - min(timestamps), 0.001),
            'stage_distribution': self._analyze_stage_timing(chain_entries)
        }

    def _analyze_stage_timing(self, chain_entries: List[Dict]) -> Dict[str, float]:
        """Analyze timing distribution across different stages."""
        stage_times = defaultdict(list)

        for entry in chain_entries:
            stage = entry.get('stage', 'unknown')
            timestamp = entry.get('timestamp', 0)
            stage_times[stage].append(timestamp)

        distribution = {}
        total_entries = len(chain_entries)

        for stage, times in stage_times.items():
            distribution[f'{stage}_ratio'] = len(times) / total_entries
            if len(times) > 1:
                distribution[f'{stage}_span'] = max(times) - min(times)

        return distribution

    def _extract_causal_insights(self, chain_entries: List[Dict]) -> Dict[str, Any]:
        """Extract causal relationships and insights from the chain."""
        insights = {
            'event_to_meaning_delay': [],
            'meaning_to_decision_delay': [],
            'decision_to_action_delay': [],
            'action_to_feedback_delay': [],
            'causal_strength': 0.0
        }

        # Extract timing relationships
        stage_timestamps = defaultdict(list)
        for entry in chain_entries:
            stage = entry.get('stage')
            if stage:
                timestamp = entry.get('timestamp', 0)
                stage_timestamps[stage].append(timestamp)

        # Calculate delays between stages
        if 'event' in stage_timestamps and 'meaning' in stage_timestamps:
            event_time = min(stage_timestamps['event'])
            meaning_time = min(stage_timestamps['meaning'])
            insights['event_to_meaning_delay'].append(meaning_time - event_time)

        if 'meaning' in stage_timestamps and 'decision' in stage_timestamps:
            meaning_time = max(stage_timestamps['meaning'])
            decision_time = min(stage_timestamps['decision'])
            insights['meaning_to_decision_delay'].append(decision_time - meaning_time)

        if 'decision' in stage_timestamps and 'action' in stage_timestamps:
            decision_time = max(stage_timestamps['decision'])
            action_time = min(stage_timestamps['action'])
            insights['decision_to_action_delay'].append(action_time - decision_time)

        if 'action' in stage_timestamps and 'feedback' in stage_timestamps:
            action_time = max(stage_timestamps['action'])
            feedback_time = min(stage_timestamps['feedback'])
            insights['action_to_feedback_delay'].append(feedback_time - action_time)

        # Calculate causal strength based on processing completeness
        expected_stages = {'event', 'meaning', 'decision', 'action', 'feedback'}
        present_stages = set(stage_timestamps.keys())
        insights['causal_strength'] = len(present_stages.intersection(expected_stages)) / len(expected_stages)

        return insights

    def _calculate_temporal_consistency(self, chain_entries: List[Dict]) -> float:
        """Calculate temporal consistency of the processing chain."""
        timestamps = [e.get('timestamp', 0) for e in chain_entries if 'timestamp' in e]
        if len(timestamps) < 2:
            return 0.5

        # Check for monotonic time progression
        monotonic_score = 1.0
        for i in range(1, len(timestamps)):
            if timestamps[i] < timestamps[i-1]:
                monotonic_score -= 0.1

        # Check for reasonable time intervals
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_interval = sum(intervals) / len(intervals)
        interval_consistency = 1.0 - min(1.0, statistics.stdev(intervals) / max(avg_interval, 0.001))

        return (monotonic_score + interval_consistency) / 2.0

    def _calculate_causal_chain_strength(self, chain_entries: List[Dict]) -> float:
        """Calculate the strength of causal relationships in the chain."""
        stages = [e.get('stage') for e in chain_entries]
        expected_sequence = ['event', 'meaning', 'decision', 'action', 'feedback']

        # Check sequence adherence
        sequence_score = 0.0
        for i, expected in enumerate(expected_sequence):
            if i < len(stages) and stages[i] == expected:
                sequence_score += 1.0

        sequence_score /= len(expected_sequence)

        # Check stage completeness
        present_stages = set(stages)
        completeness_score = len(present_stages.intersection(set(expected_sequence))) / len(expected_sequence)

        return (sequence_score + completeness_score) / 2.0

    def _calculate_semantic_flow_efficiency(self, chain_entries: List[Dict]) -> float:
        """Calculate efficiency of semantic information flow."""
        if not chain_entries:
            return 0.0

        # Measure information transformation efficiency
        stages_with_data = 0
        total_stages = len(chain_entries)

        for entry in chain_entries:
            if entry.get('data') or entry.get('event_type'):
                stages_with_data += 1

        data_density = stages_with_data / total_stages

        # Measure processing continuity
        timestamps = [e.get('timestamp', 0) for e in chain_entries if 'timestamp' in e]
        if len(timestamps) >= 2:
            time_span = max(timestamps) - min(timestamps)
            processing_density = len(chain_entries) / max(time_span, 1.0)
        else:
            processing_density = 0.5

        return (data_density + processing_density) / 2.0

    def _calculate_adaptive_capacity(self, chain_entries: List[Dict]) -> float:
        """Calculate the adaptive capacity demonstrated in the chain."""
        # Look for decision pattern diversity and effectiveness
        decisions = [e for e in chain_entries if e.get('stage') == 'decision']
        if not decisions:
            return 0.5

        patterns = [d.get('data', {}).get('pattern', 'unknown') for d in decisions]
        unique_patterns = len(set(patterns))

        # Higher diversity suggests better adaptation
        diversity_score = min(1.0, unique_patterns / 3.0)  # Cap at 3 different patterns

        # Check for feedback incorporation
        has_feedback = any(e.get('stage') == 'feedback' for e in chain_entries)
        feedback_bonus = 0.2 if has_feedback else 0.0

        return diversity_score + feedback_bonus

    def _calculate_processing_depth(self, chain_entries: List[Dict]) -> float:
        """Calculate the depth of processing in the chain."""
        # Measure how thoroughly each stage is processed
        depth_scores = []

        for entry in chain_entries:
            stage = entry.get('stage')
            data_completeness = 0.0

            if stage == 'event' and 'event_type' in entry:
                data_completeness = 1.0
            elif stage == 'meaning' and entry.get('data', {}).get('impact'):
                impact = entry['data']['impact']
                data_completeness = min(1.0, len(impact) / 4.0)  # Expect 4 impact parameters
            elif stage == 'decision' and entry.get('data', {}).get('pattern'):
                data_completeness = 1.0
            elif stage == 'action' and entry.get('data'):
                data_completeness = 0.8  # Actions typically have some data
            elif stage == 'feedback' and entry.get('data'):
                data_completeness = 0.9  # Feedback is important

            depth_scores.append(data_completeness)

        return sum(depth_scores) / len(depth_scores) if depth_scores else 0.0

    def analyze_correlation_chain(self, correlation_id: str, chain_entries: List[Dict]) -> Dict[str, Any]:
        """
        Perform advanced semantic analysis of a correlation chain using neural networks.

        Args:
            correlation_id: Correlation ID for the chain
            chain_entries: List of log entries in the chain

        Returns:
            Comprehensive semantic analysis results
        """
        start_time = time.time()

        if not chain_entries:
            return {}

        # Extract chain components with enhanced processing
        events = [e for e in chain_entries if e.get('stage') == 'event']
        meanings = [e for e in chain_entries if e.get('stage') == 'meaning']
        decisions = [e for e in chain_entries if e.get('stage') == 'decision']
        actions = [e for e in chain_entries if e.get('stage') == 'action']
        feedbacks = [e for e in chain_entries if e.get('stage') == 'feedback']

        # Create semantic embeddings for the chain
        chain_embeddings = self._create_chain_embeddings(chain_entries)

        # Neural network analysis
        neural_features = []
        if self.enable_neural_network and self.neural_net:
            neural_output = self.neural_net.forward([chain_embeddings['sequence_embedding']])
            neural_features = neural_output[0] if neural_output else []

        # Advanced semantic analysis
        chain_semantics = {
            'correlation_id': correlation_id,
            'chain_length': len(chain_entries),
            'event_types': [e.get('event_type', 'unknown') for e in events],
            'decision_patterns': [d.get('data', {}).get('pattern', 'unknown') for d in decisions],
            'impact_profile': self._extract_impact_profile(meanings),
            'semantic_category': self._categorize_chain_advanced(events),
            'behavioral_context': self._analyze_behavioral_context_advanced(chain_entries),
            'anomaly_score': self._calculate_anomaly_score_advanced(chain_entries, chain_embeddings),
            'neural_features': neural_features,
            'semantic_coherence': self._calculate_semantic_coherence(chain_embeddings),
            'temporal_patterns': self._analyze_temporal_patterns(chain_entries),
            'causal_insights': self._extract_causal_insights(chain_entries),
            'embedding_analysis': chain_embeddings,
            'timestamp': time.time(),
            'analysis_duration': time.time() - start_time
        }

        # Update learning data with neural adaptation
        self._update_advanced_pattern_learning(chain_semantics, chain_embeddings)
        self.correlation_chains[correlation_id] = chain_entries

        # Run plugin analysis
        plugin_results = self._run_plugin_analysis(correlation_id, chain_entries)
        if plugin_results:
            chain_semantics['plugin_analysis'] = plugin_results

            # Incorporate plugin anomaly scores into overall anomaly score
            plugin_anomaly_scores = [result.get('anomaly_score', 0.0)
                                   for result in plugin_results.values()
                                   if 'anomaly_score' in result]
            if plugin_anomaly_scores:
                avg_plugin_score = sum(plugin_anomaly_scores) / len(plugin_anomaly_scores)
                # Blend plugin scores with base anomaly score (weighted average)
                base_score = chain_semantics.get('anomaly_score', 0.0)
                chain_semantics['anomaly_score'] = (base_score * 0.7) + (avg_plugin_score * 0.3)

        # Track analysis time
        analysis_time = time.time() - start_time
        self.analysis_times.append(analysis_time)

        # Update analysis quality metrics
        chain_semantics['analysis_duration'] = analysis_time
        self.update_analysis_quality_metrics(chain_semantics)

        return chain_semantics

    def _extract_impact_profile(self, meanings: List[Dict]) -> Dict[str, float]:
        """Extract average impact profile from meaning entries."""
        impacts = []
        for meaning in meanings:
            data = meaning.get('data', {})
            if 'impact' in data:
                impacts.append(data['impact'])

        if not impacts:
            return {}

        # Calculate average impact across all meanings
        avg_impact = {}
        param_counts = defaultdict(int)

        for impact in impacts:
            for param, value in impact.items():
                if param not in avg_impact:
                    avg_impact[param] = 0.0
                avg_impact[param] += value
                param_counts[param] += 1

        for param in avg_impact:
            avg_impact[param] /= param_counts[param]

        return dict(avg_impact)

    def _categorize_chain(self, events: List[Dict]) -> str:
        """Categorize the semantic nature of an event chain."""
        if not events:
            return 'empty'

        event_types = [e.get('event_type', 'unknown') for e in events]

        # Count categories
        category_scores = defaultdict(int)
        for event_type in event_types:
            for category, types in self.EVENT_CATEGORIES.items():
                if event_type in types:
                    category_scores[category] += 1

        if not category_scores:
            return 'uncategorized'

        # Return dominant category
        return max(category_scores.items(), key=lambda x: x[1])[0]

    def _analyze_behavioral_context(self, chain_entries: List[Dict]) -> Dict[str, Any]:
        """Analyze the behavioral context of a chain."""
        context = {
            'has_meaning_processing': any(e.get('stage') == 'meaning' for e in chain_entries),
            'has_decision_making': any(e.get('stage') == 'decision' for e in chain_entries),
            'has_action_execution': any(e.get('stage') == 'action' for e in chain_entries),
            'has_feedback_loop': any(e.get('stage') == 'feedback' for e in chain_entries),
            'processing_completeness': 0.0,
            'response_efficiency': 0.0
        }

        # Calculate processing completeness (0.0 to 1.0)
        expected_stages = {'event', 'meaning', 'decision', 'action', 'feedback'}
        present_stages = {e.get('stage') for e in chain_entries if e.get('stage') in expected_stages}
        context['processing_completeness'] = len(present_stages) / len(expected_stages)

        # Calculate response efficiency based on timing
        timestamps = [e.get('timestamp', 0) for e in chain_entries if 'timestamp' in e]
        if len(timestamps) >= 2:
            time_span = max(timestamps) - min(timestamps)
            context['response_efficiency'] = min(1.0, 1.0 / (1.0 + time_span))  # Efficiency decreases with time

        return context

    def _calculate_anomaly_score(self, chain_entries: List[Dict]) -> float:
        """
        Calculate anomaly score based on statistical analysis of behavioral patterns.

        Uses dynamic thresholds based on historical data instead of hardcoded values.
        """
        score = 0.0
        factors = 0

        # Factor 1: Chain completeness analysis
        completeness = self._analyze_chain_completeness(chain_entries)
        completeness_threshold = self._get_dynamic_threshold('completeness', 0.8)
        if completeness < completeness_threshold:
            anomaly_contribution = (completeness_threshold - completeness) / completeness_threshold
            score += anomaly_contribution * 0.3
            factors += 1

        # Factor 2: Behavioral pattern analysis
        pattern_score = self._analyze_behavioral_patterns(chain_entries)
        pattern_threshold = self._get_dynamic_threshold('pattern', 0.7)
        if pattern_score > pattern_threshold:
            score += pattern_score * 0.4
            factors += 1

        # Factor 3: Impact distribution analysis
        impact_score = self._analyze_impact_distribution(chain_entries)
        impact_threshold = self._get_dynamic_threshold('impact', 0.6)
        if impact_score > impact_threshold:
            score += impact_score * 0.3
            factors += 1

        # Update historical data for dynamic thresholds
        self._update_historical_metrics('completeness', completeness)
        self._update_historical_metrics('pattern', pattern_score)
        self._update_historical_metrics('impact', impact_score)

        return min(1.0, score) if factors > 0 else 0.0

    def _analyze_chain_completeness(self, chain_entries: List[Dict]) -> float:
        """
        Analyze completeness of processing chain.

        A complete chain should have: event → meaning → decision → action → feedback
        """
        stages_present = set()
        for entry in chain_entries:
            stages_present.add(entry.get('stage', 'unknown'))

        required_stages = {'event', 'meaning', 'decision', 'action', 'feedback'}
        completeness = len(stages_present & required_stages) / len(required_stages)

        # Check for logical sequence
        stage_order = []
        for entry in chain_entries:
            stage = entry.get('stage')
            if stage in required_stages:
                stage_order.append(stage)

        # Verify temporal order (should be event → meaning → decision → action → feedback)
        expected_order = ['event', 'meaning', 'decision', 'action', 'feedback']
        sequence_score = 0.0

        for i, expected_stage in enumerate(expected_order):
            if expected_stage in stage_order:
                actual_pos = stage_order.index(expected_stage)
                # Penalize if stage appears out of order
                if actual_pos > i:
                    sequence_score -= 0.1

        sequence_penalty = max(0, -sequence_score)

        return max(0.0, completeness - sequence_penalty)

    def _analyze_behavioral_patterns(self, chain_entries: List[Dict]) -> float:
        """
        Analyze behavioral patterns for anomalies.

        Returns anomaly score based on deviation from learned patterns.
        """
        # Extract event sequence
        events = [e for e in chain_entries if e.get('stage') == 'event']
        event_types = [e.get('event_type', 'unknown') for e in events]

        if not event_types:
            return 0.0

        # Calculate transition probabilities
        transitions = {}
        for i in range(len(event_types) - 1):
            current = event_types[i]
            next_event = event_types[i + 1]
            key = f"{current}->{next_event}"
            transitions[key] = transitions.get(key, 0) + 1

        # Compare with historical patterns
        anomaly_score = 0.0
        for transition, count in transitions.items():
            expected_freq = self._get_expected_transition_frequency(transition)
            if expected_freq < 0.01:  # Very rare transition
                anomaly_score += 0.3
            elif count > expected_freq * 3:  # Much more frequent than expected
                anomaly_score += 0.2

        # Update transition learning
        for transition, count in transitions.items():
            self._update_transition_frequency(transition, count)

        return min(1.0, anomaly_score)

    def _analyze_impact_distribution(self, chain_entries: List[Dict]) -> float:
        """
        Analyze distribution of impacts for anomalies.

        Detects unusual impact patterns that deviate from normal behavior.
        """
        meanings = [e for e in chain_entries if e.get('stage') == 'meaning']
        if not meanings:
            return 0.0

        impacts = []
        for meaning in meanings:
            impact_data = meaning.get('data', {}).get('impact', {})
            if impact_data:
                # Calculate total impact magnitude
                magnitude = sum(abs(v) for v in impact_data.values())
                impacts.append(magnitude)

        if not impacts:
            return 0.0

        # Statistical analysis of impact distribution
        avg_impact = sum(impacts) / len(impacts)

        # Check for outliers using modified z-score
        anomaly_score = 0.0
        for impact in impacts:
            if avg_impact > 0:
                z_score = abs(impact - avg_impact) / avg_impact
                if z_score > 2.0:  # Significant outlier
                    anomaly_score += 0.2

        # Check for impact concentration (all impacts on one parameter)
        if meanings:
            param_impacts = {}
            for meaning in meanings:
                impact_data = meaning.get('data', {}).get('impact', {})
                for param, value in impact_data.items():
                    param_impacts[param] = param_impacts.get(param, 0) + abs(value)

            if param_impacts:
                max_param_impact = max(param_impacts.values())
                total_impact = sum(param_impacts.values())
                concentration_ratio = max_param_impact / total_impact if total_impact > 0 else 0

                if concentration_ratio > 0.8:  # 80%+ impact on one parameter
                    anomaly_score += 0.1

        return min(1.0, anomaly_score)

    def _get_dynamic_threshold(self, metric_type: str, default_threshold: float) -> float:
        """
        Get dynamic threshold based on historical data.

        Uses statistical analysis of historical metrics to set adaptive thresholds.
        """
        if not hasattr(self, '_historical_metrics'):
            self._historical_metrics = {}

        if metric_type not in self._historical_metrics:
            return default_threshold

        history = self._historical_metrics[metric_type]
        if len(history) < 10:  # Need minimum history
            return default_threshold

        # Calculate mean and standard deviation
        mean_val = sum(history) / len(history)
        variance = sum((x - mean_val) ** 2 for x in history) / len(history)
        std_dev = variance ** 0.5

        # Set threshold at mean + 2*std_dev for anomaly detection
        dynamic_threshold = mean_val + 2 * std_dev

        # Ensure reasonable bounds
        return max(default_threshold * 0.5, min(dynamic_threshold, default_threshold * 2.0))

    def _update_historical_metrics(self, metric_type: str, value: float):
        """Update historical metrics for dynamic threshold calculation."""
        if not hasattr(self, '_historical_metrics'):
            self._historical_metrics = {}

        if metric_type not in self._historical_metrics:
            self._historical_metrics[metric_type] = []

        self._historical_metrics[metric_type].append(value)

        # Keep only recent history (last 1000 values)
        if len(self._historical_metrics[metric_type]) > 1000:
            self._historical_metrics[metric_type] = self._historical_metrics[metric_type][-1000:]

    def _get_expected_transition_frequency(self, transition: str) -> float:
        """Get expected frequency for event transition."""
        if not hasattr(self, '_transition_frequencies'):
            self._transition_frequencies = {}

        return self._transition_frequencies.get(transition, 0.01)  # Default low frequency

    def _update_transition_frequency(self, transition: str, count: int):
        """Update transition frequency learning."""
        if not hasattr(self, '_transition_frequencies'):
            self._transition_frequencies = {}

        # Exponential moving average for frequency learning
        current_freq = self._transition_frequencies.get(transition, 0.0)
        alpha = 0.1  # Learning rate
        self._transition_frequencies[transition] = current_freq * (1 - alpha) + count * alpha

    def update_anomaly_detection_metrics(self, predicted_anomaly: bool, actual_anomaly: bool,
                                       confidence: float):
        """
        Update anomaly detection metrics with ground truth feedback.

        Args:
            predicted_anomaly: Whether system predicted an anomaly
            actual_anomaly: Ground truth - was there actually an anomaly
            confidence: Confidence score of the prediction (0.0-1.0)
        """
        self.anomaly_detection_history.append((predicted_anomaly, actual_anomaly, confidence))
        self._recalculate_accuracy_metrics()

    def _recalculate_accuracy_metrics(self):
        """Recalculate accuracy metrics based on historical data."""
        if len(self.anomaly_detection_history) < 10:
            return  # Need minimum data for reliable metrics

        history = list(self.anomaly_detection_history)

        # Calculate confusion matrix
        true_positives = sum(1 for pred, actual, _ in history if pred and actual)
        true_negatives = sum(1 for pred, actual, _ in history if not pred and not actual)
        false_positives = sum(1 for pred, actual, _ in history if pred and not actual)
        false_negatives = sum(1 for pred, actual, _ in history if not pred and actual)

        total_predictions = len(history)

        # Calculate precision, recall, F1
        if true_positives + false_positives > 0:
            precision = true_positives / (true_positives + false_positives)
        else:
            precision = 0.0

        if true_positives + false_negatives > 0:
            recall = true_positives / (true_positives + false_negatives)
        else:
            recall = 0.0

        if precision + recall > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0.0

        # Calculate rates
        false_positive_rate = false_positives / total_predictions if total_predictions > 0 else 0.0
        false_negative_rate = false_negatives / total_predictions if total_predictions > 0 else 0.0

        # Calculate temporal stability (consistency of predictions over time)
        recent_predictions = [pred for pred, _, _ in history[-50:]]  # Last 50 predictions
        if recent_predictions:
            stability = 1.0 - (sum(recent_predictions) / len(recent_predictions)) * 2 + 1  # 0=unstable, 1=stable
            stability = max(0.0, min(1.0, stability))
        else:
            stability = 0.5

        # Update metrics
        self.accuracy_metrics.update({
            'anomaly_detection_precision': precision,
            'anomaly_detection_recall': recall,
            'anomaly_detection_f1_score': f1_score,
            'false_positive_rate': false_positive_rate,
            'false_negative_rate': false_negative_rate,
            'temporal_stability_score': stability
        })

    def update_analysis_quality_metrics(self, analysis_result: Dict[str, Any]):
        """
        Update analysis quality metrics based on analysis results.

        Args:
            analysis_result: Result from analyze_correlation_chain
        """
        quality_score = 0.0
        factors = 0

        # Factor 1: Analysis completeness
        required_fields = ['correlation_id', 'chain_length', 'anomaly_score']
        completeness = sum(1 for field in required_fields if field in analysis_result) / len(required_fields)
        quality_score += completeness * 0.4
        factors += 1

        # Factor 2: Data richness
        data_fields = ['event_types', 'decision_patterns', 'impact_profile']
        data_richness = sum(1 for field in data_fields if field in analysis_result and analysis_result[field]) / len(data_fields)
        quality_score += data_richness * 0.3
        factors += 1

        # Factor 3: Analysis time (faster is better, but not too fast)
        analysis_time = analysis_result.get('analysis_duration', 0.0)
        if 0.001 <= analysis_time <= 0.1:  # Reasonable time range
            time_score = 1.0 - abs(analysis_time - 0.01) / 0.09  # Optimal around 0.01s
            quality_score += time_score * 0.3
            factors += 1

        final_quality = quality_score / max(1, factors)
        self.analysis_quality_history.append(final_quality)

        # Update overall semantic coherence score
        if self.analysis_quality_history:
            self.accuracy_metrics['semantic_coherence_score'] = \
                sum(self.analysis_quality_history) / len(self.analysis_quality_history)

    def update_plugin_performance_metrics(self, plugin_name: str, plugin_result: Dict[str, Any]):
        """
        Update performance metrics for a specific plugin.

        Args:
            plugin_name: Name of the plugin
            plugin_result: Result from plugin analysis
        """
        if plugin_name not in self.plugin_performance_metrics:
            self.plugin_performance_metrics[plugin_name] = {
                'analysis_count': 0,
                'avg_anomaly_score': 0.0,
                'avg_execution_time': 0.0,
                'error_count': 0,
                'last_execution_time': 0.0
            }

        metrics = self.plugin_performance_metrics[plugin_name]
        metrics['analysis_count'] += 1

        if 'anomaly_score' in plugin_result:
            # Update running average
            current_avg = metrics['avg_anomaly_score']
            count = metrics['analysis_count']
            new_score = plugin_result['anomaly_score']
            metrics['avg_anomaly_score'] = (current_avg * (count - 1) + new_score) / count

        if 'execution_time' in plugin_result:
            execution_time = plugin_result['execution_time']
            metrics['last_execution_time'] = execution_time
            # Update running average execution time
            current_avg_time = metrics['avg_execution_time']
            count = metrics['analysis_count']
            metrics['avg_execution_time'] = (current_avg_time * (count - 1) + execution_time) / count

        if 'error' in plugin_result:
            metrics['error_count'] += 1

    def get_detailed_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics including plugin performance.

        Returns:
            Dict with comprehensive performance metrics
        """
        base_metrics = self.accuracy_metrics.copy()

        # Add plugin metrics
        base_metrics['plugin_performance'] = self.plugin_performance_metrics.copy()

        # Add historical trends
        if self.anomaly_detection_history:
            recent_history = list(self.anomaly_detection_history)[-100:]  # Last 100
            recent_precision = sum(1 for pred, actual, _ in recent_history if pred == actual) / len(recent_history)
            base_metrics['recent_accuracy_trend'] = recent_precision

        # Add analysis quality metrics
        if self.analysis_quality_history:
            base_metrics['avg_analysis_quality'] = sum(self.analysis_quality_history) / len(self.analysis_quality_history)
            base_metrics['analysis_quality_trend'] = list(self.analysis_quality_history)[-10:]  # Last 10

        return base_metrics

    def _detect_rare_patterns(self, event_types: List[str]) -> float:
        """
        Detect rare or unusual event type combinations using statistical analysis.

        This function is kept for backward compatibility but now uses statistical thresholds.
        """
        if len(event_types) < 2:
            return 0.0

        # Use dynamic thresholds based on historical data
        rarity_score = 0.0

        # Analyze individual event frequencies
        for event_type in event_types:
            freq = self.event_type_frequencies.get(event_type, 0)
            expected_freq = self._get_expected_event_frequency(event_type)

            # Calculate deviation from expected frequency
            if expected_freq > 0:
                deviation = abs(freq - expected_freq) / expected_freq
                if deviation > 2.0:  # Significant deviation
                    rarity_score += min(0.2, deviation * 0.1)
            elif freq == 0:
                # Completely unseen event type
                rarity_score += 0.3

        # Analyze combination patterns
        combination = tuple(sorted(set(event_types)))
        if len(combination) > 1:
            combination_freq = self._get_expected_combination_frequency(combination)
            if combination_freq < 0.05:  # Rare combination
                rarity_score += 0.2

        # Update learning for future analysis
        for event_type in event_types:
            self._update_event_frequency(event_type)

        combination_key = '|'.join(combination)
        self._update_combination_frequency(combination_key)

        return min(1.0, rarity_score)

    def _get_expected_event_frequency(self, event_type: str) -> float:
        """Get expected frequency for event type."""
        if not hasattr(self, '_event_frequency_history'):
            self._event_frequency_history = {}

        history = self._event_frequency_history.get(event_type, [])
        return sum(history) / len(history) if history else 1.0  # Default expectation

    def _update_event_frequency(self, event_type: str):
        """Update event frequency learning."""
        if not hasattr(self, '_event_frequency_history'):
            self._event_frequency_history = {}

        if event_type not in self._event_frequency_history:
            self._event_frequency_history[event_type] = []

        # Add current frequency
        current_freq = self.event_type_frequencies.get(event_type, 0)
        self._event_frequency_history[event_type].append(current_freq)

        # Keep only recent history
        if len(self._event_frequency_history[event_type]) > 100:
            self._event_frequency_history[event_type] = self._event_frequency_history[event_type][-100:]

    def _get_expected_combination_frequency(self, combination: tuple) -> float:
        """Get expected frequency for event combination."""
        if not hasattr(self, '_combination_frequencies'):
            self._combination_frequencies = {}

        combo_key = '|'.join(combination)
        return self._combination_frequencies.get(combo_key, 0.01)  # Default low frequency

    def _update_combination_frequency(self, combination_key: str):
        """Update combination frequency learning."""
        if not hasattr(self, '_combination_frequencies'):
            self._combination_frequencies = {}

        # Simple frequency counting with decay
        current_freq = self._combination_frequencies.get(combination_key, 0)
        self._combination_frequencies[combination_key] = current_freq + 1

    def _update_advanced_pattern_learning(self, chain_semantics: Dict[str, Any],
                                        embeddings: Dict[str, Any]):
        """Update advanced pattern learning with neural adaptation."""
        # Update frequency counters
        for event_type in chain_semantics.get('event_types', []):
            self.event_type_frequencies[event_type] += 1

        for decision_pattern in chain_semantics.get('decision_patterns', []):
            self.decision_pattern_frequencies[decision_pattern] += 1

        # Update impact accumulators
        for param, value in chain_semantics.get('impact_profile', {}).items():
            self.impact_accumulators[param].append(value)

        # Update temporal patterns
        correlation_id = chain_semantics.get('correlation_id', 'unknown')
        timestamp = chain_semantics.get('timestamp', time.time())
        if embeddings.get('sequence_embedding'):
            self.temporal_patterns[correlation_id].append(
                (timestamp, embeddings['sequence_embedding'])
            )

        # Learn semantic patterns with embeddings
        self._learn_advanced_semantic_patterns(chain_semantics, embeddings)

        # Neural network training
        if self.enable_neural_network and self.neural_net and embeddings.get('sequence_embedding'):
            # Create training target based on anomaly score and coherence
            anomaly_score = chain_semantics.get('anomaly_score', 0.0)
            coherence = chain_semantics.get('semantic_coherence', 0.5)

            # Target is inverse of anomaly (normal=1, anomalous=0) modulated by coherence
            target = [max(0.0, 1.0 - anomaly_score) * coherence] * (self.embedding_dim // 4)

            self.neural_net.train_step([embeddings['sequence_embedding']], [target])

        # Update causal relationships
        self._update_causal_relationships(chain_semantics)

    def _learn_advanced_semantic_patterns(self, chain_semantics: Dict[str, Any],
                                        embeddings: Dict[str, Any]):
        """Learn semantic patterns using embeddings and neural features."""
        event_types = tuple(sorted(set(chain_semantics.get('event_types', []))))
        decision_patterns = tuple(sorted(set(chain_semantics.get('decision_patterns', []))))
        category = chain_semantics.get('semantic_category', 'unknown')

        if not event_types:
            return

        # Create pattern key with embedding information
        pattern_key = f"{category}:{event_types}:{decision_patterns}"

        # Create pattern embedding
        sequence_emb = embeddings.get('sequence_embedding', [])
        if sequence_emb:
            pattern_embedding = SemanticEmbedding(
                vector=sequence_emb,
                dimension=self.embedding_dim,
                source_type='pattern',
                timestamp=time.time(),
                metadata={
                    'category': category,
                    'event_types': list(event_types),
                    'decision_patterns': list(decision_patterns),
                    'coherence': chain_semantics.get('semantic_coherence', 0.5)
                }
            )
            self.pattern_embeddings[pattern_key] = pattern_embedding

        # Update or create semantic pattern
        if pattern_key in self.semantic_patterns:
            # Update existing pattern
            pattern = self.semantic_patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_seen = time.time()

            # Update impact profile with neural adaptation
            current_impact = chain_semantics.get('impact_profile', {})
            neural_features = chain_semantics.get('neural_features', [])

            # Adapt impact profile using neural features
            if neural_features:
                adaptation_factor = sum(neural_features) / len(neural_features)
                for param in current_impact:
                    old_value = pattern.impact_profile.get(param, 0.0)
                    new_value = current_impact[param]
                    # Weighted average with adaptation
                    pattern.impact_profile[param] = (
                        old_value * (1.0 - self.adaptation_rate) +
                        new_value * adaptation_factor * self.adaptation_rate
                    )

            # Update confidence based on neural coherence
            coherence = chain_semantics.get('semantic_coherence', 0.5)
            pattern.confidence = min(1.0, pattern.confidence + coherence * 0.1)

        else:
            # Create new pattern
            if len(self.semantic_patterns) < self.max_patterns:
                impact_profile = chain_semantics.get('impact_profile', {})
                coherence = chain_semantics.get('semantic_coherence', 0.5)

                self.semantic_patterns[pattern_key] = SemanticPattern(
                    pattern_id=pattern_key,
                    event_types=list(event_types),
                    decision_patterns=list(decision_patterns),
                    impact_profile=impact_profile.copy(),
                    frequency=1,
                    confidence=coherence,  # Start with coherence as confidence
                    last_seen=time.time(),
                    metadata={
                        'category': category,
                        'neural_features': chain_semantics.get('neural_features', []),
                        'embedding_key': pattern_key if sequence_emb else None
                    }
                )

    def _update_causal_relationships(self, chain_semantics: Dict[str, Any]):
        """Update causal relationship strengths based on chain analysis."""
        causal_insights = chain_semantics.get('causal_insights', {})
        event_types = chain_semantics.get('event_types', [])
        decision_patterns = chain_semantics.get('decision_patterns', [])

        # Strengthen relationships based on successful processing
        causal_strength = causal_insights.get('causal_strength', 0.0)

        if causal_strength > 0.7:  # Strong causal chain
            for event_type in event_types:
                for decision_pattern in decision_patterns:
                    key = f"{event_type}→{decision_pattern}"
                    current_strength = self.causal_relationships[event_type].get(decision_pattern, 0.0)
                    # Exponential moving average
                    self.causal_relationships[event_type][decision_pattern] = (
                        current_strength * 0.9 + causal_strength * 0.1
                    )

    def _learn_semantic_patterns(self, chain_semantics: Dict[str, Any]):
        """Learn semantic patterns from chain analysis."""
        event_types = tuple(sorted(set(chain_semantics.get('event_types', []))))
        decision_patterns = tuple(sorted(set(chain_semantics.get('decision_patterns', []))))
        category = chain_semantics.get('semantic_category', 'unknown')

        if not event_types:
            return

        # Create pattern key
        pattern_key = f"{category}:{event_types}:{decision_patterns}"

        if pattern_key in self.semantic_patterns:
            # Update existing pattern
            pattern = self.semantic_patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_seen = time.time()

            # Update impact profile (moving average)
            current_impact = chain_semantics.get('impact_profile', {})
            for param in set(pattern.impact_profile.keys()) | set(current_impact.keys()):
                old_value = pattern.impact_profile.get(param, 0.0)
                new_value = current_impact.get(param, 0.0)
                pattern.impact_profile[param] = (old_value * (pattern.frequency - 1) + new_value) / pattern.frequency

            # Update confidence based on frequency and consistency
            pattern.confidence = min(1.0, pattern.frequency / 10.0)

        else:
            # Create new pattern
            if len(self.semantic_patterns) < self.max_patterns:
                impact_profile = chain_semantics.get('impact_profile', {})
                self.semantic_patterns[pattern_key] = SemanticPattern(
                    pattern_id=pattern_key,
                    event_types=list(event_types),
                    decision_patterns=list(decision_patterns),
                    impact_profile=impact_profile.copy(),
                    frequency=1,
                    confidence=0.1,  # Start low, build up
                    last_seen=time.time(),
                    metadata={'category': category}
                )

    def analyze_system_health(self, recent_chains: List[Dict] = None) -> SystemHealthProfile:
        """
        Analyze overall system health based on semantic patterns.

        Args:
            recent_chains: Recent correlation chains to analyze

        Returns:
            System health profile
        """
        if recent_chains is None:
            recent_chains = list(self.correlation_chains.values())[-100:]  # Last 100 chains

        # Analyze energy stability
        energy_impacts = []
        stability_impacts = []
        cognitive_events = []
        adaptation_patterns = []

        for chain in recent_chains:
            for entry in chain:
                if entry.get('stage') == 'meaning':
                    impact = entry.get('data', {}).get('impact', {})
                    if 'energy' in impact:
                        energy_impacts.append(impact['energy'])
                    if 'stability' in impact:
                        stability_impacts.append(impact['stability'])

                elif entry.get('stage') == 'event':
                    event_type = entry.get('event_type', '')
                    if any(cat in ['cognitive', 'existential'] for cat, types in self.EVENT_CATEGORIES.items() if event_type in types):
                        cognitive_events.append(event_type)

                elif entry.get('stage') == 'decision':
                    pattern = entry.get('data', {}).get('pattern', '')
                    adaptation_patterns.append(pattern)

        # Calculate health metrics
        energy_stability = self._calculate_energy_stability(energy_impacts)
        cognitive_coherence = self._calculate_cognitive_coherence(cognitive_events)
        adaptation_efficiency = self._calculate_adaptation_efficiency(adaptation_patterns)
        memory_integrity = self._calculate_memory_integrity(recent_chains)

        # Overall health is weighted average
        overall_health = (
            energy_stability * 0.3 +
            cognitive_coherence * 0.3 +
            adaptation_efficiency * 0.2 +
            memory_integrity * 0.2
        )

        # Identify risk factors
        risk_factors = []
        recommendations = []

        if energy_stability < 0.5:
            risk_factors.append("Low energy stability")
            recommendations.append("Consider energy management optimization")

        if cognitive_coherence < 0.6:
            risk_factors.append("Poor cognitive coherence")
            recommendations.append("Review cognitive event processing")

        if adaptation_efficiency < 0.5:
            risk_factors.append("Inefficient adaptation patterns")
            recommendations.append("Optimize decision-making algorithms")

        if memory_integrity < 0.7:
            risk_factors.append("Memory integrity issues")
            recommendations.append("Check memory consolidation processes")

        return SystemHealthProfile(
            energy_stability=energy_stability,
            cognitive_coherence=cognitive_coherence,
            adaptation_efficiency=adaptation_efficiency,
            memory_integrity=memory_integrity,
            overall_health=overall_health,
            risk_factors=risk_factors,
            recommendations=recommendations
        )

    def _calculate_energy_stability(self, energy_impacts: List[float]) -> float:
        """Calculate energy stability score."""
        if not energy_impacts:
            return 0.5  # Neutral score

        # Energy stability is inverse of impact volatility
        if len(energy_impacts) < 3:
            return 0.5

        try:
            volatility = statistics.stdev(energy_impacts)
            # Lower volatility = higher stability
            stability = max(0.0, 1.0 - volatility * 2.0)
            return stability
        except statistics.StatisticsError:
            return 0.5

    def _calculate_cognitive_coherence(self, cognitive_events: List[str]) -> float:
        """Calculate cognitive coherence based on event patterns."""
        if not cognitive_events:
            return 0.5

        # Coherence based on event type diversity and consistency
        unique_events = len(set(cognitive_events))
        total_events = len(cognitive_events)

        # Balance between diversity and focus
        diversity_ratio = unique_events / max(1, total_events)

        # Ideal diversity is around 0.3-0.7
        if 0.3 <= diversity_ratio <= 0.7:
            coherence = 1.0
        elif diversity_ratio < 0.3:
            coherence = diversity_ratio / 0.3  # Too focused
        else:
            coherence = (1.0 - diversity_ratio) / 0.3  # Too scattered

        return max(0.0, min(1.0, coherence))

    def _calculate_adaptation_efficiency(self, adaptation_patterns: List[str]) -> float:
        """Calculate adaptation efficiency from decision patterns."""
        if not adaptation_patterns:
            return 0.5

        # Efficiency based on pattern diversity and common successful patterns
        pattern_counts = Counter(adaptation_patterns)
        total_patterns = len(adaptation_patterns)
        unique_patterns = len(pattern_counts)

        # Prefer moderate pattern diversity (not too rigid, not too chaotic)
        diversity_score = 1.0 - abs(unique_patterns / total_patterns - 0.4) / 0.4

        # Bonus for using known effective patterns
        effective_patterns = {'absorb', 'dampen', 'amplify'}  # Assume these are effective
        effective_usage = sum(count for pattern, count in pattern_counts.items()
                            if pattern in effective_patterns) / total_patterns

        efficiency = (diversity_score * 0.6 + effective_usage * 0.4)
        return max(0.0, min(1.0, efficiency))

    def _calculate_memory_integrity(self, recent_chains: List[List[Dict]]) -> float:
        """Calculate memory integrity based on chain consistency."""
        if not recent_chains:
            return 0.5

        # Check for chain completeness and consistency
        complete_chains = 0
        total_chains = len(recent_chains)

        for chain in recent_chains:
            stages = {entry.get('stage') for entry in chain}
            required_stages = {'event', 'meaning', 'decision', 'action'}
            if required_stages.issubset(stages):
                complete_chains += 1

        integrity = complete_chains / total_chains
        return max(0.0, min(1.0, integrity))

    def detect_anomalies(self, analysis_results: Dict[str, Any]) -> List[BehavioralAnomaly]:
        """
        Detect behavioral anomalies from analysis results.

        Args:
            analysis_results: Results from chain analysis

        Returns:
            List of detected anomalies
        """
        anomalies = []
        anomaly_score = analysis_results.get('anomaly_score', 0.0)

        if anomaly_score > self.anomaly_threshold:
            anomaly = BehavioralAnomaly(
                anomaly_id=f"anomaly_{int(time.time()*1000)}",
                anomaly_type='pattern_deviation',
                severity=anomaly_score,
                description=f"Unusual behavioral pattern detected (score: {anomaly_score:.2f})",
                timestamp=time.time(),
                correlation_ids=[analysis_results.get('correlation_id', 'unknown')],
                evidence={
                    'anomaly_score': anomaly_score,
                    'semantic_category': analysis_results.get('semantic_category', 'unknown'),
                    'behavioral_context': analysis_results.get('behavioral_context', {})
                }
            )
            anomalies.append(anomaly)
            self.behavioral_anomalies.append(anomaly)

        return anomalies

    def get_semantic_insights(self) -> Dict[str, Any]:
        """
        Get comprehensive semantic insights from analysis.

        Returns:
            Dictionary with semantic insights
        """
        insights = {
            'semantic_patterns': {
                pattern_id: {
                    'frequency': pattern.frequency,
                    'confidence': pattern.confidence,
                    'impact_profile': pattern.impact_profile,
                    'category': pattern.metadata.get('category', 'unknown')
                }
                for pattern_id, pattern in self.semantic_patterns.items()
            },
            'behavioral_anomalies': [
                {
                    'type': anomaly.anomaly_type,
                    'severity': anomaly.severity,
                    'description': anomaly.description,
                    'timestamp': anomaly.timestamp
                }
                for anomaly in self.behavioral_anomalies[-10:]  # Last 10 anomalies
            ],
            'system_health': self.analyze_system_health(),
            'event_type_distribution': dict(self.event_type_frequencies.most_common(10)),
            'decision_pattern_distribution': dict(self.decision_pattern_frequencies.most_common(5)),
            'analysis_timestamp': time.time()
        }

        return insights

    def analyze_behavioral_trends(self, time_window_seconds: float = 3600.0) -> Dict[str, Any]:
        """
        Анализ поведенческих трендов в заданном временном окне.

        Args:
            time_window_seconds: Временное окно для анализа (секунды)

        Returns:
            Анализ поведенческих трендов
        """
        current_time = time.time()
        window_start = current_time - time_window_seconds

        # Filter recent chains
        recent_chains = {}
        for correlation_id, chain in self.correlation_chains.items():
            if chain and chain[0].get('timestamp', 0) >= window_start:
                recent_chains[correlation_id] = chain

        if not recent_chains:
            return {
                'trend_analysis': 'insufficient_data',
                'time_window': time_window_seconds,
                'chains_analyzed': 0
            }

        # Analyze trends
        trends = {
            'event_type_trends': self._analyze_event_type_trends(recent_chains),
            'decision_pattern_trends': self._analyze_decision_trends(recent_chains),
            'impact_trends': self._analyze_impact_trends(recent_chains),
            'processing_efficiency_trends': self._analyze_processing_efficiency_trends(recent_chains),
            'anomaly_trends': self._analyze_anomaly_trends(recent_chains, window_start),
            'overall_trend': 'stable',  # Will be updated based on analysis
            'time_window': time_window_seconds,
            'chains_analyzed': len(recent_chains),
            'analysis_timestamp': current_time
        }

        # Determine overall trend
        trends['overall_trend'] = self._determine_overall_trend(trends)

        return trends

    def _analyze_event_type_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов типов событий."""
        event_timeline = defaultdict(lambda: defaultdict(int))

        for chain in chains.values():
            for entry in chain:
                if entry.get('stage') == 'event':
                    timestamp = entry.get('timestamp', 0)
                    event_type = entry.get('event_type', 'unknown')

                    # Group by 5-minute intervals
                    interval = int(timestamp // 300) * 300
                    event_timeline[interval][event_type] += 1

        # Calculate trends for each event type
        trends = {}
        intervals = sorted(event_timeline.keys())

        if len(intervals) >= 3:
            for event_type in set():
                for interval_data in event_timeline.values():
                    if event_type in interval_data:
                        break
                else:
                    continue  # Skip event types not seen

                counts = [event_timeline[interval].get(event_type, 0) for interval in intervals]

                # Simple linear trend (slope)
                if len(counts) >= 2:
                    trend_slope = self._calculate_trend_slope(counts)
                    trends[event_type] = {
                        'slope': trend_slope,
                        'direction': 'increasing' if trend_slope > 0.1 else 'decreasing' if trend_slope < -0.1 else 'stable',
                        'volatility': self._calculate_volatility(counts),
                        'recent_average': sum(counts[-3:]) / min(3, len(counts)) if counts else 0
                    }

        return trends

    def _analyze_decision_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов паттернов решений."""
        decision_timeline = defaultdict(lambda: defaultdict(int))

        for chain in chains.values():
            for entry in chain:
                if entry.get('stage') == 'decision':
                    timestamp = entry.get('timestamp', 0)
                    pattern = entry.get('data', {}).get('pattern', 'unknown')

                    interval = int(timestamp // 300) * 300
                    decision_timeline[interval][pattern] += 1

        # Analyze decision pattern effectiveness
        effectiveness = {}
        for pattern in set():
            for interval_data in decision_timeline.values():
                if pattern in interval_data:
                    break
            else:
                continue

            # Calculate effectiveness based on subsequent feedback
            pattern_effectiveness = self._calculate_decision_effectiveness(pattern, chains)
            effectiveness[pattern] = pattern_effectiveness

        return {
            'pattern_distribution': dict(sum((Counter(interval) for interval in decision_timeline.values()), Counter())),
            'effectiveness_scores': effectiveness
        }

    def _analyze_impact_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов воздействий на состояние."""
        impact_timeline = defaultdict(lambda: defaultdict(list))

        for chain in chains.values():
            for entry in chain:
                if entry.get('stage') == 'meaning':
                    timestamp = entry.get('timestamp', 0)
                    impact = entry.get('data', {}).get('impact', {})

                    interval = int(timestamp // 300) * 300
                    for param, value in impact.items():
                        impact_timeline[interval][param].append(value)

        # Calculate impact trends
        trends = {}
        intervals = sorted(impact_timeline.keys())

        for param in ['energy', 'integrity', 'stability']:
            param_impacts = []
            for interval in intervals:
                interval_impacts = impact_timeline[interval].get(param, [])
                if interval_impacts:
                    param_impacts.append(sum(interval_impacts) / len(interval_impacts))

            if len(param_impacts) >= 3:
                trends[param] = {
                    'slope': self._calculate_trend_slope(param_impacts),
                    'volatility': self._calculate_volatility(param_impacts),
                    'recent_average': sum(param_impacts[-3:]) / 3,
                    'extremes': {
                        'min': min(param_impacts),
                        'max': max(param_impacts)
                    }
                }

        return trends

    def _analyze_processing_efficiency_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов эффективности обработки."""
        efficiency_metrics = []

        for chain in chains.values():
            if not chain:
                continue

            # Calculate processing time for complete chains
            stages = {entry.get('stage') for entry in chain}
            if {'event', 'meaning', 'decision', 'action'}.issubset(stages):
                timestamps = [entry.get('timestamp', 0) for entry in chain if entry.get('timestamp')]
                if len(timestamps) >= 2:
                    processing_time = max(timestamps) - min(timestamps)
                    completeness = len(stages) / 5.0  # 5 stages total
                    efficiency = completeness / max(processing_time, 0.001)  # Avoid division by zero
                    efficiency_metrics.append({
                        'processing_time': processing_time,
                        'efficiency': efficiency,
                        'stages_completed': len(stages),
                        'timestamp': min(timestamps)
                    })

        if not efficiency_metrics:
            return {'trend': 'no_complete_chains'}

        # Analyze efficiency trends
        efficiencies = [m['efficiency'] for m in efficiency_metrics]
        processing_times = [m['processing_time'] for m in efficiency_metrics]

        return {
            'efficiency_trend': {
                'slope': self._calculate_trend_slope(efficiencies),
                'average': sum(efficiencies) / len(efficiencies),
                'volatility': self._calculate_volatility(efficiencies)
            },
            'processing_time_trend': {
                'slope': self._calculate_trend_slope(processing_times),
                'average': sum(processing_times) / len(processing_times),
                'p95': sorted(processing_times)[int(len(processing_times) * 0.95)] if processing_times else 0
            },
            'complete_chains': len(efficiency_metrics)
        }

    def _analyze_anomaly_trends(self, chains: Dict[str, List[Dict]], window_start: float) -> Dict[str, Any]:
        """Анализ трендов аномалий."""
        recent_anomalies = [a for a in self.behavioral_anomalies if a.timestamp >= window_start]

        if not recent_anomalies:
            return {'anomaly_rate': 0.0, 'trend': 'normal'}

        anomaly_rate = len(recent_anomalies) / len(chains)

        # Group anomalies by time intervals
        anomaly_timeline = defaultdict(int)
        for anomaly in recent_anomalies:
            interval = int(anomaly.timestamp // 300) * 300
            anomaly_timeline[interval] += 1

        intervals = sorted(anomaly_timeline.keys())
        counts = [anomaly_timeline[interval] for interval in intervals]

        return {
            'anomaly_rate': anomaly_rate,
            'trend_slope': self._calculate_trend_slope(counts) if len(counts) >= 2 else 0.0,
            'severity_distribution': {
                'low': len([a for a in recent_anomalies if a.severity < 0.5]),
                'medium': len([a for a in recent_anomalies if 0.5 <= a.severity < 0.8]),
                'high': len([a for a in recent_anomalies if a.severity >= 0.8])
            },
            'total_anomalies': len(recent_anomalies)
        }

    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate simple linear trend slope."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))

        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(values) / n

        # Calculate slope
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, values))
        denominator = sum((xi - mean_x) ** 2 for xi in x)

        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (standard deviation normalized by mean)."""
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

    def _calculate_decision_effectiveness(self, pattern: str, chains: Dict[str, List[Dict]]) -> float:
        """Calculate effectiveness score for a decision pattern."""
        pattern_chains = []
        for chain in chains.values():
            for entry in chain:
                if (entry.get('stage') == 'decision' and
                    entry.get('data', {}).get('pattern') == pattern):
                    pattern_chains.append(chain)
                    break

        if not pattern_chains:
            return 0.5  # Neutral score

        # Simple effectiveness based on chain completeness and feedback
        effectiveness_scores = []
        for chain in pattern_chains:
            stages = {entry.get('stage') for entry in chain}

            # Completeness score
            required_stages = {'event', 'meaning', 'decision', 'action'}
            completeness = len(stages.intersection(required_stages)) / len(required_stages)

            # Feedback score (simplified)
            has_feedback = 'feedback' in stages
            feedback_bonus = 0.2 if has_feedback else 0.0

            score = completeness + feedback_bonus
            effectiveness_scores.append(min(1.0, score))

        return sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0.5

    def _determine_overall_trend(self, trends: Dict[str, Any]) -> str:
        """Determine overall behavioral trend."""
        anomaly_trend = trends.get('anomaly_trends', {})
        efficiency_trend = trends.get('processing_efficiency_trends', {})
        impact_trends = trends.get('impact_trends', {})

        # Check for concerning signals
        concerning_signals = 0

        # High anomaly rate increasing
        if anomaly_trend.get('anomaly_rate', 0) > 0.1 and anomaly_trend.get('trend_slope', 0) > 0:
            concerning_signals += 1

        # Declining processing efficiency
        if efficiency_trend.get('efficiency_trend', {}).get('slope', 0) < -0.1:
            concerning_signals += 1

        # Volatile state impacts
        for param_trend in impact_trends.values():
            if param_trend.get('volatility', 0) > 0.5:
                concerning_signals += 1
                break

        if concerning_signals >= 2:
            return 'concerning'
        elif concerning_signals == 1:
            return 'unstable'
        else:
            return 'stable'

    def predict_behavioral_risks(self, prediction_horizon: int = 5) -> Dict[str, Any]:
        """
        Predict potential behavioral risks based on current trends.

        Args:
            prediction_horizon: Number of future intervals to predict

        Returns:
            Risk predictions and recommendations
        """
        # Get recent trends
        recent_trends = self.analyze_behavioral_trends(time_window_seconds=1800)  # Last 30 minutes

        predictions = {
            'risk_assessment': {},
            'predicted_anomalies': [],
            'recommendations': [],
            'confidence': 0.0,
            'prediction_horizon': prediction_horizon
        }

        # Predict based on anomaly trends
        anomaly_trend = recent_trends.get('anomaly_trends', {})
        if anomaly_trend.get('trend_slope', 0) > 0.5:
            predictions['predicted_anomalies'].append({
                'type': 'anomaly_rate_increase',
                'severity': 'high',
                'description': 'Увеличение частоты аномалий может указывать на проблемы',
                'timeframe': f'следующие {prediction_horizon} интервалов'
            })
            predictions['risk_assessment']['anomaly_risk'] = 'high'
            predictions['recommendations'].append('Рекомендуется проверить конфигурацию системы')

        # Predict based on efficiency trends
        efficiency_trend = recent_trends.get('processing_efficiency_trends', {})
        efficiency_slope = efficiency_trend.get('efficiency_trend', {}).get('slope', 0)

        if efficiency_slope < -0.2:
            predictions['predicted_anomalies'].append({
                'type': 'efficiency_decline',
                'severity': 'medium',
                'description': 'Снижение эффективности обработки может привести к задержкам',
                'timeframe': f'следующие {prediction_horizon} интервалов'
            })
            predictions['risk_assessment']['efficiency_risk'] = 'medium'
            predictions['recommendations'].append('Оптимизировать алгоритмы обработки')

        # Predict based on state impact volatility
        impact_trends = recent_trends.get('impact_trends', {})
        high_volatility_params = [
            param for param, trend in impact_trends.items()
            if trend.get('volatility', 0) > 0.7
        ]

        if high_volatility_params:
            predictions['predicted_anomalies'].append({
                'type': 'state_instability',
                'severity': 'medium',
                'description': f'Высокая волатильность параметров: {", ".join(high_volatility_params)}',
                'timeframe': f'следующие {prediction_horizon} интервалов'
            })
            predictions['risk_assessment']['stability_risk'] = 'medium'
            predictions['recommendations'].append('Стабилизировать параметры состояния')

        # Overall risk assessment
        risk_levels = predictions['risk_assessment'].values()
        if 'high' in risk_levels:
            predictions['overall_risk'] = 'high'
            predictions['confidence'] = 0.8
        elif 'medium' in risk_levels:
            predictions['overall_risk'] = 'medium'
            predictions['confidence'] = 0.6
        else:
            predictions['overall_risk'] = 'low'
            predictions['confidence'] = 0.4

        return predictions

    def analyze_state_context(self, state_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze contextual relationships between state parameters.

        Args:
            state_data: Current state data (energy, stability, integrity, etc.)

        Returns:
            Contextual state analysis
        """
        if state_data is None:
            # Use accumulated impact data as proxy for state analysis
            state_data = {}
            for param in ['energy', 'integrity', 'stability']:
                impacts = self.impact_accumulators.get(param, [])
                if impacts:
                    # Use recent average impact as proxy for current state
                    recent_impacts = impacts[-10:] if len(impacts) > 10 else impacts
                    state_data[param] = sum(recent_impacts) / len(recent_impacts)

        if not state_data:
            return {'analysis': 'insufficient_state_data'}

        context_analysis = {
            'state_profile': self._create_state_profile(state_data),
            'interactions': self._analyze_state_interactions(state_data),
            'resilience_indicators': self._calculate_resilience_indicators(state_data),
            'adaptation_capacity': self._assess_adaptation_capacity(state_data),
            'risk_factors': self._identify_state_risks(state_data),
            'recommendations': self._generate_state_recommendations(state_data),
            'temporal_patterns': self._analyze_state_temporal_patterns(),
            'timestamp': time.time()
        }

        return context_analysis

    def _create_state_profile(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive profile of the current system state."""
        profile = {}

        # Energy profile
        energy = state_data.get('energy', 50.0)
        profile['energy_profile'] = {
            'level': energy,
            'status': 'high' if energy > 70 else 'medium' if energy > 30 else 'low',
            'stability_risk': 'high' if energy < 20 else 'medium' if energy < 40 else 'low'
        }

        # Integrity profile
        integrity = state_data.get('integrity', 0.8)
        profile['integrity_profile'] = {
            'level': integrity,
            'status': 'robust' if integrity > 0.8 else 'compromised' if integrity > 0.5 else 'critical',
            'coherence': 'high' if integrity > 0.9 else 'medium' if integrity > 0.7 else 'low'
        }

        # Stability profile
        stability = state_data.get('stability', 0.8)
        profile['stability_profile'] = {
            'level': stability,
            'status': 'stable' if stability > 0.8 else 'unstable' if stability > 0.5 else 'chaotic',
            'predictability': 'high' if stability > 0.9 else 'medium' if stability > 0.7 else 'low'
        }

        # Subjective time profile
        subj_time = state_data.get('subjective_time', 0.0)
        profile['temporal_profile'] = {
            'subjective_time': subj_time,
            'time_dilation': 'normal',  # Would need more context to determine
            'experience_intensity': 'moderate'  # Would need event correlation
        }

        # Overall system profile
        profile['system_profile'] = {
            'overall_health': self._calculate_overall_health_score(state_data),
            'dominant_state': self._determine_dominant_state(state_data),
            'system_phase': self._determine_system_phase(state_data)
        }

        return profile

    def _analyze_state_interactions(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interactions between different state parameters."""
        interactions = {}

        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Energy-Integrity interaction
        energy_integrity_corr = self._calculate_correlation(
            self.impact_accumulators.get('energy', []),
            self.impact_accumulators.get('integrity', [])
        )
        interactions['energy_integrity'] = {
            'correlation': energy_integrity_corr,
            'relationship': 'reinforcing' if energy_integrity_corr > 0.3 else 'neutral' if energy_integrity_corr > -0.3 else 'conflicting',
            'description': 'Energy and integrity tend to change together' if abs(energy_integrity_corr) > 0.3 else 'Energy and integrity changes are independent'
        }

        # Stability-Energy interaction
        stability_energy_corr = self._calculate_correlation(
            self.impact_accumulators.get('stability', []),
            self.impact_accumulators.get('energy', [])
        )
        interactions['stability_energy'] = {
            'correlation': stability_energy_corr,
            'relationship': 'supportive' if stability_energy_corr > 0.2 else 'challenging',
            'description': 'Stability supports energy maintenance' if stability_energy_corr > 0.2 else 'Stability may drain energy resources'
        }

        # Integrity-Stability interaction
        integrity_stability_corr = self._calculate_correlation(
            self.impact_accumulators.get('integrity', []),
            self.impact_accumulators.get('stability', [])
        )
        interactions['integrity_stability'] = {
            'correlation': integrity_stability_corr,
            'relationship': 'complementary' if integrity_stability_corr > 0.4 else 'independent',
            'description': 'Integrity and stability reinforce each other' if integrity_stability_corr > 0.4 else 'Integrity and stability operate somewhat independently'
        }

        # Three-way interaction analysis
        interactions['system_dynamics'] = self._analyze_three_way_dynamics(energy, integrity, stability)

        return interactions

    def _calculate_resilience_indicators(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resilience indicators based on state parameters."""
        indicators = {}

        # Recovery capacity (based on energy and integrity interaction)
        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)

        recovery_capacity = (energy / 100.0) * integrity
        indicators['recovery_capacity'] = {
            'score': recovery_capacity,
            'level': 'high' if recovery_capacity > 0.7 else 'medium' if recovery_capacity > 0.4 else 'low',
            'description': 'Ability to recover from adverse events'
        }

        # Adaptation flexibility (based on stability range and integrity)
        stability = state_data.get('stability', 0.8)
        stability_range = self._calculate_stability_range()

        adaptation_flexibility = stability * integrity * (1 + stability_range)
        indicators['adaptation_flexibility'] = {
            'score': min(1.0, adaptation_flexibility),
            'level': 'high' if adaptation_flexibility > 0.8 else 'medium' if adaptation_flexibility > 0.5 else 'low',
            'description': 'Ability to adapt to changing conditions'
        }

        # Stress tolerance (inverse of volatility)
        state_volatility = self._calculate_overall_state_volatility()
        stress_tolerance = 1.0 - min(1.0, state_volatility)
        indicators['stress_tolerance'] = {
            'score': stress_tolerance,
            'level': 'high' if stress_tolerance > 0.7 else 'medium' if stress_tolerance > 0.4 else 'low',
            'description': 'Tolerance for environmental stress'
        }

        # Overall resilience
        overall_resilience = (recovery_capacity + adaptation_flexibility + stress_tolerance) / 3.0
        indicators['overall_resilience'] = {
            'score': overall_resilience,
            'level': 'resilient' if overall_resilience > 0.7 else 'vulnerable' if overall_resilience > 0.4 else 'fragile'
        }

        return indicators

    def _assess_adaptation_capacity(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the system's capacity for adaptation."""
        capacity = {}

        # Learning capacity (based on integrity and recent experience)
        integrity = state_data.get('integrity', 0.8)
        recent_experience = len([c for c in self.correlation_chains.values()
                               if any(e.get('timestamp', 0) > time.time() - 3600 for e in c)])

        learning_capacity = integrity * min(1.0, recent_experience / 50.0)
        capacity['learning_capacity'] = {
            'score': learning_capacity,
            'level': 'strong' if learning_capacity > 0.7 else 'moderate' if learning_capacity > 0.4 else 'limited',
            'factors': ['system_integrity', 'experience_accumulation']
        }

        # Response flexibility (based on decision pattern diversity)
        decision_patterns = list(self.decision_pattern_frequencies.keys())
        pattern_diversity = len(decision_patterns) / max(1, len(self.decision_pattern_frequencies))

        response_flexibility = pattern_diversity * 0.8  # Scale down slightly
        capacity['response_flexibility'] = {
            'score': response_flexibility,
            'level': 'flexible' if response_flexibility > 0.6 else 'moderate' if response_flexibility > 0.3 else 'rigid',
            'factors': ['decision_pattern_diversity', 'behavioral_repertoire']
        }

        # Recovery speed (based on energy recovery patterns)
        energy_impacts = self.impact_accumulators.get('energy', [])
        if len(energy_impacts) >= 5:
            # Look for recovery patterns (positive impacts after negative)
            recovery_instances = 0
            for i in range(1, len(energy_impacts)):
                if energy_impacts[i-1] < -0.1 and energy_impacts[i] > 0.05:
                    recovery_instances += 1

            recovery_rate = recovery_instances / max(1, len(energy_impacts) - 1)
            recovery_speed = recovery_rate * 2.0  # Scale up for visibility
        else:
            recovery_speed = 0.5  # Neutral assumption

        capacity['recovery_speed'] = {
            'score': min(1.0, recovery_speed),
            'level': 'fast' if recovery_speed > 0.7 else 'moderate' if recovery_speed > 0.4 else 'slow',
            'factors': ['energy_recovery_patterns', 'adaptation_effectiveness']
        }

        return capacity

    def _identify_state_risks(self, state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential risks based on state analysis."""
        risks = []

        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Critical energy risk
        if energy < 20:
            risks.append({
                'risk_type': 'energy_critical',
                'severity': 'high',
                'description': 'Energy levels critically low, system may become unresponsive',
                'indicators': [f'energy={energy:.1f}'],
                'mitigation': 'Prioritize energy recovery, reduce activity'
            })

        # Integrity degradation risk
        if integrity < 0.4:
            risks.append({
                'risk_type': 'integrity_compromised',
                'severity': 'high',
                'description': 'System integrity severely compromised',
                'indicators': [f'integrity={integrity:.2f}'],
                'mitigation': 'Focus on integrity restoration, avoid complex operations'
            })

        # Instability risk
        stability_volatility = self._calculate_stability_range()
        if stability < 0.5 or stability_volatility > 0.8:
            risks.append({
                'risk_type': 'behavioral_instability',
                'severity': 'medium',
                'description': 'System behavior is unstable or unpredictable',
                'indicators': [f'stability={stability:.2f}', f'volatility={stability_volatility:.2f}'],
                'mitigation': 'Stabilize operations, reduce environmental complexity'
            })

        # Cascade risk (multiple parameters degraded)
        degraded_count = sum(1 for val in [energy < 30, integrity < 0.6, stability < 0.6] if val)
        if degraded_count >= 2:
            risks.append({
                'risk_type': 'cascade_failure',
                'severity': 'high',
                'description': 'Multiple state parameters degraded, risk of cascade failure',
                'indicators': [f'{degraded_count}_parameters_degraded'],
                'mitigation': 'Comprehensive system stabilization required'
            })

        return risks

    def _generate_state_recommendations(self, state_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on state analysis."""
        recommendations = []

        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Energy recommendations
        if energy < 40:
            recommendations.append("Увеличить фокус на восстановлении энергии")
        elif energy > 80:
            recommendations.append("Энергия на высоком уровне - можно увеличить активность")

        # Integrity recommendations
        if integrity < 0.7:
            recommendations.append("Приоритет - восстановление целостности системы")
        else:
            recommendations.append("Целостность в хорошем состоянии - поддерживать стабильность")

        # Stability recommendations
        stability_volatility = self._calculate_stability_range()
        if stability_volatility > 0.6:
            recommendations.append("Снизить волатильность - стабилизировать поведенческие паттерны")

        # Interaction-based recommendations
        interactions = self._analyze_state_interactions(state_data)
        energy_integrity = interactions.get('energy_integrity', {})

        if energy_integrity.get('correlation', 0) < -0.5:
            recommendations.append("Разрешить конфликт между энергией и целостностью - сбалансировать приоритеты")

        # Overall system recommendations
        health_score = self._calculate_overall_health_score(state_data)
        if health_score < 0.5:
            recommendations.append("Общее состояние системы требует внимания - начать восстановление")
        elif health_score > 0.8:
            recommendations.append("Система в отличном состоянии - можно экспериментировать с новыми паттернами")

        return recommendations

    def _analyze_state_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns in state evolution."""
        patterns = {}

        # Analyze energy patterns over time
        energy_impacts = list(self.impact_accumulators.get('energy', []))
        if len(energy_impacts) >= 10:
            patterns['energy_patterns'] = self._detect_temporal_patterns(energy_impacts, 'energy')

        # Analyze integrity patterns
        integrity_impacts = list(self.impact_accumulators.get('integrity', []))
        if len(integrity_impacts) >= 10:
            patterns['integrity_patterns'] = self._detect_temporal_patterns(integrity_impacts, 'integrity')

        # Analyze stability patterns
        stability_impacts = list(self.impact_accumulators.get('stability', []))
        if len(stability_impacts) >= 10:
            patterns['stability_patterns'] = self._detect_temporal_patterns(stability_impacts, 'stability')

        # Cross-parameter temporal correlations
        if all(len(self.impact_accumulators.get(param, [])) >= 10 for param in ['energy', 'integrity', 'stability']):
            patterns['cross_parameter_patterns'] = self._analyze_cross_parameter_temporal_patterns()

        return patterns

    def _detect_temporal_patterns(self, values: List[float], param_name: str) -> Dict[str, Any]:
        """Detect temporal patterns in a parameter's values."""
        if len(values) < 5:
            return {'pattern': 'insufficient_data'}

        # Simple pattern detection
        patterns = {
            'trend': 'stable',
            'volatility': self._calculate_volatility(values),
            'cyclical': False,
            'recovery_instances': 0
        }

        # Trend analysis
        if len(values) >= 3:
            slope = self._calculate_trend_slope(values)
            if slope > 0.01:
                patterns['trend'] = 'improving'
            elif slope < -0.01:
                patterns['trend'] = 'degrading'
            else:
                patterns['trend'] = 'stable'

        # Recovery pattern detection
        for i in range(1, len(values)):
            if values[i-1] < -0.05 and values[i] > 0.05:
                patterns['recovery_instances'] += 1

        # Simple cyclical detection (very basic)
        if len(values) >= 10:
            # Look for repeating patterns in chunks
            chunk_size = 5
            chunks = [values[i:i+chunk_size] for i in range(0, len(values)-chunk_size+1, chunk_size)]
            if len(chunks) >= 3:
                # Very simple similarity check
                similarities = []
                for i in range(len(chunks)-1):
                    similarity = self._calculate_sequence_similarity(chunks[i], chunks[i+1])
                    similarities.append(similarity)

                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                patterns['cyclical'] = avg_similarity > 0.7

        return patterns

    def _analyze_cross_parameter_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal relationships between different parameters."""
        patterns = {}

        # Get aligned time series (simplified - assume same length)
        energy = list(self.impact_accumulators.get('energy', []))
        integrity = list(self.impact_accumulators.get('integrity', []))
        stability = list(self.impact_accumulators.get('stability', []))

        min_length = min(len(energy), len(integrity), len(stability))
        if min_length < 5:
            return {'analysis': 'insufficient_data'}

        energy = energy[-min_length:]
        integrity = integrity[-min_length:]
        stability = stability[-min_length:]

        # Analyze leading/lagging relationships
        correlations = {
            'energy_integrity': self._calculate_correlation(energy, integrity),
            'energy_stability': self._calculate_correlation(energy, stability),
            'integrity_stability': self._calculate_correlation(integrity, stability)
        }

        patterns['correlations'] = correlations

        # Detect cascade patterns (one parameter change leading to others)
        cascades = []
        for i in range(1, min_length):
            changes = {
                'energy': energy[i] - energy[i-1],
                'integrity': integrity[i] - integrity[i-1],
                'stability': stability[i] - stability[i-1]
            }

            # Look for significant changes followed by others
            significant_changes = [param for param, change in changes.items() if abs(change) > 0.1]

            if len(significant_changes) >= 2:
                cascades.append({
                    'initiator': significant_changes[0],
                    'followers': significant_changes[1:],
                    'index': i
                })

        patterns['cascades'] = cascades
        patterns['cascade_frequency'] = len(cascades) / max(1, min_length)

        return patterns

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        min_len = min(len(x), len(y))
        if min_len < 2:
            return 0.0

        x = x[-min_len:]
        y = y[-min_len:]

        mean_x = sum(x) / min_len
        mean_y = sum(y) / min_len

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = (sum((xi - mean_x)**2 for xi in x) * sum((yi - mean_y)**2 for yi in y)) ** 0.5

        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_stability_range(self) -> float:
        """Calculate the range of stability variations."""
        stability_impacts = self.impact_accumulators.get('stability', [])
        if len(stability_impacts) < 3:
            return 0.0

        return max(stability_impacts) - min(stability_impacts)

    def _calculate_overall_state_volatility(self) -> float:
        """Calculate overall volatility across all state parameters."""
        volatilities = []
        for param in ['energy', 'integrity', 'stability']:
            impacts = self.impact_accumulators.get(param, [])
            if len(impacts) >= 3:
                volatility = self._calculate_volatility(impacts)
                volatilities.append(volatility)

        return sum(volatilities) / len(volatilities) if volatilities else 0.0

    def _calculate_overall_health_score(self, state_data: Dict[str, Any]) -> float:
        """Calculate overall health score from state parameters."""
        energy = state_data.get('energy', 50.0) / 100.0  # Normalize to 0-1
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Weighted average
        health_score = (
            energy * 0.4 +      # Energy is important but can be managed
            integrity * 0.4 +   # Integrity is critical
            stability * 0.2     # Stability affects predictability
        )

        return health_score

    def _determine_dominant_state(self, state_data: Dict[str, Any]) -> str:
        """Determine the dominant state characteristic."""
        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        if energy < 30:
            return 'energy_depleted'
        elif integrity < 0.5:
            return 'integrity_compromised'
        elif stability < 0.6:
            return 'behaviorally_unstable'
        elif energy > 80 and integrity > 0.9 and stability > 0.9:
            return 'peak_performance'
        else:
            return 'balanced_operation'

    def _determine_system_phase(self, state_data: Dict[str, Any]) -> str:
        """Determine the current system operational phase."""
        health_score = self._calculate_overall_health_score(state_data)

        if health_score > 0.8:
            return 'optimal_operation'
        elif health_score > 0.6:
            return 'normal_operation'
        elif health_score > 0.4:
            return 'degraded_operation'
        elif health_score > 0.2:
            return 'critical_operation'
        else:
            return 'emergency_operation'

    def _analyze_three_way_dynamics(self, energy: float, integrity: float, stability: float) -> Dict[str, Any]:
        """Analyze the three-way dynamics between energy, integrity, and stability."""
        # Normalize values for comparison
        energy_norm = energy / 100.0
        integrity_norm = integrity
        stability_norm = stability

        # Calculate balance score (how close the parameters are to each other)
        values = [energy_norm, integrity_norm, stability_norm]
        balance_score = 1.0 - (max(values) - min(values))  # Higher when values are closer

        # Determine dynamic state
        if balance_score > 0.8:
            dynamic_state = 'harmonious'
            description = 'Параметры хорошо сбалансированы, система работает гармонично'
        elif balance_score > 0.6:
            dynamic_state = 'balanced'
            description = 'Параметры reasonably сбалансированы'
        elif balance_score > 0.4:
            dynamic_state = 'unbalanced'
            description = 'Параметры несбалансированы, возможны конфликты'
        else:
            dynamic_state = 'conflicting'
            description = 'Параметры сильно несбалансированы, система в напряжении'

        # Identify potential issues
        issues = []
        if energy_norm < 0.3:
            issues.append('low_energy_draining_others')
        if integrity_norm < 0.6:
            issues.append('integrity_compromising_stability')
        if stability_norm < 0.6:
            issues.append('instability_affecting_coherence')

        return {
            'dynamic_state': dynamic_state,
            'balance_score': balance_score,
            'description': description,
            'potential_issues': issues
        }

    def _calculate_sequence_similarity(self, seq1: List[float], seq2: List[float]) -> float:
        """Calculate similarity between two sequences (simple Euclidean distance)."""
        if len(seq1) != len(seq2):
            return 0.0

        distance = sum((a - b) ** 2 for a, b in zip(seq1, seq2)) ** 0.5
        max_possible_distance = (len(seq1) * 2.0) ** 0.5  # Rough maximum

        return 1.0 - min(1.0, distance / max_possible_distance)

    def reset_analysis(self):
        """Reset analysis state for fresh analysis."""
        self.semantic_patterns.clear()
        self.behavioral_anomalies.clear()
        self.correlation_chains.clear()
        self.state_evolution.clear()
        self.event_type_frequencies.clear()
        self.decision_pattern_frequencies.clear()
        self.impact_accumulators.clear()
        logger.info("Semantic analysis state reset")