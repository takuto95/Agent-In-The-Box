import os
import time
from pathlib import Path
from datetime import datetime, timedelta

# Project Root
BASE_DIR = Path(__file__).parent.parent
BRAIN_DIR = BASE_DIR / ".agent" / "brain"
REPORTS_DIR = BRAIN_DIR / "reports"

def patrol_workspace():
    """ワークスペースの変更を検知し、レポートを作成する"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    print(f"[INFO] Patrol started at {now.isoformat()}")
    
    modified_files = []
    # ワークスペース全体をスキャン（特定のディレクトリを除く）
    exclude_dirs = {".git", "node_modules", "__pycache__", ".venv"}
    
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            file_path = Path(root) / f
            try:
                # ignore self-generated reports
                if ".agent" in str(file_path): continue
                
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > yesterday:
                    modified_files.append((file_path, mtime))
            except:
                continue
                
    # レポート作成
    report_file = REPORTS_DIR / f"patrol_{now.strftime('%Y%m%d_%H%M')}.md"
    
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write(f"# パトロール報告 ({now.strftime('%Y-%m-%d %H:%M')})\n\n")
        
        if not modified_files:
            rf.write("過去24時間にワークスペースの変更は検知されませんでした。\n")
        else:
            rf.write("## 🛠️ 最近の変更点\n")
            for path, mtime in sorted(modified_files, key=lambda x: x[1], reverse=True):
                try:
                    rel_path = path.relative_to(BASE_DIR)
                    rf.write(f"- `{rel_path}` ({mtime.strftime('%H:%M')})\n")
                except:
                    rf.write(f"- `{path}` ({mtime.strftime('%H:%M')})\n")
                
        rf.write("\n## 🧠 エージェントの気づき\n")
        rf.write("- あなたの変更から、私が学習し、Cursorでの回答精度を高めるための準備をしています。\n")
        rf.write("- 重要な変更があれば、それをベースに新たなADRを起案することを提案します。\n")

    print(f"[SUCCESS] Patrol report generated: {report_file}")
    return report_file

if __name__ == "__main__":
    patrol_workspace()
