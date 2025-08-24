#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Epic 1 End-to-End Validation Runner
Comprehensive production readiness validation for crypto market integration
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'epic1_e2e_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class Epic1E2EValidator:
    """Epic 1 End-to-End Validation Orchestrator"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.test_results = {}
        self.performance_metrics = {}
        self.validation_report = {}
        
        # Test configuration
        self.test_suites = [
            "TestE2EHistoricalDataPipeline",
            "TestE2EServiceIntegration", 
            "TestE2EPerformanceValidation",
            "TestE2EProductionReadiness"
        ]
        
        # Performance thresholds
        self.performance_thresholds = {
            "data_loading_rate": 1000,  # records/second
            "streaming_capacity": 10000,  # messages/second
            "api_response_time": 200,  # milliseconds
            "memory_limit": 2048,  # MB
            "test_pass_rate": 95  # percentage
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Execute comprehensive Epic 1 validation"""
        logger.info("🚀 Starting Epic 1 Comprehensive E2E Validation")
        logger.info("=" * 60)
        
        try:
            # Phase 1: Environment validation
            self._validate_environment()
            
            # Phase 2: Execute test suites
            self._execute_test_suites()
            
            # Phase 3: Performance analysis
            self._analyze_performance()
            
            # Phase 4: Generate validation report
            self._generate_validation_report()
            
            # Phase 5: Production readiness assessment
            self._assess_production_readiness()
            
            logger.info("✅ Epic 1 Comprehensive Validation COMPLETED")
            
        except Exception as e:
            logger.error(f"❌ Epic 1 Validation FAILED: {e}")
            self.validation_report["status"] = "FAILED"
            self.validation_report["error"] = str(e)
        
        return self.validation_report
    
    def _validate_environment(self):
        """Validate test environment setup"""
        logger.info("🔍 Phase 1: Environment Validation")
        
        environment_checks = {
            "python_version": sys.version_info >= (3, 8),
            "zvt_imports": self._check_zvt_imports(),
            "test_files": self._check_test_files(),
            "dependencies": self._check_dependencies()
        }
        
        for check, result in environment_checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {check}: {status}")
        
        if not all(environment_checks.values()):
            raise RuntimeError("Environment validation failed")
        
        self.validation_report["environment"] = environment_checks
        logger.info("✅ Environment validation completed")
    
    def _check_zvt_imports(self) -> bool:
        """Check if ZVT modules can be imported"""
        try:
            from zvt.services.crypto.data_loader import CryptoDataLoader
            from zvt.services.crypto.stream_service import CryptoStreamService
            from zvt.services.crypto.api_ingestion import CryptoAPIIngestion
            return True
        except ImportError as e:
            logger.error(f"ZVT import failed: {e}")
            return False
    
    def _check_test_files(self) -> bool:
        """Check if test files exist"""
        required_files = [
            "test_epic1_e2e_integration.py",
            "EPIC_1_END_TO_END_TESTING_PLAN.md"
        ]
        
        test_dir = Path(__file__).parent
        for file in required_files:
            if not (test_dir / file).exists():
                logger.error(f"Missing test file: {file}")
                return False
        return True
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        try:
            import pytest
            import pandas
            import psutil
            import asyncio
            return True
        except ImportError as e:
            logger.error(f"Dependency check failed: {e}")
            return False
    
    def _execute_test_suites(self):
        """Execute all test suites"""
        logger.info("🧪 Phase 2: Test Suite Execution")
        
        test_file = Path(__file__).parent / "test_epic1_e2e_integration.py"
        
        # Execute pytest with detailed output (simplified for compatibility)
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v", "--tb=short", "--capture=no",
            "--junitxml=epic1_e2e_results.xml"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        execution_time = time.time() - start_time
        
        # Parse test results
        self.test_results = {
            "exit_code": result.returncode,
            "execution_time": execution_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        # Log results
        if self.test_results["success"]:
            logger.info(f"✅ Test execution completed in {execution_time:.2f} seconds")
        else:
            logger.error(f"❌ Test execution failed (exit code: {result.returncode})")
            logger.error(f"STDERR: {result.stderr}")
        
        # Extract test metrics from output
        self._extract_test_metrics()
    
    def _extract_test_metrics(self):
        """Extract test metrics from pytest output"""
        stdout = self.test_results.get("stdout", "")
        
        # Parse pytest summary
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line and ('failed' in line or 'error' in line):
                # Parse pytest summary line
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        try:
                            passed = int(parts[i-1])
                            self.performance_metrics["tests_passed"] = passed
                        except (ValueError, IndexError):
                            pass
                    elif part == "failed":
                        try:
                            failed = int(parts[i-1])
                            self.performance_metrics["tests_failed"] = failed
                        except (ValueError, IndexError):
                            pass
        
        # Calculate pass rate
        passed = self.performance_metrics.get("tests_passed", 0)
        failed = self.performance_metrics.get("tests_failed", 0)
        total = passed + failed
        
        if total > 0:
            pass_rate = (passed / total) * 100
            self.performance_metrics["test_pass_rate"] = pass_rate
            logger.info(f"Test pass rate: {pass_rate:.1f}% ({passed}/{total})")
    
    def _analyze_performance(self):
        """Analyze performance metrics"""
        logger.info("📊 Phase 3: Performance Analysis")
        
        # Performance validation
        performance_status = {}
        
        for metric, threshold in self.performance_thresholds.items():
            actual = self.performance_metrics.get(metric, 0)
            passed = actual >= threshold
            performance_status[metric] = {
                "actual": actual,
                "threshold": threshold,
                "passed": passed
            }
            
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {metric}: {actual} (threshold: {threshold}) {status}")
        
        self.validation_report["performance"] = performance_status
        
        # Overall performance assessment
        all_passed = all(status["passed"] for status in performance_status.values())
        logger.info(f"Overall performance: {'✅ PASS' if all_passed else '❌ FAIL'}")
    
    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        logger.info("📋 Phase 4: Validation Report Generation")
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        self.validation_report.update({
            "validation_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "validator_version": "1.0.0"
            },
            "test_execution": self.test_results,
            "performance_metrics": self.performance_metrics,
            "summary": self._generate_summary()
        })
        
        # Save report to file
        report_file = f"epic1_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_report, f, indent=2, default=str)
        
        logger.info(f"Validation report saved to: {report_file}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary"""
        test_success = self.test_results.get("success", False)
        performance_passed = all(
            status.get("passed", False) 
            for status in self.validation_report.get("performance", {}).values()
        )
        
        overall_status = "PASS" if test_success and performance_passed else "FAIL"
        
        return {
            "overall_status": overall_status,
            "test_execution_status": "PASS" if test_success else "FAIL",
            "performance_status": "PASS" if performance_passed else "FAIL",
            "tests_passed": self.performance_metrics.get("tests_passed", 0),
            "tests_failed": self.performance_metrics.get("tests_failed", 0),
            "test_pass_rate": self.performance_metrics.get("test_pass_rate", 0),
            "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60
        }
    
    def _assess_production_readiness(self):
        """Assess overall production readiness"""
        logger.info("🎯 Phase 5: Production Readiness Assessment")
        
        summary = self.validation_report["summary"]
        
        # Production readiness criteria
        criteria = {
            "test_execution": summary["test_execution_status"] == "PASS",
            "performance_benchmarks": summary["performance_status"] == "PASS", 
            "pass_rate_threshold": summary["test_pass_rate"] >= 95,
            "environment_validation": all(self.validation_report["environment"].values()),
            "no_critical_failures": summary["tests_failed"] == 0
        }
        
        # Assessment
        readiness_score = sum(criteria.values()) / len(criteria) * 100
        production_ready = readiness_score >= 90
        
        self.validation_report["production_readiness"] = {
            "criteria": criteria,
            "readiness_score": readiness_score,
            "production_ready": production_ready,
            "recommendation": self._get_recommendation(production_ready, criteria)
        }
        
        # Final assessment
        status = "✅ PRODUCTION READY" if production_ready else "❌ NOT READY"
        logger.info(f"Production Readiness Score: {readiness_score:.1f}%")
        logger.info(f"Final Assessment: {status}")
        
        # Log recommendations
        recommendation = self.validation_report["production_readiness"]["recommendation"]
        logger.info(f"Recommendation: {recommendation}")
    
    def _get_recommendation(self, production_ready: bool, criteria: Dict[str, bool]) -> str:
        """Get production readiness recommendation"""
        if production_ready:
            return "Epic 1 is READY for production deployment and Epic 2 development"
        
        failed_criteria = [key for key, passed in criteria.items() if not passed]
        return f"Address the following issues before production: {', '.join(failed_criteria)}"
    
    def print_final_report(self):
        """Print final validation report"""
        logger.info("\n" + "=" * 80)
        logger.info("🏆 EPIC 1 END-TO-END VALIDATION FINAL REPORT")
        logger.info("=" * 80)
        
        summary = self.validation_report["summary"]
        readiness = self.validation_report["production_readiness"]
        
        logger.info(f"Overall Status: {summary['overall_status']}")
        logger.info(f"Test Execution: {summary['test_execution_status']}")
        logger.info(f"Performance: {summary['performance_status']}")
        logger.info(f"Tests Passed: {summary['tests_passed']}")
        logger.info(f"Tests Failed: {summary['tests_failed']}")
        logger.info(f"Pass Rate: {summary['test_pass_rate']:.1f}%")
        logger.info(f"Duration: {summary['duration_minutes']:.1f} minutes")
        logger.info(f"Production Ready: {'YES' if readiness['production_ready'] else 'NO'}")
        logger.info(f"Readiness Score: {readiness['readiness_score']:.1f}%")
        logger.info(f"Recommendation: {readiness['recommendation']}")
        
        logger.info("=" * 80)


def main():
    """Main execution function"""
    try:
        validator = Epic1E2EValidator()
        validator.run_comprehensive_validation()
        validator.print_final_report()
        
        # Exit with appropriate code
        production_ready = validator.validation_report["production_readiness"]["production_ready"]
        sys.exit(0 if production_ready else 1)
        
    except Exception as e:
        logger.error(f"Epic 1 validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()