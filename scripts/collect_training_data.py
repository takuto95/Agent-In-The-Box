import os
import json
from pathlib import Path

# LoRA Training Data Collector
# Purpose: Extract decision patterns from ADRs to build user-specific personality data.

BASE_DIR = Path(__file__).parent.parent
ADR_DIR = BASE_DIR / "docs" / "adr"
TRAINING_DATA_DIR = BASE_DIR / "data" / "training"
QA_PAIRS_FILE = TRAINING_DATA_DIR / "qa_pairs.jsonl"

def extract_from_adrs():
    print(f"📖 Scanning ADRs in {ADR_DIR}...")
    adr_files = list(ADR_DIR.rglob("*.md"))
    
    pairs = []
    for adr in adr_files:
        try:
            content = adr.read_text(encoding="utf-8")
        except:
            continue
            
        title = adr.stem.replace("-", " ")
        
        # Simple extraction logic tailored for the Seed ADR format
        purpose = ""
        decision = ""
        
        if "## コンテキスト" in content:
            purpose = content.split("## コンテキスト")[1].split("##")[0].strip()
        
        if "## 決定" in content:
            decision = content.split("## 決定")[1].split("##")[0].strip()
            
        if purpose and decision:
            pairs.append({
                "instruction": f"このプロジェクトにおける '{title}' の決定事項とその背景を教えてください。",
                "context": purpose,
                "response": f"はい、{title} に関しては以下のように決定しています。\n\n【背景】\n{purpose}\n\n【決定事項】\n{decision}"
            })
            
    return pairs

def main():
    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    pairs = extract_from_adrs()
    
    if not pairs:
        print("データが見つからないよ。ADRをもっと書いてみてね！")
        return

    with open(QA_PAIRS_FILE, "a", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            
    print(f"✅ {len(pairs)} 件の学習用データを {QA_PAIRS_FILE} に保存したよ。")
    print("将来、君専用のLLMをLoRA学習させる際の種火になります。")

if __name__ == "__main__":
    main()
