#!/usr/bin/env python3
"""
Failure Prediction Engine for PyTestEmbed

Uses machine learning and heuristics to predict which tests are likely to fail
before execution, enabling proactive test management and faster feedback.
"""

import ast
import json
import math
import pickle
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib

from .parser import PyTestEmbedParser


@dataclass
class TestFeatures:
    """Features extracted from a test for failure prediction."""
    
    # Test characteristics
    test_complexity: float
    assertion_count: int
    has_external_dependencies: bool
    uses_async: bool
    uses_mocks: bool
    
    # Code characteristics
    function_complexity: float
    function_length: int
    parameter_count: int
    return_type_complexity: float
    
    # Historical characteristics
    failure_rate: float
    avg_execution_time: float
    last_failure_days_ago: float
    consecutive_failures: int
    
    # Change characteristics
    code_changed_recently: bool
    dependencies_changed: bool
    test_changed_recently: bool
    change_magnitude: float
    
    # Environmental characteristics
    time_of_day: float
    day_of_week: int
    recent_system_changes: bool


@dataclass
class FailurePrediction:
    """Prediction result for a test."""
    test_id: str
    failure_probability: float
    confidence: float
    contributing_factors: List[str]
    recommended_action: str
    prediction_timestamp: float


class CodeComplexityAnalyzer:
    """Analyzes code complexity metrics."""
    
    @staticmethod
    def calculate_cyclomatic_complexity(code: str) -> float:
        """Calculate cyclomatic complexity of code."""
        try:
            tree = ast.parse(code)
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                # Decision points increase complexity
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
                elif isinstance(node, ast.ListComp):
                    complexity += 1
                    
            return float(complexity)
        except:
            return 1.0
    
    @staticmethod
    def calculate_cognitive_complexity(code: str) -> float:
        """Calculate cognitive complexity (readability-focused)."""
        try:
            tree = ast.parse(code)
            complexity = 0
            nesting_level = 0
            
            def visit_node(node, level=0):
                nonlocal complexity, nesting_level
                
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1 + level
                elif isinstance(node, ast.Try):
                    complexity += 1 + level
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
                elif isinstance(node, ast.Lambda):
                    complexity += 1
                    
                # Increase nesting for certain constructs
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    for child in ast.iter_child_nodes(node):
                        visit_node(child, level + 1)
                else:
                    for child in ast.iter_child_nodes(node):
                        visit_node(child, level)
            
            visit_node(tree)
            return float(complexity)
        except:
            return 0.0
    
    @staticmethod
    def analyze_dependencies(code: str) -> Dict[str, Any]:
        """Analyze external dependencies in code."""
        try:
            tree = ast.parse(code)
            
            has_file_io = False
            has_network = False
            has_database = False
            has_random = False
            has_time_dependency = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        attr_name = node.func.attr
                        if attr_name in ['open', 'read', 'write']:
                            has_file_io = True
                        elif attr_name in ['get', 'post', 'request']:
                            has_network = True
                        elif attr_name in ['execute', 'query', 'commit']:
                            has_database = True
                    elif isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in ['random', 'randint', 'choice']:
                            has_random = True
                        elif func_name in ['time', 'sleep', 'now']:
                            has_time_dependency = True
            
            return {
                'has_file_io': has_file_io,
                'has_network': has_network,
                'has_database': has_database,
                'has_random': has_random,
                'has_time_dependency': has_time_dependency,
                'external_dependency_count': sum([
                    has_file_io, has_network, has_database, has_random, has_time_dependency
                ])
            }
        except:
            return {'external_dependency_count': 0}


class TestFeatureExtractor:
    """Extracts features from tests for ML prediction."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.parser = PyTestEmbedParser()
        self.complexity_analyzer = CodeComplexityAnalyzer()
        
    def extract_features(self, test_file: str, test_line: int, 
                        test_expression: str, target_function: str,
                        test_history: Dict[str, Any]) -> TestFeatures:
        """Extract all features for a test."""
        
        # Load source code
        file_path = self.workspace_path / test_file
        try:
            with open(file_path, 'r') as f:
                source_code = f.read()
        except:
            source_code = ""
        
        # Parse code to find target function
        function_code = self._extract_function_code(source_code, target_function)
        
        # Extract test characteristics
        test_features = self._extract_test_characteristics(test_expression)
        
        # Extract code characteristics
        code_features = self._extract_code_characteristics(function_code)
        
        # Extract historical characteristics
        historical_features = self._extract_historical_characteristics(test_history)
        
        # Extract change characteristics
        change_features = self._extract_change_characteristics(test_file, target_function)
        
        # Extract environmental characteristics
        env_features = self._extract_environmental_characteristics()
        
        return TestFeatures(
            # Test characteristics
            test_complexity=test_features['complexity'],
            assertion_count=test_features['assertion_count'],
            has_external_dependencies=test_features['has_external_deps'],
            uses_async=test_features['uses_async'],
            uses_mocks=test_features['uses_mocks'],
            
            # Code characteristics
            function_complexity=code_features['complexity'],
            function_length=code_features['length'],
            parameter_count=code_features['parameter_count'],
            return_type_complexity=code_features['return_complexity'],
            
            # Historical characteristics
            failure_rate=historical_features['failure_rate'],
            avg_execution_time=historical_features['avg_execution_time'],
            last_failure_days_ago=historical_features['last_failure_days_ago'],
            consecutive_failures=historical_features['consecutive_failures'],
            
            # Change characteristics
            code_changed_recently=change_features['code_changed'],
            dependencies_changed=change_features['deps_changed'],
            test_changed_recently=change_features['test_changed'],
            change_magnitude=change_features['magnitude'],
            
            # Environmental characteristics
            time_of_day=env_features['time_of_day'],
            day_of_week=env_features['day_of_week'],
            recent_system_changes=env_features['system_changes']
        )
    
    def _extract_function_code(self, source_code: str, function_name: str) -> str:
        """Extract the code for a specific function."""
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    return ast.unparse(node)
        except:
            pass
        return ""
    
    def _extract_test_characteristics(self, test_expression: str) -> Dict[str, Any]:
        """Extract characteristics from test expression."""
        
        # Count assertions (look for comparison operators)
        assertion_count = test_expression.count('==') + test_expression.count('!=') + \
                         test_expression.count('<') + test_expression.count('>') + \
                         test_expression.count('in') + test_expression.count('is')
        
        # Check for external dependencies
        has_external_deps = any(keyword in test_expression.lower() for keyword in [
            'open', 'request', 'http', 'database', 'file', 'network', 'api'
        ])
        
        # Check for async usage
        uses_async = 'await' in test_expression or 'async' in test_expression
        
        # Check for mocks
        uses_mocks = any(keyword in test_expression.lower() for keyword in [
            'mock', 'patch', 'stub', 'fake'
        ])
        
        # Calculate test complexity (simple heuristic)
        complexity = len(test_expression.split()) / 10.0  # Normalize by word count
        
        return {
            'complexity': complexity,
            'assertion_count': max(1, assertion_count),
            'has_external_deps': has_external_deps,
            'uses_async': uses_async,
            'uses_mocks': uses_mocks
        }
    
    def _extract_code_characteristics(self, function_code: str) -> Dict[str, Any]:
        """Extract characteristics from function code."""
        if not function_code:
            return {
                'complexity': 1.0,
                'length': 0,
                'parameter_count': 0,
                'return_complexity': 0.0
            }
        
        # Calculate complexity
        complexity = self.complexity_analyzer.calculate_cyclomatic_complexity(function_code)
        
        # Calculate length
        length = len(function_code.split('\n'))
        
        # Count parameters
        parameter_count = 0
        try:
            tree = ast.parse(function_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    parameter_count = len(node.args.args)
                    break
        except:
            pass
        
        # Estimate return type complexity
        return_complexity = function_code.count('return') * 0.5
        
        return {
            'complexity': complexity,
            'length': length,
            'parameter_count': parameter_count,
            'return_complexity': return_complexity
        }
    
    def _extract_historical_characteristics(self, test_history: Dict[str, Any]) -> Dict[str, Any]:
        """Extract historical characteristics from test history."""
        
        failure_rate = test_history.get('failure_rate', 0.0)
        avg_execution_time = test_history.get('execution_time', 0.1)
        last_failure = test_history.get('last_failure', 0)
        
        # Calculate days since last failure
        if last_failure:
            last_failure_days_ago = (time.time() - last_failure) / 86400
        else:
            last_failure_days_ago = 999.0  # Very old
        
        # Count consecutive failures (simplified)
        consecutive_failures = test_history.get('consecutive_failures', 0)
        
        return {
            'failure_rate': failure_rate,
            'avg_execution_time': avg_execution_time,
            'last_failure_days_ago': min(last_failure_days_ago, 999.0),
            'consecutive_failures': consecutive_failures
        }
    
    def _extract_change_characteristics(self, test_file: str, target_function: str) -> Dict[str, Any]:
        """Extract change-related characteristics."""
        
        # Simplified change detection (could be enhanced with Git integration)
        file_path = self.workspace_path / test_file
        
        try:
            stat = file_path.stat()
            days_since_modified = (time.time() - stat.st_mtime) / 86400
            
            code_changed = days_since_modified < 7  # Changed in last week
            test_changed = days_since_modified < 3   # Test changed recently
            deps_changed = False  # TODO: Implement dependency change detection
            magnitude = max(0.0, 7.0 - days_since_modified) / 7.0  # Normalized
            
        except:
            code_changed = False
            test_changed = False
            deps_changed = False
            magnitude = 0.0
        
        return {
            'code_changed': code_changed,
            'test_changed': test_changed,
            'deps_changed': deps_changed,
            'magnitude': magnitude
        }
    
    def _extract_environmental_characteristics(self) -> Dict[str, Any]:
        """Extract environmental characteristics."""
        
        current_time = time.time()
        local_time = time.localtime(current_time)
        
        # Time of day (0.0 = midnight, 0.5 = noon)
        time_of_day = (local_time.tm_hour + local_time.tm_min / 60.0) / 24.0
        
        # Day of week (0 = Monday, 6 = Sunday)
        day_of_week = local_time.tm_wday
        
        # Recent system changes (simplified)
        recent_system_changes = False  # TODO: Implement system change detection
        
        return {
            'time_of_day': time_of_day,
            'day_of_week': day_of_week,
            'system_changes': recent_system_changes
        }


class HeuristicPredictor:
    """Rule-based failure predictor using heuristics."""

    def predict_failure(self, features: TestFeatures) -> Tuple[float, float, List[str]]:
        """Predict failure probability using heuristics."""

        probability = 0.0
        confidence = 0.8
        factors = []

        # Historical failure patterns
        if features.failure_rate > 0.3:
            probability += 0.4
            factors.append(f"High historical failure rate ({features.failure_rate:.2f})")

        if features.consecutive_failures > 2:
            probability += 0.3
            factors.append(f"Multiple consecutive failures ({features.consecutive_failures})")

        if features.last_failure_days_ago < 1:
            probability += 0.2
            factors.append("Failed recently (within 24 hours)")

        # Code complexity factors
        if features.function_complexity > 10:
            probability += 0.2
            factors.append(f"High function complexity ({features.function_complexity})")

        if features.test_complexity > 2:
            probability += 0.1
            factors.append(f"Complex test assertion ({features.test_complexity:.1f})")

        # Change-related factors
        if features.code_changed_recently:
            probability += 0.3
            factors.append("Code changed recently")

        if features.dependencies_changed:
            probability += 0.2
            factors.append("Dependencies changed")

        if features.test_changed_recently:
            probability += 0.1
            factors.append("Test modified recently")

        # External dependency factors
        if features.has_external_dependencies:
            probability += 0.15
            factors.append("Uses external dependencies")

        if features.uses_async:
            probability += 0.1
            factors.append("Uses async/await (timing sensitive)")

        # Environmental factors
        if features.time_of_day < 0.25 or features.time_of_day > 0.9:  # Late night/early morning
            probability += 0.05
            factors.append("Running during off-hours")

        if features.recent_system_changes:
            probability += 0.1
            factors.append("Recent system changes detected")

        # Execution time factors
        if features.avg_execution_time > 5.0:  # Slow tests more likely to fail
            probability += 0.1
            factors.append(f"Slow test execution ({features.avg_execution_time:.1f}s)")

        # Cap probability at 1.0
        probability = min(1.0, probability)

        # Adjust confidence based on available data
        if features.failure_rate == 0.0 and features.last_failure_days_ago > 30:
            confidence = 0.6  # Less confident for tests without recent history

        return probability, confidence, factors


class SimpleMLPredictor:
    """Simple machine learning predictor using logistic regression-like approach."""

    def __init__(self):
        self.weights = self._initialize_weights()
        self.is_trained = False

    def _initialize_weights(self) -> Dict[str, float]:
        """Initialize feature weights based on domain knowledge."""
        return {
            'failure_rate': 2.0,
            'consecutive_failures': 0.3,
            'last_failure_days_ago': -0.1,  # Negative: more recent = higher probability
            'function_complexity': 0.05,
            'test_complexity': 0.1,
            'code_changed_recently': 1.0,
            'dependencies_changed': 0.8,
            'test_changed_recently': 0.5,
            'has_external_dependencies': 0.6,
            'uses_async': 0.4,
            'avg_execution_time': 0.02,
            'change_magnitude': 0.5
        }

    def predict_failure(self, features: TestFeatures) -> Tuple[float, float]:
        """Predict failure probability using weighted features."""

        # Convert features to numerical values
        feature_values = {
            'failure_rate': features.failure_rate,
            'consecutive_failures': min(features.consecutive_failures, 10) / 10.0,
            'last_failure_days_ago': max(0, 30 - features.last_failure_days_ago) / 30.0,
            'function_complexity': min(features.function_complexity, 20) / 20.0,
            'test_complexity': min(features.test_complexity, 5) / 5.0,
            'code_changed_recently': 1.0 if features.code_changed_recently else 0.0,
            'dependencies_changed': 1.0 if features.dependencies_changed else 0.0,
            'test_changed_recently': 1.0 if features.test_changed_recently else 0.0,
            'has_external_dependencies': 1.0 if features.has_external_dependencies else 0.0,
            'uses_async': 1.0 if features.uses_async else 0.0,
            'avg_execution_time': min(features.avg_execution_time, 10) / 10.0,
            'change_magnitude': features.change_magnitude
        }

        # Calculate weighted sum
        score = 0.0
        for feature, value in feature_values.items():
            if feature in self.weights:
                score += self.weights[feature] * value

        # Apply sigmoid function to get probability
        probability = 1.0 / (1.0 + math.exp(-score))

        # Confidence based on feature availability
        available_features = sum(1 for v in feature_values.values() if v > 0)
        confidence = min(0.9, available_features / len(feature_values))

        return probability, confidence

    def update_weights(self, features: TestFeatures, actual_result: bool, learning_rate: float = 0.01):
        """Update weights based on actual test results (simple online learning)."""

        predicted_prob, _ = self.predict_failure(features)
        error = (1.0 if actual_result else 0.0) - predicted_prob

        # Update weights using gradient descent
        feature_values = self._features_to_values(features)
        for feature, value in feature_values.items():
            if feature in self.weights:
                self.weights[feature] += learning_rate * error * value

        self.is_trained = True

    def _features_to_values(self, features: TestFeatures) -> Dict[str, float]:
        """Convert TestFeatures to numerical values."""
        return {
            'failure_rate': features.failure_rate,
            'consecutive_failures': min(features.consecutive_failures, 10) / 10.0,
            'last_failure_days_ago': max(0, 30 - features.last_failure_days_ago) / 30.0,
            'function_complexity': min(features.function_complexity, 20) / 20.0,
            'test_complexity': min(features.test_complexity, 5) / 5.0,
            'code_changed_recently': 1.0 if features.code_changed_recently else 0.0,
            'dependencies_changed': 1.0 if features.dependencies_changed else 0.0,
            'test_changed_recently': 1.0 if features.test_changed_recently else 0.0,
            'has_external_dependencies': 1.0 if features.has_external_dependencies else 0.0,
            'uses_async': 1.0 if features.uses_async else 0.0,
            'avg_execution_time': min(features.avg_execution_time, 10) / 10.0,
            'change_magnitude': features.change_magnitude
        }


class FailurePredictor:
    """Main failure prediction engine."""

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.feature_extractor = TestFeatureExtractor(workspace_path)
        self.heuristic_predictor = HeuristicPredictor()
        self.ml_predictor = SimpleMLPredictor()
        self.prediction_history_file = self.workspace_path / ".pytestembed" / "predictions.json"
        self.prediction_history = self._load_prediction_history()

    def predict_test_failure(self, test_file: str, test_line: int,
                           test_expression: str, target_function: str,
                           test_history: Dict[str, Any]) -> FailurePrediction:
        """Predict if a test will fail."""

        # Extract features
        features = self.feature_extractor.extract_features(
            test_file, test_line, test_expression, target_function, test_history
        )

        # Get predictions from both models
        heuristic_prob, heuristic_conf, factors = self.heuristic_predictor.predict_failure(features)
        ml_prob, ml_conf = self.ml_predictor.predict_failure(features)

        # Combine predictions (weighted average)
        if self.ml_predictor.is_trained:
            combined_prob = (heuristic_prob * 0.4 + ml_prob * 0.6)
            combined_conf = (heuristic_conf * 0.4 + ml_conf * 0.6)
        else:
            combined_prob = heuristic_prob
            combined_conf = heuristic_conf

        # Generate recommendation
        recommendation = self._generate_recommendation(combined_prob, factors)

        # Create prediction
        test_id = f"{test_file}::{target_function}::{test_line}"
        prediction = FailurePrediction(
            test_id=test_id,
            failure_probability=combined_prob,
            confidence=combined_conf,
            contributing_factors=factors,
            recommended_action=recommendation,
            prediction_timestamp=time.time()
        )

        # Store prediction for later validation
        self.prediction_history[test_id] = asdict(prediction)
        self._save_prediction_history()

        return prediction

    def update_with_results(self, test_results: List[Dict[str, Any]]):
        """Update predictors with actual test results."""

        for result in test_results:
            test_id = f"{result['file']}::{result['function']}::{result['line']}"

            if test_id in self.prediction_history:
                # Get the prediction
                prediction_data = self.prediction_history[test_id]

                # Extract features again (could be cached)
                features = self.feature_extractor.extract_features(
                    result['file'], result['line'], result['expression'],
                    result['function'], result.get('history', {})
                )

                # Update ML model
                actual_failure = result['status'] in ['fail', 'error']
                self.ml_predictor.update_weights(features, actual_failure)

                # Update prediction accuracy
                predicted_failure = prediction_data['failure_probability'] > 0.5
                was_correct = predicted_failure == actual_failure

                prediction_data['actual_result'] = actual_failure
                prediction_data['prediction_correct'] = was_correct

        self._save_prediction_history()

    def _generate_recommendation(self, probability: float, factors: List[str]) -> str:
        """Generate actionable recommendation based on prediction."""

        if probability > 0.8:
            return "HIGH RISK: Run this test first and investigate if it fails"
        elif probability > 0.6:
            return "MEDIUM RISK: Monitor this test closely"
        elif probability > 0.4:
            return "LOW RISK: Include in regular test run"
        else:
            return "STABLE: Low failure probability"

    def get_prediction_accuracy(self) -> Dict[str, float]:
        """Calculate prediction accuracy metrics."""

        predictions_with_results = [
            p for p in self.prediction_history.values()
            if 'actual_result' in p
        ]

        if not predictions_with_results:
            return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0}

        correct_predictions = sum(1 for p in predictions_with_results if p['prediction_correct'])
        accuracy = correct_predictions / len(predictions_with_results)

        # Calculate precision and recall for failure predictions
        predicted_failures = [p for p in predictions_with_results if p['failure_probability'] > 0.5]
        actual_failures = [p for p in predictions_with_results if p['actual_result']]

        true_positives = sum(1 for p in predicted_failures if p['actual_result'])

        precision = true_positives / len(predicted_failures) if predicted_failures else 0.0
        recall = true_positives / len(actual_failures) if actual_failures else 0.0

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'total_predictions': len(predictions_with_results)
        }

    def _load_prediction_history(self) -> Dict[str, Dict]:
        """Load prediction history from file."""
        if self.prediction_history_file.exists():
            try:
                with open(self.prediction_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading prediction history: {e}")
        return {}

    def _save_prediction_history(self):
        """Save prediction history to file."""
        try:
            self.prediction_history_file.parent.mkdir(exist_ok=True)
            with open(self.prediction_history_file, 'w') as f:
                json.dump(self.prediction_history, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving prediction history: {e}")


# CLI interface for failure prediction
def predict_test_failures(workspace_path: str = ".", test_history_file: Optional[str] = None):
    """Predict test failures from command line."""

    predictor = FailurePredictor(workspace_path)

    # Load test history if provided
    if test_history_file and Path(test_history_file).exists():
        with open(test_history_file, 'r') as f:
            test_history = json.load(f)
    else:
        test_history = {}

    print("🔮 Predicting test failures...")

    # Find all tests and predict failures
    predictions = []
    for py_file in Path(workspace_path).rglob("*.py"):
        # Parse and predict for each test
        # (Implementation would iterate through all tests)
        pass

    # Display results
    high_risk_tests = [p for p in predictions if p.failure_probability > 0.6]

    print(f"\n📊 Failure Prediction Results:")
    print(f"High risk tests: {len(high_risk_tests)}")

    for prediction in sorted(high_risk_tests, key=lambda p: p.failure_probability, reverse=True):
        print(f"⚠️ {prediction.test_id}: {prediction.failure_probability:.2f} - {prediction.recommended_action}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PyTestEmbed Failure Prediction")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--history", help="Test history file")

    args = parser.parse_args()

    predict_test_failures(args.workspace, args.history)
