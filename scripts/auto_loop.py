import os
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Project Root
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
BRAIN_DIR = BASE_DIR / ".agent" / "brain"
STATE_FILE = BRAIN_DIR / "state.md"
REPORTS_DIR = BRAIN_DIR / "reports"

def get_latest_patrol_summary():
    """最新のパトロールレポートから要約を取得する"""
    try:
        reports = sorted(REPORTS_DIR.glob("patrol_*.md"), reverse=True)
        if not reports:
            return "最近の変更はないみたいだよ。"
        
        latest = reports[0]
        changes = []
        with open(latest, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("- `"):
                    item = line.strip().replace("- `", "").replace("`", "")
                    changes.append(item)
                if len(changes) >= 3: break
        
        if not changes:
            return "目立ったファイル変更は見つからなかったよ。"
        return f"最新の変更には {', '.join(changes)} が含まれているよ。"
    except Exception as e:
        return f"パトロール情報の取得に失敗したよ: {e}"

def update_state_with_thought(message):
    """state.md の冒頭にエージェントの独り言を挿入する"""
    if not STATE_FILE.exists():
        return
        
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"## 🤖 エージェントの独り言 ({timestamp})\n> {message}\n\n"
    
    # 既に独り言がある場合は置換、なければ挿入
    if "## 🤖 エージェントの独り言" in content:
        # 簡易的な置換（次のセクションまでを入れ替える）
        parts = content.split("## ", 2)
        if len(parts) > 2:
            new_content = header + "## " + parts[2]
        else:
            new_content = header
    else:
        new_content = header + content
        
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

def main_loop():
    print(f"🚀 Agent-In-The-Box: Auto-Loop Engine Started.")
    print(f"ワークスペースを常駐監視して、state.md を更新します。")
    
    last_patrol = 0
    
    while True:
        now = time.time()
        
        # 2時間ごとにパトロール実行
        if now - last_patrol > 7200:
            print(f"[{datetime.now()}] Running Patrol...")
            try:
                subprocess.run([sys.executable, str(SCRIPTS_DIR / "patrol.py")], capture_output=True)
                summary = get_latest_patrol_summary()
                update_state_with_thought(f"パトロールを完了したよ。{summary}")
                print(f"   -> State updated: {summary}")
            except Exception as e:
                print(f"Error during patrol: {e}")
            last_patrol = now
            
        time.sleep(60) # 1分おきにチェック

if __name__ == "__main__":
    main_loop()
