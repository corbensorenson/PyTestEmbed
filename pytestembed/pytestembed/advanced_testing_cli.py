#!/usr/bin/env python3
"""
Advanced Testing CLI for PyTestEmbed

Command-line interface for advanced testing features including
smart test selection, failure prediction, and property-based testing.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from .smart_test_selection import SmartTestSelector, run_smart_test_selection
from .failure_prediction import FailurePredictor, predict_test_failures
from .property_testing import PropertyBasedTester
from .parser import PyTestEmbedParser


def print_banner():
    """Print PyTestEmbed advanced testing banner."""
    print("""
🚀 PyTestEmbed Advanced Testing Suite
=====================================
Intelligent • Predictive • Property-Based
""")


def smart_selection_command(args):
    """Run smart test selection."""
    print("🧠 Smart Test Selection")
    print("=" * 50)
    
    selection = run_smart_test_selection(
        workspace_path=args.workspace,
        commit_hash=args.commit,
        max_time=args.max_time,
        confidence=args.confidence
    )
    
    print(f"\n📊 Results:")
    print(f"Selected tests: {len(selection.selected_tests)}")
    print(f"Skipped tests: {len(selection.skipped_tests)}")
    print(f"Time saved: {selection.estimated_time_saved:.1f}s")
    print(f"Confidence: {selection.confidence_score:.2f}")
    
    if args.verbose:
        print(f"\n🎯 Selected Tests:")
        for test in selection.selected_tests[:10]:  # Show top 10
            reason = selection.selection_reason.get(
                f"{test.test_file}::{test.target_function}::{test.test_line}",
                "Unknown"
            )
            print(f"  • {test.test_file}:{test.test_line} - {reason}")
        
        if len(selection.selected_tests) > 10:
            print(f"  ... and {len(selection.selected_tests) - 10} more")


def failure_prediction_command(args):
    """Run failure prediction."""
    print("🔮 Failure Prediction")
    print("=" * 50)
    
    predictor = FailurePredictor(args.workspace)
    
    # Find all tests
    parser = PyTestEmbedParser()
    all_tests = []
    
    for py_file in Path(args.workspace).rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            parsed = parser.parse_file(content)
            file_path = str(py_file.relative_to(Path(args.workspace)))
            
            for func in parsed.functions:
                for test_block in func.test_blocks:
                    for i, test_case in enumerate(test_block.test_cases):
                        all_tests.append({
                            'file_path': file_path,
                            'line_number': test_case.line_number,
                            'expression': test_case.assertion,
                            'function_name': func.name
                        })
        except:
            continue
    
    print(f"Found {len(all_tests)} tests")
    
    # Predict failures
    predictions = []
    for test in all_tests:
        prediction = predictor.predict_test_failure(
            test['file_path'],
            test['line_number'],
            test['expression'],
            test['function_name'],
            {}  # Empty history for now
        )
        predictions.append(prediction)
    
    # Sort by failure probability
    predictions.sort(key=lambda p: p.failure_probability, reverse=True)
    
    # Show results
    high_risk = [p for p in predictions if p.failure_probability > 0.6]
    medium_risk = [p for p in predictions if 0.3 < p.failure_probability <= 0.6]
    
    print(f"\n📊 Prediction Results:")
    print(f"High risk tests: {len(high_risk)}")
    print(f"Medium risk tests: {len(medium_risk)}")
    print(f"Low risk tests: {len(predictions) - len(high_risk) - len(medium_risk)}")
    
    if high_risk:
        print(f"\n⚠️ High Risk Tests:")
        for pred in high_risk[:5]:  # Show top 5
            print(f"  • {pred.test_id}")
            print(f"    Probability: {pred.failure_probability:.2f}")
            print(f"    Recommendation: {pred.recommended_action}")
            if pred.contributing_factors:
                print(f"    Factors: {', '.join(pred.contributing_factors[:3])}")
            print()
    
    # Show accuracy if available
    accuracy = predictor.get_prediction_accuracy()
    if accuracy['total_predictions'] > 0:
        print(f"📈 Model Performance:")
        print(f"Accuracy: {accuracy['accuracy']:.2f}")
        print(f"Precision: {accuracy['precision']:.2f}")
        print(f"Recall: {accuracy['recall']:.2f}")


def property_testing_command(args):
    """Run property-based testing."""
    print("🧪 Property-Based Testing")
    print("=" * 50)
    
    tester = PropertyBasedTester(args.workspace)
    
    # Load the target file
    file_path = Path(args.workspace) / args.file
    if not file_path.exists():
        print(f"❌ File not found: {args.file}")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse to find the function
    parser = PyTestEmbedParser()
    parsed = parser.parse_file(content)
    
    target_function = None
    for func in parsed.functions:
        if func.name == args.function:
            target_function = func
            break
    
    if not target_function:
        print(f"❌ Function '{args.function}' not found in {args.file}")
        return
    
    # Extract test block content
    test_block_content = ""
    if target_function.test_blocks:
        test_block_content = "\n".join(
            tc.assertion for tb in target_function.test_blocks for tc in tb.test_cases
        )
    
    print(f"🎯 Testing function: {args.function}")
    print(f"📄 File: {args.file}")
    
    # Generate property suggestions
    suggestions = tester.generate_property_suggestions(lambda: None)  # Mock function
    
    if suggestions:
        print(f"\n💡 Suggested Properties:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    
    # If test block has property tests, run them
    if 'property(' in test_block_content:
        print(f"\n🔍 Running existing property tests...")
        # Mock function for demonstration
        def mock_function(*args):
            return sum(args) if all(isinstance(arg, (int, float)) for arg in args) else 0
        
        results = tester.run_property_tests(mock_function, test_block_content)
        
        print(f"\n📊 Property Test Results:")
        for result in results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status} {result.property_name}")
            print(f"    Tests run: {result.tests_run}")
            print(f"    Coverage: {result.coverage_achieved:.2f}")
            
            if not result.passed:
                if result.counterexamples:
                    print(f"    Counterexamples: {result.counterexamples[:3]}")
                if result.error_message:
                    print(f"    Error: {result.error_message}")
            print()


def benchmark_command(args):
    """Run benchmarking of advanced testing features."""
    print("⚡ Advanced Testing Benchmark")
    print("=" * 50)
    
    import time
    
    # Benchmark smart test selection
    print("🧠 Benchmarking Smart Test Selection...")
    start_time = time.time()
    
    selector = SmartTestSelector(args.workspace)
    selection = selector.select_tests()
    
    selection_time = time.time() - start_time
    
    print(f"  Time: {selection_time:.2f}s")
    print(f"  Tests analyzed: {len(selection.selected_tests) + len(selection.skipped_tests)}")
    print(f"  Selection ratio: {len(selection.selected_tests) / (len(selection.selected_tests) + len(selection.skipped_tests)):.2f}")
    
    # Benchmark failure prediction
    print("\n🔮 Benchmarking Failure Prediction...")
    start_time = time.time()
    
    predictor = FailurePredictor(args.workspace)
    
    # Mock some predictions
    for i in range(100):
        predictor.predict_test_failure(
            "test_file.py", i, f"test_expression_{i}", f"function_{i}", {}
        )
    
    prediction_time = time.time() - start_time
    
    print(f"  Time: {prediction_time:.2f}s")
    print(f"  Predictions per second: {100 / prediction_time:.1f}")
    
    # Show overall performance
    print(f"\n📊 Overall Performance:")
    print(f"Smart selection overhead: {selection_time:.2f}s")
    print(f"Prediction overhead: {prediction_time / 100:.4f}s per test")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PyTestEmbed Advanced Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pytestembed-advanced smart --workspace . --commit HEAD~1
  pytestembed-advanced predict --workspace . --verbose
  pytestembed-advanced property --file mycode.py --function calculate
  pytestembed-advanced benchmark --workspace .
        """
    )
    
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Smart test selection
    smart_parser = subparsers.add_parser("smart", help="Smart test selection")
    smart_parser.add_argument("--commit", default="HEAD~1", help="Compare against commit")
    smart_parser.add_argument("--max-time", type=float, help="Maximum execution time")
    smart_parser.add_argument("--confidence", type=float, default=0.8, help="Confidence threshold")
    
    # Failure prediction
    predict_parser = subparsers.add_parser("predict", help="Failure prediction")
    
    # Property-based testing
    property_parser = subparsers.add_parser("property", help="Property-based testing")
    property_parser.add_argument("--file", required=True, help="Python file to test")
    property_parser.add_argument("--function", required=True, help="Function name to test")
    
    # Benchmarking
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark advanced features")
    
    args = parser.parse_args()
    
    if not args.command:
        print_banner()
        parser.print_help()
        return
    
    print_banner()
    
    try:
        if args.command == "smart":
            smart_selection_command(args)
        elif args.command == "predict":
            failure_prediction_command(args)
        elif args.command == "property":
            property_testing_command(args)
        elif args.command == "benchmark":
            benchmark_command(args)
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
