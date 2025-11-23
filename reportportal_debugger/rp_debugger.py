#!/usr/bin/env python3
"""
ReportPortal Debugger - Automated RCA and Debugging Tool
Fetches failed tests, analyzes them, and helps with debugging
"""

import os
import sys
import requests
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  'rich' library not found. Install with: pip install rich")


load_dotenv()


@dataclass
class RPConfig:
    base_url: str
    api_token: str
    project_name: str
    
    @property
    def api_base(self) -> str:
        return f"{self.base_url}/api/v1/{self.project_name}"
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }


class ReportPortalClient:
    def __init__(self, config: RPConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
    
    def test_connection(self) -> bool:
        try:
            url = f"{self.config.base_url}/api/v1/user"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def get_latest_launch(self) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.config.api_base}/launch/latest"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching latest launch: {e}")
            return None
    
    def get_launch_by_id(self, launch_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.config.api_base}/launch/{launch_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching launch {launch_id}: {e}")
            return None
    
    def get_failed_tests(self, launch_id: str) -> List[Dict[str, Any]]:
        try:
            url = f"{self.config.api_base}/item"
            params = {
                "filter.eq.launchId": launch_id,
                "filter.in.status": "FAILED",
                "page.size": 300,
                "isLatest": "false",
                "launchesLimit": 0
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("content", [])
        except Exception as e:
            print(f"Error fetching failed tests: {e}")
            return []
    
    def get_test_logs(self, test_item_id: str) -> List[Dict[str, Any]]:
        try:
            url = f"{self.config.api_base}/log"
            params = {
                "filter.eq.itemId": test_item_id,
                "page.size": 100
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("content", [])
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []
    
    def update_defect_type(self, test_item_id: str, defect_type: str, comment: str = "") -> bool:
        try:
            url = f"{self.config.api_base}/item/{test_item_id}/update"
            
            payload = {
                "issues": [
                    {
                        "issueType": defect_type,
                        "comment": comment
                    }
                ]
            }
            
            response = self.session.put(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating defect type: {e}")
            return False


class RCAAnalyzer:
    DEFECT_PATTERNS = {
        "pb001": {
            "name": "Product Bug",
            "patterns": [
                r"assertion.*failed",
                r"expected.*but.*got",
                r"incorrect.*value",
                r"validation.*error",
                r"business.*logic.*error",
                r"wrong.*result",
                r"invalid.*response",
                r"incorrect.*status.*code",
                r"missing.*field",
                r"unexpected.*data",
            ]
        },
        "ab001": {
            "name": "Automation Bug",
            "patterns": [
                r"element.*not.*found",
                r"timeout.*waiting",
                r"stale.*element",
                r"no.*such.*element",
                r"webdriver",
                r"selenium.*exception",
                r"element.*not.*interactable",
                r"element.*not.*visible",
                r"page.*not.*loaded",
                r"locator.*failed",
            ]
        },
        "si001": {
            "name": "System Issue",
            "patterns": [
                r"connection.*refused",
                r"network.*error",
                r"database.*error",
                r"out.*of.*memory",
                r"disk.*space",
                r"permission.*denied",
                r"503.*service.*unavailable",
                r"502.*bad.*gateway",
                r"500.*internal.*server",
                r"timeout.*exceeded",
                r"connection.*timeout",
                r"host.*unreachable",
            ]
        },
        "ti001": {
            "name": "To Investigate",
            "patterns": [
                r"unknown.*error",
                r"unexpected.*exception",
                r"null.*pointer",
                r"index.*out.*of.*bounds",
            ]
        }
    }
    
    @staticmethod
    def analyze_failure(test_name: str, test_data: Dict[str, Any], logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        error_message = ""
        
        if test_data.get("issue"):
            error_message = test_data["issue"].get("comment", "")
        
        status = test_data.get("status", "")
        
        combined_text = f"{test_name} {error_message} {status}"
        log_messages = []
        
        for log in logs:
            log_msg = log.get("message", "")
            log_messages.append(log_msg)
            combined_text += f" {log_msg}"
        
        combined_text = combined_text.lower()
        
        scores = {}
        matched_patterns = {}
        
        for defect_type, info in RCAAnalyzer.DEFECT_PATTERNS.items():
            scores[defect_type] = 0
            matched_patterns[defect_type] = []
            
            for pattern in info["patterns"]:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    scores[defect_type] += 1
                    matched_patterns[defect_type].append(pattern)
        
        if max(scores.values()) == 0:
            return {
                "defect_type": "ti001",
                "confidence": "low",
                "category": "To Investigate",
                "reason": "No clear pattern detected - requires manual investigation",
                "matched_patterns": [],
                "error_message": error_message,
                "log_summary": log_messages[:5]
            }
        
        suggested_defect = max(scores, key=scores.get)
        confidence_score = scores[suggested_defect]
        
        if confidence_score >= 3:
            confidence = "high"
        elif confidence_score >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "defect_type": suggested_defect,
            "confidence": confidence,
            "category": RCAAnalyzer.DEFECT_PATTERNS[suggested_defect]["name"],
            "reason": f"Matched {confidence_score} patterns",
            "matched_patterns": matched_patterns[suggested_defect],
            "error_message": error_message,
            "log_summary": log_messages[:5]
        }
    
    @staticmethod
    def get_debug_suggestions(analysis: Dict[str, Any]) -> List[str]:
        suggestions = []
        defect_type = analysis["defect_type"]
        
        if defect_type == "pb001":
            suggestions = [
                "🐛 Verify the expected vs actual values in the assertion",
                "📝 Check if business logic has changed recently",
                "🔍 Review recent code changes in the tested feature",
                "🧪 Try reproducing the issue manually",
                "📊 Check if the data/test environment is correct"
            ]
        elif defect_type == "ab001":
            suggestions = [
                "🔧 Check if element locators need updating",
                "⏱️ Add explicit waits for dynamic elements",
                "🖥️ Verify page load completion before interactions",
                "🎯 Use more stable locators (ID, data-testid)",
                "🔄 Check if UI changes broke the automation"
            ]
        elif defect_type == "si001":
            suggestions = [
                "🌐 Check network connectivity and service health",
                "💾 Verify database/API availability",
                "🔐 Check authentication tokens and permissions",
                "📡 Review service logs for infrastructure issues",
                "⚙️ Verify environment configuration"
            ]
        else:
            suggestions = [
                "🔍 Review complete error stack trace",
                "📋 Check test execution logs",
                "🧩 Verify test data and preconditions",
                "🔄 Try running the test again",
                "👥 Consult with team members"
            ]
        
        return suggestions


class RPDebugger:
    def __init__(self, config: RPConfig):
        self.client = ReportPortalClient(config)
        self.analyzer = RCAAnalyzer()
        self.console = Console() if RICH_AVAILABLE else None
    
    def print_info(self, message: str):
        if self.console:
            self.console.print(f"[blue]ℹ️  {message}[/blue]")
        else:
            print(f"ℹ️  {message}")
    
    def print_success(self, message: str):
        if self.console:
            self.console.print(f"[green]✅ {message}[/green]")
        else:
            print(f"✅ {message}")
    
    def print_error(self, message: str):
        if self.console:
            self.console.print(f"[red]❌ {message}[/red]")
        else:
            print(f"❌ {message}")
    
    def print_warning(self, message: str):
        if self.console:
            self.console.print(f"[yellow]⚠️  {message}[/yellow]")
        else:
            print(f"⚠️  {message}")
    
    def debug_launch(self, launch_id: Optional[str] = None, auto_update: bool = False):
        self.print_info("Testing connection to ReportPortal...")
        
        if not self.client.test_connection():
            self.print_error("Failed to connect to ReportPortal. Check your configuration.")
            return
        
        self.print_success("Connected to ReportPortal successfully!")
        
        if not launch_id:
            self.print_info("Fetching latest test launch...")
            launch = self.client.get_latest_launch()
        else:
            self.print_info(f"Fetching launch: {launch_id}")
            launch = self.client.get_launch_by_id(launch_id)
        
        if not launch:
            self.print_error("Failed to fetch launch")
            return
        
        launch_id = launch.get("id")
        launch_name = launch.get("name", "Unknown")
        launch_number = launch.get("number", "N/A")
        
        self.print_success(f"Found Launch: {launch_name} (#{launch_number})")
        
        self.print_info("Fetching failed tests...")
        failed_tests = self.client.get_failed_tests(launch_id)
        
        if not failed_tests:
            self.print_success("No failed tests found! 🎉")
            return
        
        self.print_warning(f"Found {len(failed_tests)} failed test(s)")
        print("\n" + "="*80 + "\n")
        
        results = []
        
        for idx, test in enumerate(failed_tests, 1):
            test_id = test.get("id")
            test_name = test.get("name", "Unknown")
            
            print(f"\n{'='*80}")
            print(f"[{idx}/{len(failed_tests)}] 🔍 DEBUGGING: {test_name}")
            print(f"{'='*80}")
            print(f"Test ID: {test_id}")
            
            logs = self.client.get_test_logs(test_id)
            print(f"Fetched {len(logs)} log entries")
            
            analysis = self.analyzer.analyze_failure(test_name, test, logs)
            
            print(f"\n📊 ROOT CAUSE ANALYSIS:")
            print(f"   Category: {analysis['category']}")
            print(f"   Defect Type: {analysis['defect_type']}")
            print(f"   Confidence: {analysis['confidence'].upper()}")
            print(f"   Reason: {analysis['reason']}")
            
            if analysis['matched_patterns']:
                print(f"\n🎯 Matched Patterns:")
                for pattern in analysis['matched_patterns'][:5]:
                    print(f"   - {pattern}")
            
            if analysis['error_message']:
                print(f"\n💥 Error Message:")
                print(f"   {analysis['error_message'][:300]}")
            
            if analysis['log_summary']:
                print(f"\n📋 Key Log Entries:")
                for log_entry in analysis['log_summary'][:3]:
                    if log_entry.strip():
                        print(f"   - {log_entry[:150]}")
            
            suggestions = self.analyzer.get_debug_suggestions(analysis)
            print(f"\n💡 DEBUG SUGGESTIONS:")
            for suggestion in suggestions:
                print(f"   {suggestion}")
            
            if auto_update:
                comment = f"Auto-RCA: {analysis['category']} (Confidence: {analysis['confidence']}) - {analysis['reason']}"
                print(f"\n🔄 Updating defect type in ReportPortal...")
                success = self.client.update_defect_type(test_id, analysis['defect_type'], comment)
                if success:
                    self.print_success("Defect type updated successfully!")
                else:
                    self.print_error("Failed to update defect type")
            
            results.append({
                "test_name": test_name,
                "test_id": test_id,
                "analysis": analysis
            })
            
            print("\n")
        
        print("\n" + "="*80)
        print("📈 SUMMARY")
        print("="*80)
        
        summary = {}
        for result in results:
            category = result['analysis']['category']
            summary[category] = summary.get(category, 0) + 1
        
        print(f"\nTotal Failed Tests: {len(results)}")
        for category, count in sorted(summary.items()):
            print(f"  {category}: {count}")
        
        print("\n" + "="*80 + "\n")
        
        return results


def main():
    print("\n" + "="*80)
    print("🔧 ReportPortal Debugger - Automated RCA Tool")
    print("="*80 + "\n")
    
    base_url = os.getenv("RP_BASE_URL")
    api_token = os.getenv("RP_API_TOKEN")
    project_name = os.getenv("RP_PROJECT_NAME")
    launch_id = os.getenv("RP_LAUNCH_ID", "")
    auto_update = os.getenv("RP_AUTO_UPDATE", "false").lower() == "true"
    
    if not all([base_url, api_token, project_name]):
        print("❌ Missing configuration!")
        print("\nPlease create a .env file with:")
        print("  RP_BASE_URL=https://your-reportportal-url.com")
        print("  RP_API_TOKEN=your_api_token_here")
        print("  RP_PROJECT_NAME=your_project_name")
        print("\nOr set these environment variables.")
        sys.exit(1)
    
    config = RPConfig(
        base_url=base_url.rstrip('/'),
        api_token=api_token,
        project_name=project_name
    )
    
    debugger = RPDebugger(config)
    
    try:
        debugger.debug_launch(
            launch_id=launch_id if launch_id else None,
            auto_update=auto_update
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


