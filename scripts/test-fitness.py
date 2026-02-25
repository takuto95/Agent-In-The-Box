#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alter-Ego 進化的適合度関数 (Fitness Function) 検証スクリプト
ADR-0100 に基づき、システムの「健康状態」を診断します。
"""

import os
import sys
from pathlib import Path
import json

BASE_DIR = Path(__file__).parent.parent.parent
BOOKS_DIR = BASE_DIR / "knowledge" / "books"
SCRIPTS_DIR = BASE_DIR / "scripts"
ADR_DIR = BASE_DIR / "docs" / "adr"
LOGS_DIR = BASE_DIR / "logs"

def check_essential_scripts():
    """主要なスクリプトが存在するかチェック"""
    print("[1/4] Essential Scripts Check...")
    essentials = [
        "knowledge/extract-oreilly-learning.py",
        "knowledge/extract-text-from-screenshots.py",
        "knowledge/extract-kindle-book.py",
        "knowledge/index-book-pages.py",
        "patrol/clickup_adapter.py",
        "analyze/analyze_thoughts.py"
    ]
    missing = []
    for s in essentials:
        if not (SCRIPTS_DIR / s).exists():
            missing.append(s)
    
    if not missing:
        print("✅ All essential scripts found.")
        return True
    else:
        print(f"❌ Missing scripts: {', '.join(missing)}")
        return False

def check_book_indexes():
    """書籍MDに対してPage Indexが存在するかチェック"""
    print("\n[2/4] Book Knowledge Integrity Check...")
    md_files = list(BOOKS_DIR.glob("*.md"))
    if not md_files:
        print("⚠️ No book MD files found.")
        return True
    
    missing_index = []
    for md in md_files:
        if md.name == "README.md": continue
        index_file = md.with_name(f"{md.stem}_page_index.json")
        if not index_file.exists():
            missing_index.append(md.name)
            
    if not missing_index:
        print(f"✅ All {len(md_files)} books have page indexes.")
        
        # New: Check for potential duplicates (Principle 3: Scalability/Efficiency)
        redundant_books = []
        for md in md_files:
            if md.stat().st_size > 1024 * 1024: # > 1MB might still have duplicates
                redundant_books.append(md.name)
        
        if redundant_books:
            print(f"⚠️ Large books detected (>1MB), verify deduplication: {len(redundant_books)}")
        
        return True
    else:
        print(f"⚠️ Books missing page index: {len(missing_index)}")
        for m in missing_index[:3]:
            print(f"  - {m}")
        return False

def check_adr_health():
    """ADRのステータスとリンクの健全性をチェック (日本語/英語両対応)"""
    print("\n[3/5] ADR Governance Check...")
    adrs = list(ADR_DIR.rglob("0*.md"))
    tags = {"Proposed": 0, "Accepted": 0, "Deprecated": 0, "Superseeded": 0, "Unknown": 0}
    
    for adr in adrs:
        try:
            content = adr.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = adr.read_text(encoding="shift-jis")
            except:
                content = adr.read_text(encoding="utf-8", errors="replace")
        
        # Check multiple patterns
        is_proposed = any([
            "Status: Proposed" in content,
            "ステータス: Proposed" in content,
            "## ステータス\nProposed" in content,
            "**ステータス**: Proposed" in content,
            ("ステータス" in content and "提案中" in content)
        ])
        
        is_accepted = any([
            "Status: Accepted" in content,
            "ステータス: Accepted" in content,
            "## ステータス\nAccepted" in content,
            "**ステータス**: Accepted" in content,
            "Accepted（" in content,
            ("ステータス" in content and "承認済み" in content)
        ])
        
        is_deprecated = any([
            "Status: Deprecated" in content,
            "ステータス: Deprecated" in content,
            "## ステータス\nDeprecated" in content,
            "**ステータス**: Deprecated" in content,
            "Deprecated（" in content,
            ("ステータス" in content and "廃止" in content)
        ])
        
        is_superseeded = any([
            "Status: Superseeded" in content,
            "ステータス: Superseeded" in content,
            "## ステータス\nSuperseeded" in content,
            "**ステータス**: Superseeded" in content,
            "Superseeded（" in content
        ])
        
        if is_proposed:
            tags["Proposed"] += 1
        elif is_accepted:
            tags["Accepted"] += 1
        elif is_deprecated:
            tags["Deprecated"] += 1
        elif is_superseeded:
            tags["Superseeded"] += 1
        else:
            tags["Unknown"] += 1
            
    print(f"📊 ADR Statistics (Total: {len(adrs)}):")
    for k, v in tags.items():
        print(f"  - {k}: {v}")
    
    if tags["Unknown"] > 0:
        print(f"⚠️ {tags['Unknown']} ADRs have undefined status.")
        return False
    return True

def check_dependencies():
    """requirements.txt と実際のインポート可能性をチェック"""
    print("\n[4/5] Dependency Environment Check...")
    import importlib.util
    
    # (import_name, display_name)
    libs = [
        ("playwright", "playwright"),
        ("google.cloud.vision", "google.cloud.vision"),
        ("mobi", "mobi"),
        ("requests", "requests"),
        ("boto3", "boto3"),
        ("feedparser", "feedparser")
    ]
    missing = []
    for import_name, display_name in libs:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            print(f"✅ {display_name}: OK")
        else:
            print(f"❌ {display_name}: Missing")
            missing.append(display_name)
    
    if not missing:
        return True
    elif "playwright" in missing or "requests" in missing:
        return False # 必須系
    else:
        print("⚠️ Optional dependencies missing.")
        return True

def check_api_connectivity():
    """外部サービス (GitHub, ClickUp, AWS) のAPI疎通を確認 (ADR-0101 + STRATEGIC-PLAN)"""
    print("\n[5/5] External API Connectivity Check (Clawdbot-Native)...")
    
    from dotenv import load_dotenv
    import requests
    import boto3
    from botocore.exceptions import ClientError
    
    load_dotenv()
    
    results = {}
    
    # 1. GitHub Test
    token = os.getenv("GITHUB_TOKEN")
    if token and "your_" not in token:
        try:
            resp = requests.get("https://api.github.com/user", headers={"Authorization": f"token {token}"})
            results["GitHub API"] = resp.status_code == 200
        except:
            results["GitHub API"] = False
    else:
        results["GitHub API"] = "(Not Configured)"

    # 2. ClickUp Test
    cu_key = os.getenv("CLICKUP_API_KEY")
    if cu_key and "your_" not in cu_key:
        try:
            resp = requests.get("https://api.clickup.com/api/v2/user", headers={"Authorization": cu_key})
            results["ClickUp API"] = resp.status_code == 200
        except:
            results["ClickUp API"] = False
    else:
        results["ClickUp API"] = "(Not Configured)"

    # 3. AWS Test
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    if aws_key and "your_" not in aws_key:
        try:
            sts = boto3.client("sts")
            sts.get_caller_identity()
            results["AWS API"] = True
        except ClientError:
            results["AWS API"] = False
        except:
            results["AWS API"] = False
    else:
        results["AWS API"] = "(Not Configured)"

    all_ok = True
    for service, status in results.items():
        if status is True:
            print(f"✅ {service}: Connected")
        elif status == "(Not Configured)":
            print(f"⚠️ {service}: Skipped (Placeholder detected)")
        else:
            print(f"❌ {service}: Disconnected/Auth Failed")
            all_ok = False
    return all_ok

def main():
    print("="*50)
    print("Alter-Ego System Health Check (Fitness Functions)")
    print("="*50)
    
    results = [
        check_essential_scripts(),
        check_book_indexes(),
        check_adr_health(),
        check_dependencies(),
        check_api_connectivity()
    ]
    
    # Get ADR stats for detailed judgment
    adrs = list(ADR_DIR.glob("0*.md"))
    unknown_count = 0
    for adr in adrs:
        try:
            content = adr.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = adr.read_text(encoding="shift-jis")
            except:
                content = adr.read_text(encoding="utf-8", errors="replace")
        is_unknown = not any([
            "Status: Proposed" in content, "Status: Accepted" in content,
            "Status: Deprecated" in content, "Status: Superseeded" in content,
            "ステータス: Proposed" in content, "ステータス: Accepted" in content,
            "ステータス: Deprecated" in content, "ステータス: Superseeded" in content,
            "## ステータス\nProposed" in content, "## ステータス\nAccepted" in content,
            "## ステータス\nDeprecated" in content, "## ステータス\nSuperseeded" in content,
            "**ステータス**: Proposed" in content, "**ステータス**: Accepted" in content,
            "**ステータス**: Deprecated" in content, "**ステータス**: Superseeded" in content,
            "Accepted（" in content, "Proposed（" in content,
            "Deprecated（" in content, "Superseeded（" in content,
            ("ステータス" in content and "承認済み" in content),
            ("ステータス" in content and "提案中" in content),
            ("ステータス" in content and "廃止" in content)
        ])
        if is_unknown:
            unknown_count += 1
    
    print("\n" + "="*50)
    if all(results):
        print("✨ SYSTEM HEALTH: EXCELLENT (Production-Ready)")
    elif results[0] and results[3] and unknown_count == 0:
        print("✅ SYSTEM HEALTH: GOOD (Functional but needs polish)")
    elif results[0] and results[3]:
        print("⚠️ SYSTEM HEALTH: FUNCTIONAL (Infrastructure OK, Governance lagging)")
    else:
        print("🚨 SYSTEM HEALTH: CRITICAL (Principles violated)")
    print("="*50)

if __name__ == "__main__":
    main()
