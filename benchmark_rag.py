#!/usr/bin/env python3
"""
Enhanced RAG Pipeline - Performance Benchmark Script
Comprehensive performance testing and analysis for the Academic Agent system.
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict, Any
from dataclasses import dataclass
import requests
import concurrent.futures
from pathlib import Path

@dataclass
class BenchmarkResult:
    """Benchmark result data structure."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float
    error_rate: float
    confidence_scores: List[float]
    answer_types: Dict[str, int]

class RAGBenchmark:
    """Performance benchmark suite for the Enhanced RAG Pipeline."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
    
    def print_banner(self):
        """Print benchmark banner."""
        print("🚀" + "=" * 60 + "🚀")
        print("    Enhanced RAG Pipeline - Performance Benchmark")
        print("    Comprehensive Testing and Analysis")
        print("🚀" + "=" * 60 + "🚀")
        print()
    
    def check_server_health(self) -> bool:
        """Check if the server is running and healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Server is healthy and ready for benchmarking")
                return True
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def make_request(self, question: str, doc_id: str = "any") -> Dict[str, Any]:
        """Make a single API request and measure performance."""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/ask",
                json={
                    "doc_id": doc_id,
                    "question": question,
                    "top_k": 5,
                    "temperature": 0.1
                },
                timeout=60
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response_time": response_time,
                    "answer_type": data.get("answer_type", "unknown"),
                    "confidence": data.get("confidence", 0.0),
                    "answer_length": len(data.get("answer", "")),
                    "sources_count": len(data.get("sources", [])),
                    "chunks_used": len(data.get("used_chunks", []))
                }
            else:
                return {
                    "success": False,
                    "response_time": response_time,
                    "error": f"HTTP {response.status_code}",
                    "answer_type": "error",
                    "confidence": 0.0
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response_time": end_time - start_time,
                "error": str(e),
                "answer_type": "error",
                "confidence": 0.0
            }
    
    def run_sequential_test(self, questions: List[str], test_name: str) -> BenchmarkResult:
        """Run sequential performance test."""
        print(f"\n🔍 Running Sequential Test: {test_name}")
        print("-" * 50)
        
        results = []
        start_time = time.time()
        
        for i, question in enumerate(questions, 1):
            print(f"Request {i}/{len(questions)}: {question[:50]}...")
            result = self.make_request(question)
            results.append(result)
            
            if result["success"]:
                print(f"  ✅ {result['response_time']:.2f}s - {result['answer_type']}")
            else:
                print(f"  ❌ {result['response_time']:.2f}s - {result.get('error', 'Unknown error')}")
        
        total_time = time.time() - start_time
        return self._calculate_metrics(results, test_name, total_time)
    
    def run_concurrent_test(self, questions: List[str], test_name: str, max_workers: int = 5) -> BenchmarkResult:
        """Run concurrent performance test."""
        print(f"\n🔄 Running Concurrent Test: {test_name}")
        print(f"   Workers: {max_workers}")
        print("-" * 50)
        
        start_time = time.time()
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            future_to_question = {
                executor.submit(self.make_request, question): question 
                for question in questions
            }
            
            # Collect results
            for i, future in enumerate(concurrent.futures.as_completed(future_to_question), 1):
                question = future_to_question[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result["success"]:
                        print(f"  ✅ {i}/{len(questions)} - {result['response_time']:.2f}s")
                    else:
                        print(f"  ❌ {i}/{len(questions)} - {result.get('error', 'Failed')}")
                        
                except Exception as e:
                    print(f"  ❌ {i}/{len(questions)} - Exception: {e}")
                    results.append({
                        "success": False,
                        "response_time": 0,
                        "error": str(e),
                        "answer_type": "error",
                        "confidence": 0.0
                    })
        
        total_time = time.time() - start_time
        return self._calculate_metrics(results, test_name, total_time)
    
    def _calculate_metrics(self, results: List[Dict], test_name: str, total_time: float) -> BenchmarkResult:
        """Calculate performance metrics from results."""
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        if successful_results:
            response_times = [r["response_time"] for r in successful_results]
            confidence_scores = [r["confidence"] for r in successful_results]
            
            # Calculate percentiles
            response_times.sort()
            p95_index = int(0.95 * len(response_times))
            p95_time = response_times[p95_index] if response_times else 0
            
            # Count answer types
            answer_types = {}
            for result in successful_results:
                answer_type = result["answer_type"]
                answer_types[answer_type] = answer_types.get(answer_type, 0) + 1
        else:
            response_times = [0]
            confidence_scores = [0]
            p95_time = 0
            answer_types = {}
        
        return BenchmarkResult(
            test_name=test_name,
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            avg_response_time=statistics.mean([r["response_time"] for r in results]),
            min_response_time=min([r["response_time"] for r in results]),
            max_response_time=max([r["response_time"] for r in results]),
            p95_response_time=p95_time,
            requests_per_second=len(results) / total_time if total_time > 0 else 0,
            error_rate=len(failed_results) / len(results) * 100,
            confidence_scores=confidence_scores,
            answer_types=answer_types
        )
    
    def print_results(self, result: BenchmarkResult):
        """Print benchmark results."""
        print(f"\n📊 Results for {result.test_name}")
        print("=" * 50)
        print(f"Total Requests:      {result.total_requests}")
        print(f"Successful:          {result.successful_requests}")
        print(f"Failed:              {result.failed_requests}")
        print(f"Error Rate:          {result.error_rate:.1f}%")
        print(f"Requests/Second:     {result.requests_per_second:.2f}")
        print()
        print("Response Times:")
        print(f"  Average:           {result.avg_response_time:.2f}s")
        print(f"  Minimum:           {result.min_response_time:.2f}s")
        print(f"  Maximum:           {result.max_response_time:.2f}s")
        print(f"  95th Percentile:   {result.p95_response_time:.2f}s")
        print()
        
        if result.confidence_scores:
            avg_confidence = statistics.mean(result.confidence_scores)
            print(f"Average Confidence:  {avg_confidence:.3f}")
        
        if result.answer_types:
            print("Answer Types:")
            for answer_type, count in result.answer_types.items():
                percentage = (count / result.successful_requests) * 100
                print(f"  {answer_type:12}: {count:3d} ({percentage:5.1f}%)")
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to JSON file."""
        results_data = []
        for result in self.results:
            results_data.append({
                "test_name": result.test_name,
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "avg_response_time": result.avg_response_time,
                "min_response_time": result.min_response_time,
                "max_response_time": result.max_response_time,
                "p95_response_time": result.p95_response_time,
                "requests_per_second": result.requests_per_second,
                "error_rate": result.error_rate,
                "avg_confidence": statistics.mean(result.confidence_scores) if result.confidence_scores else 0,
                "answer_types": result.answer_types
            })
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": results_data
            }, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")

def main():
    """Run comprehensive benchmark suite."""
    benchmark = RAGBenchmark()
    benchmark.print_banner()
    
    # Check server health
    if not benchmark.check_server_health():
        print("❌ Server is not available. Please start the server first.")
        return
    
    # Define test questions
    simple_questions = [
        "What is a database?",
        "Define normalization",
        "What is SQL?",
        "Explain ACID properties",
        "What is a primary key?"
    ]
    
    comparison_questions = [
        "What is the difference between SQL and NoSQL?",
        "Compare normalization vs denormalization",
        "SQL vs NoSQL advantages and disadvantages",
        "Difference between OLTP and OLAP",
        "Compare relational and document databases"
    ]
    
    complex_questions = [
        "Explain database normalization with examples and advantages",
        "How do indexes work in databases and what are their trade-offs?",
        "Describe the ACID properties and their importance in transactions",
        "What are the different types of database joins and when to use them?",
        "Explain database sharding and its benefits for scalability"
    ]
    
    external_questions = [
        "What is quantum computing?",
        "Explain machine learning algorithms",
        "How does blockchain technology work?",
        "What is artificial intelligence?",
        "Describe cloud computing architecture"
    ]
    
    # Run benchmark tests
    print("🚀 Starting Benchmark Suite...")
    
    # Test 1: Simple Questions (Sequential)
    result1 = benchmark.run_sequential_test(simple_questions, "Simple Questions (Sequential)")
    benchmark.results.append(result1)
    benchmark.print_results(result1)
    
    # Test 2: Comparison Questions (Sequential)
    result2 = benchmark.run_sequential_test(comparison_questions, "Comparison Questions (Sequential)")
    benchmark.results.append(result2)
    benchmark.print_results(result2)
    
    # Test 3: Complex Questions (Sequential)
    result3 = benchmark.run_sequential_test(complex_questions, "Complex Questions (Sequential)")
    benchmark.results.append(result3)
    benchmark.print_results(result3)
    
    # Test 4: External Knowledge (Sequential)
    result4 = benchmark.run_sequential_test(external_questions, "External Knowledge (Sequential)")
    benchmark.results.append(result4)
    benchmark.print_results(result4)
    
    # Test 5: Mixed Load (Concurrent)
    mixed_questions = simple_questions + comparison_questions[:3]
    result5 = benchmark.run_concurrent_test(mixed_questions, "Mixed Load (Concurrent)", max_workers=3)
    benchmark.results.append(result5)
    benchmark.print_results(result5)
    
    # Test 6: Stress Test (Higher Concurrency)
    stress_questions = simple_questions * 2  # Repeat simple questions
    result6 = benchmark.run_concurrent_test(stress_questions, "Stress Test (High Concurrency)", max_workers=5)
    benchmark.results.append(result6)
    benchmark.print_results(result6)
    
    # Save results
    benchmark.save_results()
    
    # Summary
    print(f"\n🎉 Benchmark Complete!")
    print("=" * 50)
    print(f"Total Tests Run: {len(benchmark.results)}")
    
    # Overall statistics
    total_requests = sum(r.total_requests for r in benchmark.results)
    total_successful = sum(r.successful_requests for r in benchmark.results)
    overall_error_rate = ((total_requests - total_successful) / total_requests * 100) if total_requests > 0 else 0
    
    print(f"Total Requests: {total_requests}")
    print(f"Overall Success Rate: {(total_successful/total_requests*100):.1f}%")
    print(f"Overall Error Rate: {overall_error_rate:.1f}%")
    
    # Performance recommendations
    print(f"\n💡 Performance Insights:")
    avg_response_times = [r.avg_response_time for r in benchmark.results if r.successful_requests > 0]
    if avg_response_times:
        overall_avg = statistics.mean(avg_response_times)
        print(f"   Average Response Time: {overall_avg:.2f}s")
        
        if overall_avg < 5:
            print("   ✅ Excellent response times!")
        elif overall_avg < 10:
            print("   ✅ Good response times")
        elif overall_avg < 20:
            print("   ⚠️  Acceptable response times")
        else:
            print("   ❌ Consider optimization")
    
    print(f"\n📊 Detailed results saved to benchmark_results.json")

if __name__ == "__main__":
    main()