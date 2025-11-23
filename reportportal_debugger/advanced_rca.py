#!/usr/bin/env python3
"""
Advanced RCA Engine for ReportPortal
Enhanced analysis using pattern matching, log analysis, and historical data
Based on ReportPortal's official API structure
"""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter
import json


class AdvancedRCAEngine:
    """
    Advanced Root Cause Analysis Engine
    Uses multiple analysis techniques to determine failure causes
    """
    
    PRODUCT_BUG_PATTERNS = [
        (r"assertion\s*(error|failed|failure)", 3),
        (r"expected\s+.*\s+but\s+(got|was|received)", 3),
        (r"incorrect\s+(value|result|data|response)", 2),
        (r"validation\s+(error|failed|failure)", 2),
        (r"wrong\s+(status|code|result|value)", 2),
        (r"(invalid|missing|unexpected)\s+(field|attribute|property)", 2),
        (r"business\s+logic\s+(error|failure)", 3),
        (r"status\s+code\s+\d{3}", 1),
        (r"api\s+(returned|response)", 1),
    ]
    
    AUTOMATION_BUG_PATTERNS = [
        (r"element\s+(not\s+found|could\s+not\s+be\s+located)", 4),
        (r"timeout\s+(waiting|expired|exceeded)", 3),
        (r"stale\s+element", 4),
        (r"no\s+such\s+element", 4),
        (r"(selenium|webdriver|playwright|cypress)\s+", 3),
        (r"element\s+(not\s+visible|not\s+interactable)", 3),
        (r"locator\s+(failed|invalid|not\s+found)", 3),
        (r"page\s+(not\s+loaded|load\s+timeout)", 2),
        (r"click\s+intercepted", 3),
        (r"javascript\s+error", 2),
    ]
    
    SYSTEM_ISSUE_PATTERNS = [
        (r"connection\s+(refused|reset|timeout|failed)", 4),
        (r"network\s+(error|timeout|unavailable)", 3),
        (r"database\s+(connection|error|timeout)", 3),
        (r"(503|502|504|500)\s+", 4),
        (r"service\s+unavailable", 4),
        (r"out\s+of\s+memory", 4),
        (r"disk\s+(space|full)", 3),
        (r"permission\s+denied", 3),
        (r"cannot\s+connect\s+to", 3),
        (r"host\s+(unreachable|not\s+found)", 3),
    ]
    
    def __init__(self):
        self.historical_patterns = {}
    
    def analyze_comprehensive(
        self,
        test_name: str,
        error_message: str,
        logs: List[Dict[str, Any]],
        stack_trace: str = "",
        test_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive RCA analysis using multiple techniques
        
        Args:
            test_name: Name of the failed test
            error_message: Error message from the test
            logs: List of log entries
            stack_trace: Stack trace if available
            test_history: Historical data for this test
            
        Returns:
            Detailed analysis result with confidence scores
        """
        
        combined_text = self._prepare_text(test_name, error_message, logs, stack_trace)
        
        scores = {
            "pb001": self._score_patterns(combined_text, self.PRODUCT_BUG_PATTERNS),
            "ab001": self._score_patterns(combined_text, self.AUTOMATION_BUG_PATTERNS),
            "si001": self._score_patterns(combined_text, self.SYSTEM_ISSUE_PATTERNS),
        }
        
        if test_history:
            historical_score = self._analyze_history(test_history)
            for defect_type, boost in historical_score.items():
                scores[defect_type] = scores.get(defect_type, 0) + boost
        
        keyword_analysis = self._analyze_keywords(combined_text)
        for defect_type, boost in keyword_analysis.items():
            scores[defect_type] = scores.get(defect_type, 0) + boost
        
        suggested_defect, confidence = self._determine_defect_type(scores)
        
        return {
            "defect_type": suggested_defect,
            "confidence": confidence,
            "confidence_score": max(scores.values()) if scores else 0,
            "scores": scores,
            "category": self._get_category_name(suggested_defect),
            "analysis_details": {
                "primary_indicators": self._extract_indicators(combined_text, suggested_defect),
                "error_summary": error_message[:300] if error_message else "No error message",
                "log_analysis": self._analyze_logs(logs),
            },
            "recommendations": self._get_recommendations(suggested_defect, combined_text),
        }
    
    def _prepare_text(
        self, 
        test_name: str, 
        error_message: str, 
        logs: List[Dict[str, Any]], 
        stack_trace: str
    ) -> str:
        """Combine all text sources for analysis"""
        text_parts = [test_name, error_message, stack_trace]
        
        for log in logs[:10]:
            text_parts.append(log.get("message", ""))
        
        return " ".join(text_parts)
    
    def _score_patterns(self, text: str, patterns: List[Tuple[str, int]]) -> int:
        """Score text against pattern list with weights"""
        score = 0
        text_lower = text.lower()
        
        for pattern, weight in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += weight
        
        return score
    
    def _analyze_keywords(self, text: str) -> Dict[str, int]:
        """Analyze specific keywords for additional scoring"""
        keywords = {
            "pb001": ["assert", "expect", "should", "incorrect", "wrong", "invalid"],
            "ab001": ["selenium", "webdriver", "locator", "xpath", "css", "timeout"],
            "si001": ["network", "connection", "server", "database", "service", "unavailable"],
        }
        
        scores = {}
        text_lower = text.lower()
        
        for defect_type, words in keywords.items():
            count = sum(1 for word in words if word in text_lower)
            scores[defect_type] = count
        
        return scores
    
    def _analyze_history(self, test_history: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze historical patterns for this test"""
        if not test_history:
            return {}
        
        defect_counts = Counter()
        for entry in test_history:
            if entry.get("issue"):
                defect_type = entry["issue"].get("issueType", "")
                if defect_type:
                    defect_counts[defect_type] += 1
        
        if not defect_counts:
            return {}
        
        most_common_defect, count = defect_counts.most_common(1)[0]
        
        if count >= 2:
            return {most_common_defect: 2}
        
        return {}
    
    def _determine_defect_type(self, scores: Dict[str, int]) -> Tuple[str, str]:
        """Determine defect type and confidence based on scores"""
        if not scores or max(scores.values()) == 0:
            return "ti001", "low"
        
        max_score = max(scores.values())
        suggested_defect = max(scores, key=scores.get)
        
        if max_score >= 8:
            confidence = "high"
        elif max_score >= 4:
            confidence = "medium"
        else:
            confidence = "low"
        
        return suggested_defect, confidence
    
    def _get_category_name(self, defect_type: str) -> str:
        """Get human-readable category name"""
        categories = {
            "pb001": "Product Bug",
            "ab001": "Automation Bug",
            "si001": "System Issue",
            "ti001": "To Investigate",
            "nd001": "No Defect",
        }
        return categories.get(defect_type, "Unknown")
    
    def _extract_indicators(self, text: str, defect_type: str) -> List[str]:
        """Extract key indicators that led to the classification"""
        indicators = []
        
        patterns = {
            "pb001": self.PRODUCT_BUG_PATTERNS,
            "ab001": self.AUTOMATION_BUG_PATTERNS,
            "si001": self.SYSTEM_ISSUE_PATTERNS,
        }
        
        if defect_type in patterns:
            text_lower = text.lower()
            for pattern, _ in patterns[defect_type]:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    indicators.extend(matches[:2])
        
        return indicators[:5]
    
    def _analyze_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze log entries for patterns"""
        if not logs:
            return {"log_count": 0, "error_logs": 0, "warning_logs": 0}
        
        error_count = 0
        warning_count = 0
        
        for log in logs:
            level = log.get("level", "").lower()
            if level in ["error", "fatal", "severe"]:
                error_count += 1
            elif level in ["warning", "warn"]:
                warning_count += 1
        
        return {
            "log_count": len(logs),
            "error_logs": error_count,
            "warning_logs": warning_count,
            "has_critical_errors": error_count > 0,
        }
    
    def _get_recommendations(self, defect_type: str, text: str) -> List[str]:
        """Get contextual recommendations based on defect type and content"""
        base_recommendations = {
            "pb001": [
                "🔍 Review the assertion/validation logic",
                "📊 Compare expected vs actual values",
                "🔄 Check for recent changes in business logic",
                "🧪 Reproduce the issue manually",
                "📝 Verify test data correctness",
            ],
            "ab001": [
                "🎯 Update element locators to be more stable",
                "⏱️ Add appropriate wait conditions",
                "🔧 Check if UI structure has changed",
                "💻 Review browser/driver versions",
                "🧩 Verify test automation framework setup",
            ],
            "si001": [
                "🌐 Check service/API health status",
                "🔌 Verify network connectivity",
                "💾 Review database connection status",
                "⚙️ Check environment configuration",
                "📡 Review infrastructure logs",
            ],
            "ti001": [
                "🔍 Review complete error stack trace",
                "📋 Analyze all test logs in detail",
                "🔄 Re-run the test to confirm failure",
                "👥 Consult with development team",
                "🧪 Check test prerequisites and data",
            ],
        }
        
        recommendations = base_recommendations.get(defect_type, [])
        
        text_lower = text.lower()
        if "timeout" in text_lower:
            recommendations.insert(0, "⏰ Increase timeout values or optimize performance")
        
        if "404" in text_lower or "not found" in text_lower:
            recommendations.insert(0, "🔗 Verify endpoint/URL is correct and accessible")
        
        if "401" in text_lower or "403" in text_lower or "unauthorized" in text_lower:
            recommendations.insert(0, "🔐 Check authentication/authorization credentials")
        
        return recommendations[:7]


def export_analysis_report(analysis_results: List[Dict[str, Any]], output_file: str = "rca_report.json"):
    """
    Export detailed analysis results to JSON file
    
    Args:
        analysis_results: List of analysis results
        output_file: Output filename
    """
    report = {
        "timestamp": str(datetime.now()),
        "total_failures": len(analysis_results),
        "summary": {},
        "detailed_results": analysis_results,
    }
    
    for result in analysis_results:
        category = result.get("analysis", {}).get("category", "Unknown")
        report["summary"][category] = report["summary"].get(category, 0) + 1
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Analysis report exported to: {output_file}")


if __name__ == "__main__":
    from datetime import datetime
    
    engine = AdvancedRCAEngine()
    
    test_example = {
        "name": "test_user_login_with_invalid_credentials",
        "error": "AssertionError: Expected status code 401 but got 200",
        "logs": [
            {"message": "Login API called with invalid credentials", "level": "INFO"},
            {"message": "Response status: 200", "level": "ERROR"},
            {"message": "Authentication validation bypassed", "level": "ERROR"},
        ],
        "stack_trace": "at login_test.py line 42",
    }
    
    result = engine.analyze_comprehensive(
        test_name=test_example["name"],
        error_message=test_example["error"],
        logs=test_example["logs"],
        stack_trace=test_example["stack_trace"]
    )
    
    print("\n" + "="*80)
    print("ADVANCED RCA ANALYSIS EXAMPLE")
    print("="*80)
    print(json.dumps(result, indent=2))


