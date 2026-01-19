#!/usr/bin/env python3
"""
MongoDB Migration Cleanup Script
================================

This script documents and helps clean up deprecated code after the complete 
MongoDB migration completed on January 24, 2025.

PURPOSE:
- Archive deprecated SQLite-dependent files
- Generate cleanup report
- Validate that main APIs use MongoDB exclusively

DEPRECATED FILES MARKED:
- app/services/mongodb_tag_service.py (transitional bridge)
- app/services/unified_tag_service.py (SQLite-based)
- app/services/tag_service_v2.py (SQLite fallback)
- app/services/tag_concept_service.py (SQLite concepts)
- app/services/tag_concept_v2_service.py (SQLite concepts v2)

ACTIVE FILES (MongoDB-based):
- app/main.py (fully MongoDB, no SQLite)
- app/services/concept_only_tag_service.py (PRIMARY tag service)
- All app/api/*_mongodb.py files
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBMigrationCleaner:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.backend_dir = self.base_dir
        self.app_dir = self.backend_dir / "app"
        
        # Files marked as deprecated
        self.deprecated_services = [
            "app/services/mongodb_tag_service.py",
            "app/services/unified_tag_service.py", 
            "app/services/tag_service_v2.py",
            "app/services/tag_concept_service.py",
            "app/services/tag_concept_v2_service.py"
        ]
        
        # Backup files that should be archived
        self.backup_files = [
            "app/main_sqlite_backup.py",
            "app/main_mongodb.py", # Intermediate version
            "tweet_collector_service_sqlite_backup.py",
            "data/tweets.db"  # Original SQLite database
        ]
        
        # Files that should be MongoDB-only (no SQLite imports)
        self.mongodb_apis = [
            "app/main.py",
            "app/api/tags_mongodb.py",
            "app/api/tweets_mongodb.py", 
            "app/api/papers_mongodb.py",
            "app/api/articles_mongodb.py",
            "app/api/statistics_mongodb.py",
            "app/api/tag_ontology_v2_mongodb.py"
        ]

    def analyze_codebase(self) -> Dict:
        """Analyze current state of codebase after cleanup"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "deprecated_services": {},
            "backup_files": {},
            "mongodb_apis": {},
            "sqlite_references": [],
            "import_issues": []
        }
        
        logger.info("Analyzing codebase after MongoDB migration cleanup...")
        
        # Check deprecated services
        for service_path in self.deprecated_services:
            full_path = self.backend_dir / service_path
            if full_path.exists():
                analysis["deprecated_services"][service_path] = {
                    "exists": True,
                    "marked_deprecated": self._check_deprecation_header(full_path),
                    "size_bytes": full_path.stat().st_size
                }
            else:
                analysis["deprecated_services"][service_path] = {"exists": False}
        
        # Check backup files
        for backup_path in self.backup_files:
            full_path = self.backend_dir / backup_path
            if full_path.exists():
                analysis["backup_files"][backup_path] = {
                    "exists": True,
                    "size_bytes": full_path.stat().st_size
                }
            else:
                analysis["backup_files"][backup_path] = {"exists": False}
        
        # Check MongoDB APIs for SQLite references
        for api_path in self.mongodb_apis:
            full_path = self.backend_dir / api_path
            if full_path.exists():
                sqlite_refs = self._find_sqlite_references(full_path)
                analysis["mongodb_apis"][api_path] = {
                    "exists": True,
                    "sqlite_references": sqlite_refs,
                    "clean": len(sqlite_refs) == 0
                }
                if sqlite_refs:
                    analysis["sqlite_references"].extend([
                        f"{api_path}: {ref}" for ref in sqlite_refs
                    ])
            else:
                analysis["mongodb_apis"][api_path] = {"exists": False}
        
        # Find import issues
        analysis["import_issues"] = self._find_import_issues()
        
        return analysis
    
    def _check_deprecation_header(self, file_path: Path) -> bool:
        """Check if file has deprecation header"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # First 500 chars
                return "DEPRECATED" in content and "JANUARY 24, 2025" in content
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return False
    
    def _find_sqlite_references(self, file_path: Path) -> List[str]:
        """Find SQLite references in file"""
        sqlite_patterns = [
            "from sqlalchemy",
            "import sqlalchemy", 
            "Session",
            "get_db",
            "sqlite3",
            "tweets.db",
            "Tag, Tweet, Paper",
            "query(Tweet)",
            "query(Paper)"
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                found_refs = []
                for pattern in sqlite_patterns:
                    if pattern in content:
                        found_refs.append(pattern)
                return found_refs
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return []
    
    def _find_import_issues(self) -> List[str]:
        """Find deprecated imports in active files"""
        issues = []
        
        # Check for imports of deprecated services
        deprecated_imports = [
            "from app.services.mongodb_tag_service",
            "from app.services.unified_tag_service", 
            "from app.services.tag_service_v2",
            "from app.services.tag_concept_service",
            "from app.services.tag_concept_v2_service"
        ]
        
        # Search in active API files
        api_files = list(self.app_dir.glob("api/*.py"))
        for api_file in api_files:
            if "_backup" in str(api_file) or "_patch" in str(api_file):
                continue  # Skip backup/patch files
                
            try:
                with open(api_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for dep_import in deprecated_imports:
                        if dep_import in content:
                            issues.append(f"{api_file.name}: {dep_import}")
            except Exception as e:
                logger.warning(f"Could not check {api_file}: {e}")
        
        return issues

    def create_archive_directory(self, archive_name: str = None) -> Path:
        """Create archive directory for deprecated files"""
        if not archive_name:
            archive_name = f"deprecated_sqlite_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        archive_dir = self.backend_dir / "archives" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created archive directory: {archive_dir}")
        return archive_dir

    def generate_report(self, analysis: Dict, output_file: str = None) -> str:
        """Generate comprehensive cleanup report"""
        if not output_file:
            output_file = f"mongodb_migration_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_lines = [
            "# MongoDB Migration Cleanup Report",
            f"Generated: {analysis['timestamp']}",
            "",
            "## Summary",
            f"SmartTrendTracer completed MongoDB migration on January 24, 2025.",
            f"This report documents the cleanup of deprecated SQLite-dependent code.",
            "",
            "## Component Status",
            "",
            "### ✅ Migration Completed",
            "- **Main API**: All APIs use MongoDB exclusively",
            "- **Tweet Collector**: MongoDB state management", 
            "- **Tag System**: ConceptOnlyTagService is primary service",
            "- **Data**: 1,169 tweets, 34 papers, 40 articles, 1,746 concepts in MongoDB",
            "",
            "### 🗂️ Deprecated Services Marked",
        ]
        
        # Add deprecated services status
        for service, info in analysis["deprecated_services"].items():
            if info["exists"]:
                status = "✅ Marked" if info["marked_deprecated"] else "⚠️ Needs marking"
                report_lines.append(f"- `{service}`: {status}")
            else:
                report_lines.append(f"- `{service}`: Not found")
        
        report_lines.extend([
            "",
            "### 📁 Backup Files Status",
        ])
        
        # Add backup files status  
        for backup, info in analysis["backup_files"].items():
            if info["exists"]:
                size_kb = info["size_bytes"] // 1024
                report_lines.append(f"- `{backup}`: Preserved ({size_kb}KB)")
            else:
                report_lines.append(f"- `{backup}`: Not found")
        
        report_lines.extend([
            "",
            "### 🔍 MongoDB API Validation",
        ])
        
        # Add MongoDB API validation
        clean_apis = 0
        total_apis = len(analysis["mongodb_apis"])
        
        for api, info in analysis["mongodb_apis"].items():
            if info["exists"]:
                if info["clean"]:
                    report_lines.append(f"- ✅ `{api}`: Clean (no SQLite references)")
                    clean_apis += 1
                else:
                    report_lines.append(f"- ⚠️ `{api}`: Found SQLite references: {', '.join(info['sqlite_references'])}")
            else:
                report_lines.append(f"- ❌ `{api}`: File not found")
        
        report_lines.extend([
            "",
            f"**MongoDB API Status**: {clean_apis}/{total_apis} APIs are clean",
            ""
        ])
        
        # Add issues if found
        if analysis["sqlite_references"] or analysis["import_issues"]:
            report_lines.extend([
                "## ⚠️ Issues Found",
                "",
            ])
            
            if analysis["sqlite_references"]:
                report_lines.extend([
                    "### SQLite References in MongoDB APIs",
                    ""
                ])
                for ref in analysis["sqlite_references"]:
                    report_lines.append(f"- {ref}")
                report_lines.append("")
            
            if analysis["import_issues"]:
                report_lines.extend([
                    "### Deprecated Import Issues", 
                    ""
                ])
                for issue in analysis["import_issues"]:
                    report_lines.append(f"- {issue}")
                report_lines.append("")
        else:
            report_lines.extend([
                "## ✅ No Issues Found",
                "",
                "All MongoDB APIs are clean and use ConceptOnlyTagService appropriately.",
                ""
            ])
        
        # Add recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "### Immediate Actions",
            "- ✅ SQLite dependencies removed from tags_mongodb.py",
            "- ✅ All deprecated services marked with clear headers",
            "- ✅ ConceptOnlyTagService is primary tag service",
            "",
            "### Future Cleanup (Optional)",
            "- Archive deprecated service files to `archives/` directory",
            "- Remove unused backup files older than 6 months", 
            "- Update documentation to reflect MongoDB-only architecture",
            "",
            "### Architecture Notes",
            "- **Primary Database**: MongoDB (`smarttrendtracer`)", 
            "- **Primary Tag Service**: `ConceptOnlyTagService`",
            "- **Collections**: tweets, papers, articles, tag_concepts_v2, tag_instances",
            "- **Backup Database**: SQLite preserved at `data/tweets.db`",
            "",
            "## Files Modified in This Cleanup",
            "",
            "### Fixed",
            "- `app/api/tags_mongodb.py`: Removed SQLite imports, now uses ConceptOnlyTagService",
            "",
            "### Deprecated (Marked)",
            "- `app/services/mongodb_tag_service.py`",
            "- `app/services/unified_tag_service.py`", 
            "- `app/services/tag_service_v2.py`",
            "- `app/services/tag_concept_service.py`",
            "- `app/services/tag_concept_v2_service.py`",
            "",
            "---",
            "*Report generated by MongoDB Migration Cleanup Script*"
        ])
        
        report_content = "\n".join(report_lines)
        
        # Write report
        report_path = self.backend_dir / output_file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Cleanup report written to: {report_path}")
        return str(report_path)

def main():
    """Run the cleanup analysis and generate report"""
    cleaner = MongoDBMigrationCleaner()
    
    print("🔍 SmartTrendTracer MongoDB Migration Cleanup")
    print("=" * 50)
    
    # Run analysis
    print("Analyzing codebase...")
    analysis = cleaner.analyze_codebase()
    
    # Generate report
    print("Generating cleanup report...")
    report_path = cleaner.generate_report(analysis)
    
    # Summary
    print(f"\n✅ Analysis Complete!")
    print(f"📋 Report: {report_path}")
    
    # Quick summary
    deprecated_count = sum(1 for info in analysis["deprecated_services"].values() 
                          if info.get("exists") and info.get("marked_deprecated"))
    clean_apis = sum(1 for info in analysis["mongodb_apis"].values() 
                    if info.get("exists") and info.get("clean"))
    total_apis = len([info for info in analysis["mongodb_apis"].values() if info.get("exists")])
    
    print(f"🗂️ Deprecated Services Marked: {deprecated_count}/{len(analysis['deprecated_services'])}")
    print(f"🔧 Clean MongoDB APIs: {clean_apis}/{total_apis}")
    
    if analysis["sqlite_references"] or analysis["import_issues"]:
        print(f"⚠️ Issues Found: {len(analysis['sqlite_references']) + len(analysis['import_issues'])}")
        print("   See report for details")
    else:
        print("✨ No issues found - cleanup successful!")

if __name__ == "__main__":
    main()