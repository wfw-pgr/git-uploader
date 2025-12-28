#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import re
import argparse
import json
import datetime
from pathlib import Path
from typing import List, Optional

import extract_msg  # pip install extract-msg
from dateutil import parser as dtparser  # pip install python-dateutil
from pydantic import BaseModel, Field, ValidationError


# -----------------------------
# 1) 出力スキーマ（Pydantic）
# -----------------------------
class MailExtraction(BaseModel):
    # 「日付」: ニュースの発表日/出来事の日付を優先。無ければメール日付などから推定して YYYY-MM-DD、無理なら null。
    date: Optional[str] = Field(
        default=None,
        description="ニュースとしての主要日付（YYYY-MM-DD）。不明なら null。"
    )
    company_names: List[str] = Field(
        default_factory=list,
        description="会社名（複数可）。例: [\"Novartis\", \"PharmaLogic\"]"
    )
    radionuclides: List[str] = Field(
        default_factory=list,
        description="放射性核種（複数可）。例: [\"Ac-225\", \"Lu-177\"]"
    )
    drug_names: List[str] = Field(
        default_factory=list,
        description="薬剤/候補薬（複数可）。例: [\"[Ac-225]-RTX-2358\"]"
    )
    english_news_article: Optional[str] = Field(
        default=None,
        description="メール本文中の英文ニュース記事（あれば原文を抽出、無ければ null）。"
    )
    japanese_translation: Optional[str] = Field(
        default=None,
        description="english_news_article の日本語訳（english_news_article が無いなら null）。"
    )
    summary: str = Field(
        description="メール全体（日本語・英語含む）の要約（日本語）。"
    )
    impact_opinion: str = Field(
        description="このニュースの影響・示唆（日本語、推測は推測とわかるように）。"
    )
    sender_opinion: Optional[str] = Field(
        default=None,
        description="送信者が冒頭で述べる所感・コメント（個人名/メール等は書かず、内容のみ）。無ければ null。"
    )
    title_en: str = Field(
        description="英語タイトル。8単語以内。ハイフン連結は不要（Python側で行う）。"
    )
    # ★追加：日本語タイトル（ファイル名や title_en は変えず、タグとして保持）
    title_ja: str = Field(
        description="title_en に対応する、わかりやすい日本語タイトル。短く自然な見出し。"
    )


# -----------------------------
# 2) .msg 読み取り
# -----------------------------
def read_msg(path: Path) -> dict:
    """
    extract-msg で .msg から主要フィールドを抽出（process() は不要）。
    """
    msg = extract_msg.openMsg(str(path))

    try:
        subject = (msg.subject or "").strip()

        # plain body（無ければ ""）
        body = (msg.body or "").strip()

        # plain が空で HTML がある場合のフォールバック（HTMLをそのまま入れる）
        if (not body) and getattr(msg, "htmlBodyPrepared", None):
            try:
                body = msg.htmlBodyPrepared.decode("utf-8", errors="replace")
            except Exception:
                body = ""

        # msg.date は datetime か None（send date）
        raw_date = ""
        iso_date: Optional[str] = None
        if getattr(msg, "date", None):
            try:
                raw_date = str(msg.date)
                iso_date = msg.date.date().isoformat()
            except Exception:
                raw_date = str(msg.date)

        sender = (msg.sender or "").strip()

        # 長すぎる本文の安全弁
        MAX_CHARS = 80_000
        if len(body) > MAX_CHARS:
            body = body[:MAX_CHARS] + "\n\n[TRUNCATED]\n"

        return {
            "file_name": path.name,
            "subject": subject,
            "body": body,
            "email_date_iso": iso_date,
            "email_date_raw": raw_date,
            "sender_raw": sender,
        }

    finally:
        try:
            msg.close()
        except Exception:
            pass


# -----------------------------
# 3) LLM に投げるプロンプト
# -----------------------------
def build_prompt(mail: dict) -> str:
    """
    Structured Output 前提で、スキーマに沿う JSON を返すよう強く指示。
    個人情報（個人名・メールアドレス等）は sender_opinion に含めない。
    """
    instructions = f"""
あなたは放射性医薬品（Radiopharmaceuticals）のニュースを整理するアシスタントです。
以下の「メール」から情報を抽出し、指定スキーマに厳密に従う JSON だけを返してください（JSON以外は出力しない）。

重要ルール:
- "sender_opinion" には送信者が冒頭で述べる所感・コメントを要約して書く。
  ただし個人情報は書かない（個人名、メールアドレス、電話番号、部署内の固有名詞などは削除/一般化）。
  例: 「（同僚）」「（送信者）」のように匿名化する。
- "english_news_article" は、メール本文中に「ニュース記事としての英文」がまとまって存在する場合のみ、その英文部分を抽出する。
  断片的な英語だけなら null でもよい。
- "japanese_translation" は english_news_article の忠実な日本語訳。english_news_article が null なら null。
- "date" はニュースとしての主要日付（プレスリリース日、治験開始/結果発表日など）を優先して YYYY-MM-DD で記載。
  本文から判断できなければ、メール日付（参考: {mail.get("email_date_iso")}）を使ってもよい。無理なら null。
- 不明な項目は、配列は []、文字列は null（ただし必須の summary/impact_opinion/title_en/title_ja は空でなく書く）。
- 会社名/核種/薬剤名は本文に出てくる表記を尊重（例: Ac-225, [Ac-225]-RTX-2358 など）。
- "title_en" は英語で8単語以内の短いタイトル（単語区切りのままでOK）。固有名詞は会社名/薬剤名は可。
  例: "Ac-225 FAP radiopharmaceutical enters Phase 1/2"
- ★"title_ja" は title_en に対応する、わかりやすい日本語タイトル（短い見出し）。
  直訳よりも自然さを優先してよいが、意味は title_en と整合させる。

メール情報:
[SUBJECT]
{mail.get("subject")}

[EMAIL_DATE_RAW]
{mail.get("email_date_raw")}

[BODY]
{mail.get("body")}
""".strip()

    return instructions


# -----------------------------
# 4) JSON抽出の保険（まれにモデルが前後にゴミを付ける場合）
# -----------------------------
def _extract_json_fallback(text: str) -> str:
    """
    まずは text 全体を JSON として扱う。
    失敗したら、最初の { から最後の } を雑に抜き出す（最後の手段）。
    """
    t = (text or "").strip()
    if not t:
        return t

    # そのままJSONの可能性
    try:
        json.loads(t)
        return t
    except Exception:
        pass

    # ```json ... ``` の場合
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, flags=re.DOTALL | re.IGNORECASE)
    if m:
        cand = m.group(1).strip()
        try:
            json.loads(cand)
            return cand
        except Exception:
            pass

    # 最初の { から最後の } を抜き出し
    i = t.find("{")
    j = t.rfind("}")
    if i != -1 and j != -1 and i < j:
        cand = t[i : j + 1].strip()
        try:
            json.loads(cand)
            return cand
        except Exception:
            pass

    return t


# -----------------------------
# 5) Gemini 呼び出し（Structured Output）
# -----------------------------
def extract_with_gemini(
    prompt: str,
    model: str,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
) -> MailExtraction:
    """
    google-genai を使って JSON schema に沿う応答を生成し、Pydanticで検証。
    """
    try:
        from google import genai  # pip install google-genai
    except Exception as e:
        raise RuntimeError(
            "google-genai が import できません。Geminiモードを使う場合は `pip install google-genai` してください。"
        ) from e

    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        # 環境変数 GEMINI_API_KEY / GOOGLE_API_KEY から読む
        client = genai.Client()

    schema = MailExtraction.model_json_schema()

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "temperature": float(temperature),
            "response_mime_type": "application/json",
            "response_json_schema": schema,
        },
    )

    raw = resp.text or ""
    raw = _extract_json_fallback(raw)

    try:
        return MailExtraction.model_validate_json(raw)
    except ValidationError as e:
        raise RuntimeError(
            "Gemini response did not match schema. "
            f"Raw response text:\n{resp.text}\n\nValidation error:\n{e}"
        )


# -----------------------------
# 6) Ollama 呼び出し（ローカル / Ollama Cloudでも可）
# -----------------------------
def extract_with_ollama(
    prompt: str,
    model: str,
    host: Optional[str] = None,
    temperature: float = 0.0,
) -> MailExtraction:
    """
    Ollamaの structured outputs を使って JSON schema に沿う応答を生成し、Pydanticで検証。
    - ローカル: Ollamaアプリ起動 + `ollama pull <model>` 済みで利用
    - host を指定するとリモートOllamaにも接続可能（例: http://localhost:11434）
    """
    try:
        import ollama  # pip install ollama
        from ollama import Client
    except Exception as e:
        raise RuntimeError(
            "ollama Python が import できません。Ollamaモードを使う場合は `pip install ollama` してください。"
        ) from e

    schema = MailExtraction.model_json_schema()

    if host:
        client = Client(host=host)
        resp = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,  # ★ JSON Schemaを強制
            options={"temperature": float(temperature)},
            stream=False,
        )
        raw = resp.message.content
    else:
        resp = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,  # ★ JSON Schemaを強制
            options={"temperature": float(temperature)},
            stream=False,
        )
        raw = resp.message.content if hasattr(resp, "message") else resp["message"]["content"]

    raw = _extract_json_fallback(raw)

    try:
        return MailExtraction.model_validate_json(raw)
    except ValidationError as e:
        raise RuntimeError(
            "Ollama response did not match schema. "
            f"Raw response text:\n{raw}\n\nValidation error:\n{e}"
        )


# -----------------------------
# 7) 入出力（単体/ディレクトリ対応）
# -----------------------------
def iter_msg_files(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted([p for p in input_path.rglob("*.msg") if p.is_file()])


def ensure_out_path(out: Path, input_is_dir: bool) -> None:
    if input_is_dir:
        out.mkdir(parents=True, exist_ok=True)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)


def _yyyymmdd_from_dates(primary_iso: str | None, fallback_iso: str | None) -> str:
    """
    YYYYMMDD を作る。primary_iso 優先、無ければ fallback_iso、無ければ今日。
    """
    for iso in (primary_iso, fallback_iso):
        if iso:
            try:
                d = dtparser.parse(iso).date()
                return d.strftime("%Y%m%d")
            except Exception:
                pass
    return datetime.date.today().strftime("%Y%m%d")


def _slug_from_title_en(title_en: str) -> str:
    """
    英語タイトル（単語区切り）→ 8単語に制限 → '-' 連結 → ファイル名に安全な slug 化
    """
    words = re.findall(r"[A-Za-z0-9\[\]\(\)\+\.]+(?:-[A-Za-z0-9\[\]\(\)\+\.]+)?", title_en)
    words = words[:8] if words else []

    slug = "-".join(words).strip("-").lower()
    slug = re.sub(r"[^a-z0-9\-\[\]\(\)\+\.]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")

    return slug or "news-update"


def build_final_title(result_date_iso: str | None, email_date_iso: str | None, title_en: str) -> str:
    yyyymmdd = _yyyymmdd_from_dates(result_date_iso, email_date_iso)
    slug = _slug_from_title_en(title_en)
    return f"{yyyymmdd}-{slug}"


def unique_path(base: Path) -> Path:
    """
    既に存在する場合は -2, -3... を付けてユニークにする
    """
    if not base.exists():
        return base
    stem = base.stem
    suffix = base.suffix
    parent = base.parent
    i = 2
    while True:
        cand = parent / f"{stem}-{i}{suffix}"
        if not cand.exists():
            return cand
        i += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i", "--input", type=str, default="msg",
        help="入力 .msg ファイル、または .msg を含むディレクトリ"
    )
    ap.add_argument(
        "-o", "--output", type=str, default="json",
        help="出力先（省略時: ./json）。単体入力なら親ディレクトリとして扱い title.json を作成"
    )

    # ★追加：バックエンド切替
    ap.add_argument(
        "--backend", type=str, default="gemini", choices=["gemini", "ollama"],
        help="使用するLLMバックエンド（gemini: API / ollama: ローカルLLM）"
    )

    # Gemini用
    ap.add_argument(
        "--model", type=str, default="gemini-flash-latest",
        help="Gemini model name (default: gemini-flash-latest)"
    )
    ap.add_argument(
        "--api-key", type=str, default=None,
        help="Gemini APIキーを直接渡す（通常は環境変数 GEMINI_API_KEY 推奨）"
    )

    # Ollama用
    ap.add_argument(
        "--ollama-model", type=str, default="gemma3",
        help="Ollama model name (default: gemma3). 例: gemma3, llama3.2, qwen2.5, etc."
    )
    ap.add_argument(
        "--ollama-host", type=str, default=None,
        help="Ollama host (例: http://localhost:11434). 未指定なら環境変数 OLLAMA_HOST / デフォルトを使用"
    )

    # 共通
    ap.add_argument(
        "--temperature", type=float, default=0.0,
        help="生成温度（structured outputでは 0 推奨）"
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="LLMには投げず、抽出対象テキスト確認のみ行う"
    )
    args = ap.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve()

    msg_files = iter_msg_files(in_path)
    if not msg_files:
        raise SystemExit(f"No .msg files found: {in_path}")

    input_is_dir = in_path.is_dir()
    ensure_out_path(out_path, input_is_dir=input_is_dir)

    for msg_file in msg_files:
        mail = read_msg(msg_file)

        if args.dry_run:
            print(f"--- {msg_file} ---")
            print("SUBJECT:", mail["subject"])
            print("EMAIL_DATE_RAW:", mail["email_date_raw"])
            print("BODY(head):", mail["body"][:500])
            continue

        prompt = build_prompt(mail)

        # ★ここでバックエンド分岐
        if args.backend == "gemini":
            result = extract_with_gemini(
                prompt,
                model=args.model,
                api_key=args.api_key,
                temperature=args.temperature,
            )
        else:
            result = extract_with_ollama(
                prompt,
                model=args.ollama_model,
                host=args.ollama_host,
                temperature=args.temperature,
            )

        payload = result.model_dump()

        # title を最終生成（YYYYMMDD- + 英語8単語以内を'-'連結）
        final_title = build_final_title(
            result_date_iso=payload.get("date"),
            email_date_iso=mail.get("email_date_iso"),
            title_en=payload.get("title_en", ""),
        )
        payload["title"] = final_title  # ← JSON に含める（要件）

        # 出力先の解釈：
        # - 入力がディレクトリなら out_path はディレクトリ扱い
        # - 入力が単体でも、out_path がディレクトリならそこへ title.json
        # - out_path がファイルパスでも、要件に従い parent に title.json を作る
        if input_is_dir or out_path.is_dir() or str(out_path).endswith(os.sep):
            out_dir = out_path
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = out_path.parent
            out_dir.mkdir(parents=True, exist_ok=True)

        dst = out_dir / f"{final_title}.json"
        dst = unique_path(dst)

        dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote: {dst}")


if __name__ == "__main__":
    main()
