#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

# ステータス（指定の3種）
ALLOWED_STATUS = ["New", "既読", "要再確認"]

DEFAULTS = {
    "user_comment": "",
    "user_rating": None,      # 1-5 or None（JSON保存はint）
    "user_status": "New",
    "user_updated_at": None,
}


def now_iso_jst() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")


def safe_load_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def ensure_user_fields(d: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in DEFAULTS.items():
        if k not in d:
            d[k] = v

    if d.get("user_status") not in ALLOWED_STATUS:
        d["user_status"] = "New"

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


def title_of(d: Dict[str, Any]) -> str:
    return str(d.get("title") or d.get("subject") or d.get("file_name") or "untitled")


def rating_to_stars(r: Optional[int]) -> str:
    """表示専用：★のみ（空き☆は出さない）"""
    if r is None:
        return "—"
    try:
        r = int(r)
    except Exception:
        return "—"
    r = max(0, min(5, r))
    return "★" * r if r > 0 else "—"


def stars_to_int(s: str) -> Optional[int]:
    """UI選択（★表記）→ intへ"""
    if s == "(なし)":
        return None
    return s.count("★")


def get_app_root() -> Path:
    """
    app.py と同階層を “home” とみなす。
    pages/01_pageview.py を想定して、親の親がルート。
    """
    here = Path(__file__).resolve()
    return here.parents[1]


def backup_file(src: Path) -> Path:
    backup_dir = get_app_root() / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = backup_dir / f"{src.stem}__{ts}{src.suffix}"
    shutil.copy2(src, dst)
    return dst


def save_record(path: Path, d: Dict[str, Any]) -> None:
    backup_file(path)
    d["user_updated_at"] = now_iso_jst()
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_id_param() -> Optional[str]:
    if hasattr(st, "query_params"):
        v = st.query_params.get("id")
        return v if isinstance(v, str) else (v[0] if v else None)
    qp = st.experimental_get_query_params()
    return qp.get("id", [None])[0]


# ========= UI =========
st.set_page_config(page_title="核医学の情報収集ログ - 記事", layout="wide")
st.title("核医学の情報収集ログ")

st.page_link("app.py", label="← 目次に戻る")

id_path = get_id_param()
if not id_path:
    st.warning("記事ID（id）がありません。目次から開いてください。")
    st.stop()

path = Path(id_path)
rec = safe_load_json(path)
if not isinstance(rec, dict):
    st.error(f"JSONを読めません: {id_path}")
    st.stop()

rec = ensure_user_fields(rec)

st.markdown(f"## {title_of(rec)}")
st.write(f"**日付:** {rec.get('date') or '-'}")
st.write(f"**会社:** {join_list(rec.get('company_names')) or '-'}")
st.write(f"**核種:** {join_list(rec.get('radionuclides')) or '-'}")
st.write(f"**薬剤:** {join_list(rec.get('drug_names')) or '-'}")
st.write(f"**状態:** {rec.get('user_status') or 'New'}")
st.write(f"**重要度:** {rating_to_stars(rec.get('user_rating'))}")
st.caption(f"JSON: {id_path}")

with st.expander("要約", expanded=True):
    st.write(rec.get("summary") or "")
with st.expander("AI影響コメント", expanded=True):
    st.write(rec.get("impact_opinion") or "")
if rec.get("sender_opinion"):
    with st.expander("他者コメント", expanded=False):
        st.write(rec.get("sender_opinion") or "")
with st.expander("英文", expanded=False):
    st.write(rec.get("english_news_article") or "")
with st.expander("和訳", expanded=False):
    st.write(rec.get("japanese_translation") or "")

st.subheader("評価メモ")
with st.form("edit_form", clear_on_submit=False):
    c1, c2, c3 = st.columns([0.34, 0.22, 0.44])

    with c1:
        user_status = st.selectbox(
            "状態",
            options=ALLOWED_STATUS,
            index=ALLOWED_STATUS.index(rec.get("user_status") or "New"),
        )

    with c2:
        # UIは★のみ。保存はint。
        rating_options = ["(なし)"] + ["★" * i for i in range(1, 6)]
        cur = rec.get("user_rating")
        idx = 0 if cur is None else max(1, min(5, int(cur)))
        rating_sel = st.selectbox("重要度", options=rating_options, index=idx)

    with c3:
        st.text_input("更新日時", value=rec.get("user_updated_at") or "-", disabled=True)

    user_comment = st.text_area("コメント", value=rec.get("user_comment") or "", height=180)

    submitted = st.form_submit_button("保存(.jsonに追記)")

if submitted:
    rec["user_status"] = user_status
    rec["user_rating"] = stars_to_int(rating_sel)  # int/Noneで保存
    rec["user_comment"] = user_comment or ""

    save_record(path, rec)
    st.cache_data.clear()  # ★ 目次の load_index キャッシュを無効化
    st.success("Saved.")
