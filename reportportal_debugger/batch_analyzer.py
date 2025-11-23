#!/usr/bin/env python3
"""
Batch Analyzer for ReportPortal
Processes multiple launches and generates comprehensive reports
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
from rp_debugger import ReportPortalClient, RPConfig
from advanced_rca import AdvancedRCAEngine

load_dotenv()


class BatchAnalyzer:
    """Batch analysis of multiple launches"""
    
    def __init__(self, config: RPConfig):
        self.client = ReportPortalClient(config)
        self.engine = AdvancedRCAEngine()
        self.results = []
    
    def analyze_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Analyze all launches within a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        print(f"\n{'='*80}")
        print(f"Batch Analysis: {start_date} to {end_date}")
        print(f"{'='*80}\n")
        
        launches = self._get_launches_in_range(start_date, end_date)
        
        if not launches:
            print("No launches found in the specified date range")
            return {}
        
        print(f"Found {len(launches)} launches to analyze\n")
        
        all_results = []
        summary = {
            "total_launches": len(launches),
            "total_failed_tests": 0,
            "defect_breakdown": {},
            "flaky_tests": [],
            "persistent_failures": [],
        }
        
        for idx, launch in enumerate(launches, 1):
            launch_id = launch.get("id")
            launch_name = launch.get("name", "Unknown")
            
            print(f"[{idx}/{len(launches)}] Analyzing: {launch_name}")
            
            failed_tests = self.client.get_failed_tests(launch_id)
            summary["total_failed_tests"] += len(failed_tests)
            
            for test in failed_tests:
                test_id = test.get("id")
                test_name = test.get("name", "Unknown")
                logs = self.client.get_test_logs(test_id)
                
                error_msg = test.get("issue", {}).get("comment", "")
                
                analysis = self.engine.analyze_comprehensive(
                    test_name=test_name,
                    error_message=error_msg,
                    logs=logs
                )
                
                result = {
                    "launch_id": launch_id,
                    "launch_name": launch_name,
                    "test_id": test_id,
                    "test_name": test_name,
                    "analysis": analysis,
                    "timestamp": launch.get("startTime"),
                }
                
                all_results.append(result)
                
                category = analysis["category"]
                summary["defect_breakdown"][category] = \
                    summary["defect_breakdown"].get(category, 0) + 1
        
        summary["flaky_tests"] = self._identify_flaky_tests(all_results)
        summary["persistent_failures"] = self._identify_persistent_failures(all_results)
        
        self._print_summary(summary)
        
        return {
            "summary": summary,
            "detailed_results": all_results,
        }
    
    def analyze_last_n_launches(self, n: int = 5) -> Dict[str, Any]:
        """Analyze the last N launches"""
        print(f"\n{'='*80}")
        print(f"Analyzing Last {n} Launches")
        print(f"{'='*80}\n")
        
        try:
            url = f"{self.client.config.api_base}/launch"
            params = {
                "page.size": n,
                "page.sort": "startTime,DESC"
            }
            
            response = self.client.session.get(url, params=params)
            response.raise_for_status()
            launches = response.json().get("content", [])
            
            if not launches:
                print("No launches found")
                return {}
            
            all_results = []
            summary = {
                "total_launches": len(launches),
                "total_failed_tests": 0,
                "defect_breakdown": {},
            }
            
            for idx, launch in enumerate(launches, 1):
                launch_id = launch.get("id")
                launch_name = launch.get("name", "Unknown")
                launch_number = launch.get("number", "N/A")
                
                print(f"\n[{idx}/{len(launches)}] Launch: {launch_name} (#{launch_number})")
                
                failed_tests = self.client.get_failed_tests(launch_id)
                print(f"  Failed tests: {len(failed_tests)}")
                
                summary["total_failed_tests"] += len(failed_tests)
                
                for test in failed_tests:
                    test_id = test.get("id")
                    test_name = test.get("name", "Unknown")
                    logs = self.client.get_test_logs(test_id)
                    
                    error_msg = test.get("issue", {}).get("comment", "")
                    
                    analysis = self.engine.analyze_comprehensive(
                        test_name=test_name,
                        error_message=error_msg,
                        logs=logs
                    )
                    
                    result = {
                        "launch_id": launch_id,
                        "launch_name": launch_name,
                        "test_id": test_id,
                        "test_name": test_name,
                        "analysis": analysis,
                    }
                    
                    all_results.append(result)
                    
                    category = analysis["category"]
                    summary["defect_breakdown"][category] = \
                        summary["defect_breakdown"].get(category, 0) + 1
            
            self._print_summary(summary)
            
            return {
                "summary": summary,
                "detailed_results": all_results,
            }
            
        except Exception as e:
            print(f"Error analyzing launches: {e}")
            return {}
    
    def _get_launches_in_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get all launches within date range"""
        try:
            url = f"{self.client.config.api_base}/launch"
            params = {
                "filter.gte.startTime": start_date,
                "filter.lte.startTime": end_date,
                "page.size": 50,
            }
            
            response = self.client.session.get(url, params=params)
            response.raise_for_status()
            return response.json().get("content", [])
        except Exception as e:
            print(f"Error fetching launches: {e}")
            return []
    
    def _identify_flaky_tests(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify tests that fail intermittently"""
        test_occurrences = {}
        
        for result in results:
            test_name = result["test_name"]
            if test_name not in test_occurrences:
                test_occurrences[test_name] = []
            test_occurrences[test_name].append(result)
        
        flaky_tests = []
        for test_name, occurrences in test_occurrences.items():
            if len(occurrences) >= 2:
                defect_types = [
                    occ["analysis"]["defect_type"] for occ in occurrences
                ]
                if len(set(defect_types)) > 1:
                    flaky_tests.append({
                        "test_name": test_name,
                        "failure_count": len(occurrences),
                        "defect_types": defect_types,
                    })
        
        return flaky_tests
    
    def _identify_persistent_failures(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify tests that consistently fail"""
        test_occurrences = {}
        
        for result in results:
            test_name = result["test_name"]
            if test_name not in test_occurrences:
                test_occurrences[test_name] = []
            test_occurrences[test_name].append(result)
        
        persistent_failures = []
        for test_name, occurrences in test_occurrences.items():
            if len(occurrences) >= 3:
                persistent_failures.append({
                    "test_name": test_name,
                    "failure_count": len(occurrences),
                    "category": occurrences[0]["analysis"]["category"],
                })
        
        persistent_failures.sort(key=lambda x: x["failure_count"], reverse=True)
        return persistent_failures[:10]
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print analysis summary"""
        print(f"\n{'='*80}")
        print("BATCH ANALYSIS SUMMARY")
        print(f"{'='*80}")
        
        print(f"\nTotal Launches Analyzed: {summary['total_launches']}")
        print(f"Total Failed Tests: {summary['total_failed_tests']}")
        
        print(f"\nDefect Breakdown:")
        for category, count in sorted(summary["defect_breakdown"].items()):
            percentage = (count / summary["total_failed_tests"] * 100) if summary["total_failed_tests"] > 0 else 0
            print(f"  {category}: {count} ({percentage:.1f}%)")
        
        if summary.get("flaky_tests"):
            print(f"\n🔄 Flaky Tests Detected: {len(summary['flaky_tests'])}")
            for flaky in summary["flaky_tests"][:5]:
                print(f"  - {flaky['test_name']} (failed {flaky['failure_count']} times)")
        
        if summary.get("persistent_failures"):
            print(f"\n⚠️  Persistent Failures: {len(summary['persistent_failures'])}")
            for persistent in summary["persistent_failures"][:5]:
                print(f"  - {persistent['test_name']} ({persistent['category']}, {persistent['failure_count']} failures)")
        
        print("\n" + "="*80)
    
    def export_report(self, data: Dict[str, Any], filename: str = "batch_report.json"):
        """Export batch analysis report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "analysis": data,
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Report exported to: {filename}")


def main():
    base_url = os.getenv("RP_BASE_URL")
    api_token = os.getenv("RP_API_TOKEN")
    project_name = os.getenv("RP_PROJECT_NAME")
    
    if not all([base_url, api_token, project_name]):
        print("❌ Missing configuration! Set RP_BASE_URL, RP_API_TOKEN, RP_PROJECT_NAME")
        sys.exit(1)
    
    config = RPConfig(
        base_url=base_url.rstrip('/'),
        api_token=api_token,
        project_name=project_name
    )
    
    analyzer = BatchAnalyzer(config)
    
    print("\n🔧 ReportPortal Batch Analyzer")
    print("\nOptions:")
    print("  1. Analyze last N launches")
    print("  2. Analyze date range")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    try:
        if choice == "1":
            n = int(input("How many launches? [5]: ") or "5")
            results = analyzer.analyze_last_n_launches(n)
            analyzer.export_report(results)
        
        elif choice == "2":
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
            results = analyzer.analyze_date_range(start_date, end_date)
            analyzer.export_report(results)
        
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()


