#!/usr/bin/env python3
"""
MCP Server Integration Demo
This demonstrates how our backtest execution system integrates with the MCP server
to provide real HaasOnline API functionality.
"""

import requests
import json
import time
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPBacktestIntegration:
    """Integration between our backtest system and MCP server"""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        self.session = requests.Session()
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get MCP server and HaasOnline API status"""
        try:
            response = self.session.get(f"{self.mcp_base_url}/status")
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def discover_labs(self) -> List[Dict[str, Any]]:
        """Discover available labs (replaces our mock lab discovery)"""
        try:
            response = self.session.get(f"{self.mcp_base_url}/get_all_labs")
            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return data.get("Data", [])
            return []
        except Exception as e:
            logger.error(f"Error discovering labs: {e}")
            return []
    
    def clone_lab_for_testing(self, source_lab_id: str, new_name: str) -> Optional[str]:
        """Clone a lab for testing (replaces our mock lab creation)"""
        try:
            payload = {"lab_id": source_lab_id, "new_name": new_name}
            response = self.session.post(
                f"{self.mcp_base_url}/clone_lab",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("lab_id")
            return None
        except Exception as e:
            logger.error(f"Error cloning lab: {e}")
            return None
    
    def start_backtest_execution(self, lab_id: str, period: str = "2_years") -> Dict[str, Any]:
        """Start backtest execution with period presets"""
        try:
            payload = {
                "lab_id": lab_id,
                "period": period,
                "send_email": False
            }
            response = self.session.post(
                f"{self.mcp_base_url}/start_lab_execution",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_backtest_results(self, lab_id: str, page_length: int = 10) -> Dict[str, Any]:
        """Get backtest results"""
        try:
            payload = {
                "lab_id": lab_id,
                "next_page_id": -1,
                "page_length": page_length
            }
            response = self.session.post(
                f"{self.mcp_base_url}/get_backtest_results",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def clone_to_multiple_markets(self, source_lab_id: str, assets: List[str]) -> Dict[str, Any]:
        """Clone lab to multiple markets using MCP bulk operations"""
        try:
            targets = [{"asset": asset, "exchange": "BINANCEFUTURES"} for asset in assets]
            payload = {
                "source_lab_id": source_lab_id,
                "targets": targets,
                "lab_name_template": "Auto Test - {primary} - {suffix}"
            }
            response = self.session.post(
                f"{self.mcp_base_url}/clone_lab_to_markets",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def start_multiple_labs(self, lab_ids: List[str], period: str = "1_year") -> Dict[str, Any]:
        """Start multiple labs with bulk execution"""
        try:
            payload = {
                "lab_ids": lab_ids,
                "period": period,
                "send_email": False
            }
            response = self.session.post(
                f"{self.mcp_base_url}/start_multiple_labs",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_lab_performance(self, lab_id: str) -> Dict[str, Any]:
        """Analyze lab performance using our heuristics (integrated with real data)"""
        results = self.get_backtest_results(lab_id, page_length=100)
        
        if not results.get("Success"):
            return {"error": "Could not get backtest results"}
        
        backtest_data = results.get("Data", {}).get("I", [])
        
        if not backtest_data:
            return {"analysis": "No backtest data available"}
        
        # Apply our heuristics analysis to real data
        analysis = {
            "total_backtests": len(backtest_data),
            "completed_backtests": len([b for b in backtest_data if b.get("ST") == 3]),
            "performance_summary": self._analyze_performance_metrics(backtest_data),
            "parameter_analysis": self._analyze_parameters(backtest_data),
            "recommendations": self._generate_recommendations(backtest_data)
        }
        
        return analysis
    
    def _analyze_performance_metrics(self, backtest_data: List[Dict]) -> Dict[str, Any]:
        """Analyze performance metrics from real backtest data"""
        completed = [b for b in backtest_data if b.get("ST") == 3]
        
        if not completed:
            return {"status": "No completed backtests"}
        
        # Extract performance data
        roi_values = []
        profit_values = []
        
        for backtest in completed:
            stats = backtest.get("S", {})
            if stats:
                roi = stats.get("ReturnOnInvestment", 0.0)
                profit = stats.get("RealizedProfits", 0.0)
                roi_values.append(roi)
                profit_values.append(profit)
        
        if roi_values:
            return {
                "avg_roi": sum(roi_values) / len(roi_values),
                "max_roi": max(roi_values),
                "min_roi": min(roi_values),
                "avg_profit": sum(profit_values) / len(profit_values),
                "profitable_configs": len([r for r in roi_values if r > 0]),
                "total_configs": len(roi_values)
            }
        
        return {"status": "No performance data available"}
    
    def _analyze_parameters(self, backtest_data: List[Dict]) -> Dict[str, Any]:
        """Analyze parameter patterns in successful backtests"""
        completed = [b for b in backtest_data if b.get("ST") == 3]
        
        if not completed:
            return {"status": "No completed backtests"}
        
        # Analyze parameter frequency
        parameter_analysis = {}
        
        for backtest in completed:
            params = backtest.get("P", {})
            roi = backtest.get("S", {}).get("ReturnOnInvestment", 0.0)
            
            if roi > 0:  # Only analyze profitable configs
                for param_key, param_value in params.items():
                    if param_key not in parameter_analysis:
                        parameter_analysis[param_key] = {}
                    
                    if param_value not in parameter_analysis[param_key]:
                        parameter_analysis[param_key][param_value] = {"count": 0, "total_roi": 0.0}
                    
                    parameter_analysis[param_key][param_value]["count"] += 1
                    parameter_analysis[param_key][param_value]["total_roi"] += roi
        
        # Find best parameters
        best_parameters = {}
        for param_key, values in parameter_analysis.items():
            if values:
                best_value = max(values.items(), 
                               key=lambda x: x[1]["total_roi"] / x[1]["count"])
                best_parameters[param_key] = {
                    "value": best_value[0],
                    "avg_roi": best_value[1]["total_roi"] / best_value[1]["count"],
                    "frequency": best_value[1]["count"]
                }
        
        return {
            "total_parameters_analyzed": len(parameter_analysis),
            "best_parameters": best_parameters
        }
    
    def _generate_recommendations(self, backtest_data: List[Dict]) -> List[str]:
        """Generate recommendations based on backtest analysis"""
        recommendations = []
        
        completed = [b for b in backtest_data if b.get("ST") == 3]
        total_backtests = len(backtest_data)
        completed_backtests = len(completed)
        
        if completed_backtests == 0:
            recommendations.append("No completed backtests - check lab configuration")
            return recommendations
        
        completion_rate = completed_backtests / total_backtests
        if completion_rate < 0.8:
            recommendations.append(f"Low completion rate ({completion_rate:.1%}) - review parameter ranges")
        
        # Analyze profitability
        profitable = len([b for b in completed 
                         if b.get("S", {}).get("ReturnOnInvestment", 0.0) > 0])
        
        if profitable == 0:
            recommendations.append("No profitable configurations found - consider different strategy or parameters")
        elif profitable / completed_backtests < 0.2:
            recommendations.append("Low profitability rate - narrow parameter ranges around best performers")
        else:
            recommendations.append(f"Good profitability rate ({profitable/completed_backtests:.1%}) - consider expanding successful parameter ranges")
        
        return recommendations

def demonstrate_integration():
    """Demonstrate the complete integration workflow"""
    print("MCP Server Integration Demonstration")
    print("=" * 50)
    
    integration = MCPBacktestIntegration()
    
    # Step 1: Check server status
    print("\n1. Checking MCP server status...")
    status = integration.get_server_status()
    if "error" in status:
        print(f"❌ Server error: {status['error']}")
        return
    
    print(f"✅ Server status: {status.get('status', 'unknown')}")
    print(f"✅ HaasOnline API: {'connected' if status.get('haas_api_connected') else 'disconnected'}")
    
    # Step 2: Discover available labs
    print("\n2. Discovering available labs...")
    labs = integration.discover_labs()
    print(f"✅ Found {len(labs)} labs")
    
    if not labs:
        print("❌ No labs available for testing")
        return
    
    # Show some lab details
    for i, lab in enumerate(labs[:3]):
        status_map = {0: "Created", 1: "Running", 2: "Paused", 3: "Completed", 4: "Error"}
        lab_status = status_map.get(lab.get("S", 0), "Unknown")
        print(f"   - {lab.get('N', 'Unknown')[:50]}... (Status: {lab_status})")
    
    # Step 3: Find a good source lab for testing
    print("\n3. Selecting source lab for testing...")
    source_lab = None
    for lab in labs:
        if lab.get("S") == 3 and lab.get("CB", 0) > 0:  # Completed with results
            source_lab = lab
            break
    
    if not source_lab:
        source_lab = labs[0]  # Use first available
    
    print(f"✅ Selected lab: {source_lab.get('N', 'Unknown')}")
    print(f"   Lab ID: {source_lab.get('LID')}")
    print(f"   Completed backtests: {source_lab.get('CB', 0)}")
    
    # Step 4: Analyze existing lab performance
    print("\n4. Analyzing lab performance...")
    analysis = integration.analyze_lab_performance(source_lab.get('LID'))
    
    if "error" not in analysis:
        print(f"✅ Analysis completed:")
        print(f"   Total backtests: {analysis.get('total_backtests', 0)}")
        print(f"   Completed: {analysis.get('completed_backtests', 0)}")
        
        perf = analysis.get('performance_summary', {})
        if 'avg_roi' in perf:
            print(f"   Average ROI: {perf['avg_roi']:.2f}%")
            print(f"   Profitable configs: {perf['profitable_configs']}/{perf['total_configs']}")
        
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print("   Recommendations:")
            for rec in recommendations[:2]:
                print(f"     - {rec}")
    
    # Step 5: Clone lab for new testing
    print("\n5. Cloning lab for new testing...")
    new_lab_id = integration.clone_lab_for_testing(
        source_lab.get('LID'),
        f"Integration Test - {int(time.time())}"
    )
    
    if new_lab_id:
        print(f"✅ Lab cloned successfully: {new_lab_id}")
        
        # Step 6: Start backtest execution with period preset
        print("\n6. Starting backtest execution...")
        execution_result = integration.start_backtest_execution(new_lab_id, "1_year")
        
        if "error" not in execution_result:
            print("✅ Backtest execution started successfully")
            print(f"   Period: {execution_result.get('period', 'unknown')}")
            print(f"   Start time: {execution_result.get('start_unix', 'unknown')}")
            print(f"   End time: {execution_result.get('end_unix', 'unknown')}")
        else:
            print(f"❌ Execution failed: {execution_result['error']}")
    
    # Step 7: Demonstrate bulk operations
    print("\n7. Demonstrating bulk operations...")
    if len(labs) >= 2:
        lab_ids = [lab.get('LID') for lab in labs[:2]]
        bulk_result = integration.start_multiple_labs(lab_ids, "6_months")
        
        if "error" not in bulk_result:
            print(f"✅ Bulk execution started for {len(lab_ids)} labs")
        else:
            print(f"❌ Bulk execution failed: {bulk_result['error']}")
    
    # Step 8: Demonstrate market cloning
    print("\n8. Demonstrating market cloning...")
    clone_result = integration.clone_to_multiple_markets(
        source_lab.get('LID'),
        ["BTC", "ETH", "SOL"]
    )
    
    if "error" not in clone_result:
        print("✅ Lab cloned to multiple markets")
        cloned_labs = clone_result.get('cloned_labs', [])
        print(f"   Created {len(cloned_labs)} new labs")
    else:
        print(f"❌ Market cloning failed: {clone_result['error']}")
    
    print("\n" + "=" * 50)
    print("Integration demonstration completed!")
    
    print("\n🎯 Key Integration Benefits:")
    print("✅ Real HaasOnline API connectivity")
    print("✅ Automatic timestamp calculation with period presets")
    print("✅ Bulk operations for multiple labs")
    print("✅ Real backtest data analysis")
    print("✅ Automated lab cloning and market distribution")
    print("✅ Performance analysis with actual trading results")
    
    print("\n🔧 Our System Enhancement:")
    print("- Backtest execution system provides orchestration")
    print("- MCP server provides HaasOnline API access")
    print("- Heuristics analysis works with real data")
    print("- Account management integrates with real accounts")
    print("- Lab configuration templates work with real labs")

if __name__ == "__main__":
    demonstrate_integration()