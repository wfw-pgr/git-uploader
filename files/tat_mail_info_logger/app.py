#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

# ★ ステータス（記事ページ側と揃える）
ALLOWED_STATUS = ["New", "既読", "要再確認"]

# 目次表でのプレビュー量（文字数）
PREVIEW_MAX_CHARS = 2600


def safe_load_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def ensure_user_fields(d: Dict[str, Any]) -> Dict[str, Any]:
    # 追記欄の既定値だけ保証
    if "user_comment" not in d:
        d["user_comment"] = ""
    if "user_rating" not in d:
        d["user_rating"] = None
    if "user_status" not in d:
        d["user_status"] = "New"
    if "user_updated_at" not in d:
        d["user_updated_at"] = None

    # 既存データ互換（旧: new/reviewed/shared/ignored → 新: New/既読/要再確認）
    old = str(d.get("user_status") or "")
    mapping = {
        "new": "New",
        "reviewed": "既読",
        "shared": "既読",
        "ignored": "要再確認",
    }
    if old in mapping:
        d["user_status"] = mapping[old]

    if d.get("user_status") not in ALLOWED_STATUS:
        d["user_status"] = "New"

    # ratingをintに正規化
    r = d.get("user_rating")
    if r is not None:
        try:
            r = int(r)
            d["user_rating"] = r if 1 <= r <= 5 else None
        except Exception:
            d["user_rating"] = None

    return d


def join_list(x: Any) -> str:
    if not x:
        return ""
    if isinstance(x, list):
        return ", ".join(str(i) for i in x)
    return str(x)


def normalize_text(x: Any) -> str:
    if not x:
        return ""
    return str(x).replace("\r\n", "\n").replace("\r", "\n")


def preview_text(x: Any) -> str:
    t = " ".join(normalize_text(x).split())
    if len(t) > PREVIEW_MAX_CHARS:
        t = t[:PREVIEW_MAX_CHARS] + "…"
    return t


def title_of(d: Dict[str, Any]) -> str:
    return str(d.get("title") or d.get("subject") or d.get("file_name") or "untitled")


def parse_date_for_sort(d: Dict[str, Any]) -> pd.Timestamp:
    for k in ["date", "email_date_iso"]:
        v = d.get(k)
        if v:
            try:
                return pd.to_datetime(v, errors="raise")
            except Exception:
                pass
    return pd.Timestamp.min


def rating_to_stars(r: Any) -> str:
    """目次表示専用：★のみ（☆☆なし）"""
    if r is None or (isinstance(r, float) and pd.isna(r)):
        return ""
    try:
        rr = int(r)
    except Exception:
        return ""
    rr = max(0, min(5, rr))
    return "★" * rr if rr > 0 else ""


def list_json_files(root: Path) -> List[Path]:
    return sorted([p for p in root.rglob("*.json") if p.is_file()])


@st.cache_data(show_spinner=False)
def load_index(json_dir: str) -> pd.DataFrame:
    root = Path(json_dir).expanduser().resolve()
    rows = []
    for p in list_json_files(root):
        d = safe_load_json(p)
        if not isinstance(d, dict):
            continue
        d = ensure_user_fields(d)

        rows.append({
            "_path": str(p),
            "_sort_date": parse_date_for_sort(d),

            # 並び順は後でcolsで制御するので、ここは全項目を持つ
            "No.": None,  # 後で採番
            "日付": d.get("date") or "",
            "タイトル": title_of(d),

            "リンク": "",  # HTML生成時に作る（ここはダミー）

            "状態": d.get("user_status") or "New",
            "重要度": rating_to_stars(d.get("user_rating")),

            "要約": preview_text(d.get("summary")),
            "会社": join_list(d.get("company_names")),
            "核種": join_list(d.get("radionuclides")),
            "薬剤": join_list(d.get("drug_names")),
            "コメント": preview_text(d.get("user_comment")),
            "更新日時": d.get("user_updated_at") or "",

            "AI影響評価": preview_text(d.get("impact_opinion")),
            "英文": preview_text(d.get("english_news_article")),
            "和訳": preview_text(d.get("japanese_translation")),
            "他者コメント": preview_text(d.get("sender_opinion")),
        })

    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df

    df = df.sort_values(by=["_sort_date", "タイトル"], ascending=[False, True], kind="stable").reset_index(drop=True)
    df["No."] = range(1, len(df) + 1)
    return df


def render_html_table(df: pd.DataFrame, clamp_lines: int) -> None:
    st.markdown(f"""
<style>
.table-wrap {{
  overflow-x: auto;
  padding-bottom: 8px;
}}

.news-table {{
  border-collapse: separate;
  border-spacing: 0 10px;
  width: max-content;
  font-size: 0.80rem;
  line-height: 1.20;
}}

.news-table tbody tr {{
  background: rgba(255,255,255,0.03);
  outline: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
}}

.news-table td, .news-table th {{
  padding: 8px 10px;
  vertical-align: top;
  border: none;
}}

.news-table thead th {{
  position: sticky;
  top: 0;
  background: rgba(0,0,0,0.60);
  z-index: 5;
  outline: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
}}

.clamp {{
  display: -webkit-box;
  -webkit-line-clamp: {clamp_lines};
  -webkit-box-orient: vertical;
  overflow: hidden;
  white-space: normal;
}}

.title {{
  font-weight: 400;
  white-space: normal;
}}

a {{
  text-decoration: none;
}}
a:hover {{
  text-decoration: underline;
}}

.goto a {{
  display: inline-block;
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.18);
  background: rgba(100,200,255,0.10);
}}
.goto a:hover {{
  background: rgba(100,200,255,0.18);
}}

/* 列幅（メタ列は細く） */
.w-no     {{ min-width: 46px;  max-width: 60px;  }}
.w-date   {{ min-width: 80px;  max-width: 110px; }}
.w-title  {{ min-width: 260px; max-width: 520px; }}
.w-link   {{ min-width: 70px;  max-width: 90px;  }}
.w-state  {{ min-width: 70px;  max-width: 110px; }}
.w-rate   {{ min-width: 70px;  max-width: 110px; }}

.w-summary{{ min-width: 520px; max-width: 860px; }}
.w-company{{ min-width: 120px; max-width: 200px; }}
.w-nuclide{{ min-width: 90px;  max-width: 140px; }}
.w-drug   {{ min-width: 120px; max-width: 200px; }}
.w-comment{{ min-width: 360px; max-width: 620px; }}
.w-upd    {{ min-width: 140px; max-width: 220px; }}

.w-impact {{ min-width: 520px; max-width: 860px; }}
.w-en     {{ min-width: 520px; max-width: 860px; }}
.w-ja     {{ min-width: 520px; max-width: 860px; }}
.w-other  {{ min-width: 520px; max-width: 860px; }}
</style>
""", unsafe_allow_html=True)

    # ★ 指定の列順
    cols = [
        ("No.", "w-no"),
        ("日付", "w-date"),
        ("タイトル", "w-title"),
        ("リンク", "w-link"),
        ("状態", "w-state"),
        ("重要度", "w-rate"),
        ("要約", "w-summary"),
        ("会社", "w-company"),
        ("核種", "w-nuclide"),
        ("薬剤", "w-drug"),
        ("コメント", "w-comment"),
        ("更新日時", "w-upd"),
        ("AI影響評価", "w-impact"),
        ("英文", "w-en"),
        ("和訳", "w-ja"),
        ("他者コメント", "w-other"),
    ]

    thead = "<tr>" + "".join(
        f"<th class='{cls}'>{html.escape(name)}</th>" for name, cls in cols
    ) + "</tr>"

    def cell(text: Any, cls: str, clamp: bool = True, extra: str = "") -> str:
        s = "" if pd.isna(text) else str(text)
        s = html.escape(s)
        c = "clamp " if clamp else ""
        return f"<td class='{cls}'><div class='{c}{extra}'>{s}</div></td>"

    rows_html = []
    for _, r in df.iterrows():
        p = str(r["_path"])
        href = f"/pageview?id={html.escape(p)}"

        row = "<tr>"
        row += cell(r["No."], "w-no", clamp=False)
        row += cell(r["日付"], "w-date", clamp=False)
        row += cell(r["タイトル"], "w-title", clamp=True, extra="title")

        # リンク列（表示文字は「リンク」固定）
        row += f"<td class='w-link goto'><a href='{href}' target='_self'>リンク</a></td>"

        row += cell(r["状態"], "w-state", clamp=False)
        row += cell(r["重要度"], "w-rate", clamp=False)

        row += cell(r["要約"], "w-summary", clamp=True)
        row += cell(r["会社"], "w-company", clamp=True)
        row += cell(r["核種"], "w-nuclide", clamp=True)
        row += cell(r["薬剤"], "w-drug", clamp=True)

        row += cell(r["コメント"], "w-comment", clamp=True)
        row += cell(r["更新日時"], "w-upd", clamp=False)

        row += cell(r["AI影響評価"], "w-impact", clamp=True)
        row += cell(r["英文"], "w-en", clamp=True)
        row += cell(r["和訳"], "w-ja", clamp=True)
        row += cell(r["他者コメント"], "w-other", clamp=True)

        row += "</tr>"
        rows_html.append(row)

    table_html = f"""
<div class="table-wrap">
  <table class="news-table">
    <thead>{thead}</thead>
    <tbody>{''.join(rows_html)}</tbody>
  </table>
</div>
"""
    st.markdown(table_html, unsafe_allow_html=True)


# ========= UI =========
st.set_page_config(page_title="核医学の情報収集ログ", layout="wide")
st.title("核医学の情報収集ログ")

with st.sidebar:
    json_dir = st.text_input("JSONフォルダ（out/など）", value="json")
    if st.button("再読み込み", use_container_width=True):
        load_index.clear()

    st.divider()
    st.subheader("フィルタ")
    q = st.text_input("検索（タイトル/会社/核種/薬剤/要約/コメント/AI影響/英文/和訳/他者コメント）", value="")
    status_filter = st.multiselect("状態（user_status）", options=ALLOWED_STATUS, default=[])

    # 重要度は★表示でフィルタ
    rating_filter = st.multiselect("重要度（★）", options=[1, 2, 3, 4, 5], default=[])

    st.divider()
    st.subheader("表示")
    clamp_lines = st.slider("本文プレビュー行数（目次）", min_value=3, max_value=14, value=8, step=1)
    

df = load_index(json_dir)
if df is None or len(df) == 0:
    st.warning("JSONが見つかりません。フォルダ指定を確認してください。")
    st.stop()


def match_row(r: pd.Series) -> bool:
    if status_filter and r["状態"] not in status_filter:
        return False

    if rating_filter:
        # df側は ★文字列なので、その数で判定
        star_n = str(r.get("重要度", "")).count("★")
        if star_n not in rating_filter:
            return False

    if q.strip():
        qq = q.strip().lower()
        hay = " ".join([
            str(r.get("タイトル", "")),
            str(r.get("会社", "")),
            str(r.get("核種", "")),
            str(r.get("薬剤", "")),
            str(r.get("要約", "")),
            str(r.get("コメント", "")),
            str(r.get("状態", "")),
            str(r.get("重要度", "")),
            str(r.get("AI影響評価", "")),
            str(r.get("英文", "")),
            str(r.get("和訳", "")),
            str(r.get("他者コメント", "")),
        ]).lower()
        if qq not in hay:
            return False

    return True


df_view = df[df.apply(match_row, axis=1)].copy()
st.caption(f"表示: {len(df_view)} / 全体: {len(df)}")


# 全件表示（ページングなし）
if len(df_view) == 0:
    st.info("フィルタ結果が0件です。")
    st.stop()

render_html_table(df_view, clamp_lines=clamp_lines)


# --- ページングあり --- #
# total = len(df_view)
# if total == 0:
#     st.info("フィルタ結果が0件です。")
#     st.stop()

# max_page = (total - 1) // rows_per_page + 1
# page = st.number_input("ページ", min_value=1, max_value=max_page, value=1, step=1)
# start = (page - 1) * rows_per_page
# end = min(start + rows_per_page, total)
# df_page = df_view.iloc[start:end].copy()

# render_html_table(df_page, clamp_lines=clamp_lines)
