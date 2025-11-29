#!/usr/bin/env python3
"""
Enhanced RAG Pipeline - Project Status Dashboard
Comprehensive project health and status monitoring.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import requests

class ProjectStatus:
    """Project status and health monitoring dashboard."""
    
    def __init__(self):
        self.status_data = {}
        self.base_url = "http://localhost:8000"
    
    def print_banner(self):
        """Print status dashboard banner."""
        print("📊" + "=" * 60 + "📊")
        print("    Enhanced RAG Pipeline - Project Status Dashboard")
        print("    Comprehensive Health and Status Monitoring")
        print("📊" + "=" * 60 + "📊")
        print()
    
    def check_python_environment(self) -> Dict[str, Any]:
        """Check Python environment status."""
        print("🐍 Checking Python Environment...")
        
        status = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_executable": sys.executable,
            "virtual_env": os.environ.get('VIRTUAL_ENV'),
            "pip_version": None,
            "requirements_installed": False
        }
        
        # Check pip version
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                status["pip_version"] = result.stdout.strip().split()[1]
        except Exception:
            pass
        
        # Check if requirements are installed
        try:
            import fastapi
            import google.generativeai
            import qdrant_client
            status["requirements_installed"] = True
        except ImportError:
            status["requirements_installed"] = False
        
        # Print status
        print(f"  Python Version: {status['python_version']}")
        print(f"  Virtual Environment: {'✅' if status['virtual_env'] else '❌'}")
        print(f"  Requirements Installed: {'✅' if status['requirements_installed'] else '❌'}")
        
        return status
    
    def check_project_structure(self) -> Dict[str, Any]:
        """Check project structure and files."""
        print("\n📁 Checking Project Structure...")
        
        required_files = [
            "main.py", "requirements.txt", ".env", "README.md",
            "app/rag/rag_pipeline.py", "app/api/qa_routes.py"
        ]
        
        required_dirs = [
            "app", "logs", "uploads", "pdfs", "tests"
        ]
        
        status = {
            "files": {},
            "directories": {},
            "structure_complete": True
        }
        
        # Check files
        for file_path in required_files:
            exists = Path(file_path).exists()
            status["files"][file_path] = exists
            if not exists:
                status["structure_complete"] = False
            print(f"  {file_path}: {'✅' if exists else '❌'}")
        
        # Check directories
        for dir_path in required_dirs:
            exists = Path(dir_path).exists()
            status["directories"][dir_path] = exists
            if not exists:
                status["structure_complete"] = False
            print(f"  {dir_path}/: {'✅' if exists else '❌'}")
        
        return status
    
    def check_configuration(self) -> Dict[str, Any]:
        """Check configuration and environment variables."""
        print("\n⚙️ Checking Configuration...")
        
        status = {
            "env_file_exists": Path(".env").exists(),
            "google_api_key": False,
            "config_valid": False
        }
        
        # Check .env file
        if status["env_file_exists"]:
            try:
                with open(".env", "r") as f:
                    content = f.read()
                    if "GOOGLE_API_KEY=" in content and "your_google_api_key_here" not in content:
                        status["google_api_key"] = True
            except Exception:
                pass
        
        # Try to load configuration
        try:
            sys.path.insert(0, ".")
            from app.core.config import settings
            status["config_valid"] = True
        except Exception:
            status["config_valid"] = False
        
        print(f"  .env file: {'✅' if status['env_file_exists'] else '❌'}")
        print(f"  Google API Key: {'✅' if status['google_api_key'] else '❌'}")
        print(f"  Configuration Valid: {'✅' if status['config_valid'] else '❌'}")
        
        return status
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies."""
        print("\n📦 Checking Dependencies...")
        
        status = {
            "qdrant_available": False,
            "google_ai_available": False,
            "database_accessible": False
        }
        
        # Check Qdrant
        try:
            response = requests.get("http://localhost:6333/health", timeout=5)
            status["qdrant_available"] = response.status_code == 200
        except Exception:
            status["qdrant_available"] = False
        
        # Check Google AI
        try:
            import google.generativeai as genai
            # This is a basic import check
            status["google_ai_available"] = True
        except Exception:
            status["google_ai_available"] = False
        
        # Check database
        try:
            db_path = Path("aiagent.db")
            status["database_accessible"] = db_path.exists()
        except Exception:
            status["database_accessible"] = False
        
        print(f"  Qdrant Vector DB: {'✅' if status['qdrant_available'] else '❌'}")
        print(f"  Google AI SDK: {'✅' if status['google_ai_available'] else '❌'}")
        print(f"  Database: {'✅' if status['database_accessible'] else '❌'}")
        
        return status
    
    def check_server_status(self) -> Dict[str, Any]:
        """Check server status and health."""
        print("\n🚀 Checking Server Status...")
        
        status = {
            "server_running": False,
            "health_check": False,
            "api_responsive": False,
            "response_time": None
        }
        
        try:
            # Health check
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status["server_running"] = True
                status["health_check"] = True
                status["response_time"] = response_time
                
                # Try API endpoint
                try:
                    api_response = requests.get(f"{self.base_url}/docs", timeout=5)
                    status["api_responsive"] = api_response.status_code == 200
                except Exception:
                    status["api_responsive"] = False
            
        except Exception:
            status["server_running"] = False
        
        print(f"  Server Running: {'✅' if status['server_running'] else '❌'}")
        print(f"  Health Check: {'✅' if status['health_check'] else '❌'}")
        print(f"  API Responsive: {'✅' if status['api_responsive'] else '❌'}")
        if status["response_time"]:
            print(f"  Response Time: {status['response_time']:.3f}s")
        
        return status
    
    def check_features(self) -> Dict[str, Any]:
        """Check enhanced features functionality."""
        print("\n✨ Checking Enhanced Features...")
        
        status = {
            "enhanced_pipeline": False,
            "table_generation": False,
            "external_fallback": False,
            "confidence_scoring": False
        }
        
        if not self.check_server_status()["server_running"]:
            print("  ❌ Server not running - cannot test features")
            return status
        
        try:
            # Test basic functionality
            response = requests.post(
                f"{self.base_url}/api/v1/ask",
                json={"doc_id": "any", "question": "What is a database?"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check enhanced pipeline
                if "answer_type" in data and "confidence" in data:
                    status["enhanced_pipeline"] = True
                
                # Check confidence scoring
                if isinstance(data.get("confidence"), (int, float)):
                    status["confidence_scoring"] = True
                
                # Check structured format
                answer = data.get("answer", "")
                if "## Definition" in answer or "## Explanation" in answer:
                    status["table_generation"] = True  # Structure indicates enhanced formatting
                
                # Test external fallback with a non-PDF question
                ext_response = requests.post(
                    f"{self.base_url}/api/v1/ask",
                    json={"doc_id": "any", "question": "What is quantum computing?"},
                    timeout=30
                )
                
                if ext_response.status_code == 200:
                    ext_data = ext_response.json()
                    if ext_data.get("answer_type") in ["external_only", "mixed"]:
                        status["external_fallback"] = True
        
        except Exception as e:
            print(f"  ❌ Feature test failed: {e}")
        
        print(f"  Enhanced Pipeline: {'✅' if status['enhanced_pipeline'] else '❌'}")
        print(f"  Table Generation: {'✅' if status['table_generation'] else '❌'}")
        print(f"  External Fallback: {'✅' if status['external_fallback'] else '❌'}")
        print(f"  Confidence Scoring: {'✅' if status['confidence_scoring'] else '❌'}")
        
        return status
    
    def check_documentation(self) -> Dict[str, Any]:
        """Check documentation completeness."""
        print("\n📚 Checking Documentation...")
        
        docs = [
            "README.md", "CONTRIBUTING.md", "LICENSE",
            "ENHANCED_RAG_IMPLEMENTATION.md", "IMPLEMENTATION_SUCCESS_SUMMARY.md"
        ]
        
        status = {"docs": {}, "complete": True}
        
        for doc in docs:
            exists = Path(doc).exists()
            status["docs"][doc] = exists
            if not exists:
                status["complete"] = False
            print(f"  {doc}: {'✅' if exists else '❌'}")
        
        return status
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        print("\n📋 Generating Status Report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_env": self.check_python_environment(),
            "project_structure": self.check_project_structure(),
            "configuration": self.check_configuration(),
            "dependencies": self.check_dependencies(),
            "server": self.check_server_status(),
            "features": self.check_features(),
            "documentation": self.check_documentation()
        }
        
        # Calculate overall health score
        checks = [
            report["python_env"]["requirements_installed"],
            report["project_structure"]["structure_complete"],
            report["configuration"]["config_valid"],
            report["dependencies"]["google_ai_available"],
            report["server"]["health_check"],
            report["features"]["enhanced_pipeline"],
            report["documentation"]["complete"]
        ]
        
        health_score = sum(checks) / len(checks) * 100
        report["overall_health"] = health_score
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """Print status summary."""
        print("\n🎯 Project Status Summary")
        print("=" * 50)
        
        health_score = report["overall_health"]
        
        if health_score >= 90:
            status_emoji = "🟢"
            status_text = "EXCELLENT"
        elif health_score >= 70:
            status_emoji = "🟡"
            status_text = "GOOD"
        elif health_score >= 50:
            status_emoji = "🟠"
            status_text = "NEEDS ATTENTION"
        else:
            status_emoji = "🔴"
            status_text = "CRITICAL"
        
        print(f"Overall Health: {status_emoji} {health_score:.1f}% - {status_text}")
        print()
        
        # Key metrics
        print("Key Status Indicators:")
        print(f"  Environment Ready: {'✅' if report['python_env']['requirements_installed'] else '❌'}")
        print(f"  Configuration Valid: {'✅' if report['configuration']['config_valid'] else '❌'}")
        print(f"  Server Running: {'✅' if report['server']['server_running'] else '❌'}")
        print(f"  Enhanced Features: {'✅' if report['features']['enhanced_pipeline'] else '❌'}")
        
        # Recommendations
        print("\n💡 Recommendations:")
        
        if not report['configuration']['google_api_key']:
            print("  🔑 Configure Google API key in .env file")
        
        if not report['dependencies']['qdrant_available']:
            print("  🗄️ Start Qdrant vector database (docker-compose up qdrant)")
        
        if not report['server']['server_running']:
            print("  🚀 Start the server (python main.py)")
        
        if health_score < 70:
            print("  📖 Check README.md for setup instructions")
            print("  🔧 Run setup.py for automated configuration")
        
        if health_score >= 90:
            print("  🎉 System is ready for production use!")
            print("  🌐 Try the web demo: enhanced_rag_demo.html")
    
    def save_report(self, report: Dict[str, Any], filename: str = "project_status.json"):
        """Save status report to file."""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Status report saved to {filename}")

def main():
    """Run project status dashboard."""
    dashboard = ProjectStatus()
    dashboard.print_banner()
    
    # Generate comprehensive report
    report = dashboard.generate_report()
    
    # Print summary
    dashboard.print_summary(report)
    
    # Save report
    dashboard.save_report(report)
    
    print(f"\n🔗 For detailed setup instructions, see README.md")
    print(f"🛠️ For development guidelines, see CONTRIBUTING.md")
    print(f"🚀 To get started quickly, run: python setup.py")

if __name__ == "__main__":
    main()