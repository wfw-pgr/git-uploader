#!/usr/bin/env python3
# fix_ctetra_only.py
# 用途: BDF/Nastran 風ファイル中の CTETRA / CTETRA* カードだけを検出して、
# 継続行マーカーを除き、指定の固定幅フォーマットで1行に書き直す。

import sys
import re
from pathlib import Path

CTETRA_FMT = "".join(["%8s","%8d","%8d","%8d","%8d","%8d","%8d"])  # ユーザー指定のフォーマット

def normalize_ctetra_block(lines_block):
    """
    lines_block: list[str] -- 最初の行が CTETRA*... で、そのあと継続行 (先頭が '*') が続く想定
    戻り値: (ok_bool, output_lines_list, warning_msg)
      ok_bool: True なら変換成功、output_lines_list に置換後1行が入る
    """
    # 1) 各行の継続マーキングを取り除いて連結
    parts = []
    for idx, ln in enumerate(lines_block):
        s = ln.rstrip("\n\r")
        # 行末のツール固有の継続トークン例: "...E0000001" を削る
        s = re.sub(r'E0+\d+\s*$', '', s, flags=re.IGNORECASE)
        # 継続行（先頭）に "*0000001" のようなインデックスがある場合は除去
        if idx > 0:
            s = re.sub(r'^\*0*\d+\s*', '', s)
        parts.append(s.strip())
    combined = " ".join(p for p in parts if p != "")
    # 2) 数字を抽出（CTETRA では整数が期待される）
    nums = re.findall(r'-?\d+', combined)
    if len(nums) < 6:
        return (False, lines_block, f"CTETRA: 数字が {len(nums)} 個しか見つかりません（期待: >=6）。元のまま出力します。")
    # 3) 最初の 6 個を取ってフォーマット出力（必要なら他のノードは切り捨て）
    try:
        fields = [int(n) for n in nums[:6]]
    except Exception as e:
        return (False, lines_block, f"CTETRA: 数値変換エラー: {e}. 元のまま出力します。")
    out_line = CTETRA_FMT % ( "CTETRA", fields[0], fields[1], fields[2], fields[3], fields[4], fields[5] )
    return (True, [out_line + "\n"], "")

def process_file(in_path: Path, out_path: Path, inplace=False):
    raw = in_path.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)
    out_lines = []
    i = 0
    warnings = []
    while i < len(lines):
        ln = lines[i]
        # 大文字小文字の両方に対応、先頭に空白があってもOK
        if re.match(r'^\s*CTETRA\b', ln, flags=re.IGNORECASE):
            # collect this line and any immediate following lines that begin with '*' (継続行)
            block = [ln]
            j = i + 1
            while j < len(lines) and re.match(r'^\s*\*', lines[j]):
                block.append(lines[j])
                j += 1
            ok, replaced, warn = normalize_ctetra_block(block)
            if ok:
                out_lines.extend(replaced)
            else:
                out_lines.extend(block)  # 変換できなければ元をそのまま出す
                if warn:
                    warnings.append(f"行 {i+1}: {warn}")
            i = j
            continue
        else:
            out_lines.append(ln)
            i += 1

    out_text = "".join(out_lines)
    out_path.write_text(out_text, encoding="utf-8")
    return warnings

def main():
    if len(sys.argv) not in (3,4):
        print("Usage: python fix_ctetra_only.py input.bdf output.bdf")
        sys.exit(1)
    inf = Path(sys.argv[1])
    outf = Path(sys.argv[2])
    if not inf.exists():
        print("入力ファイルが見つかりません:", inf)
        sys.exit(1)
    # 作業前にバックアップを推奨
    warnings = process_file(inf, outf)
    print(f"書き出し完了: {outf}")
    if warnings:
        print("注意:")
        for w in warnings:
            print(" -", w)
    else:
        print("変換に問題は検出されませんでした。")

if __name__ == "__main__":
    main()
