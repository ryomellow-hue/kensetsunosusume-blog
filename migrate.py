#!/usr/bin/env python3
"""
migrate.py — 新しいデザインHTMLに全設定を自動適用するスクリプト

【対応フォーマット】
  フォーマット1 (旧): エスケープ済みJSバンドル（バックスラッシュ+引用符+改行エスケープ）
  フォーマット2 (新): UUIDキー + gzip + base64 JSONブロブ（claude.ai/design の最新出力）

使い方:
  python3 migrate.py 新しいデザイン.html
"""

import sys, re, json, gzip, base64, datetime
from pathlib import Path

# ────────────────────────────────────────────
# 設定（変更が必要な場合はここを編集）
# ────────────────────────────────────────────
CONFIG = {
    "blog_name":     "ゼネコン投資家のリアル",
    "author_name":   "SALUT",
    "author_title":  "準大手ゼネコン施工管理10年・32歳・長期投資家",
    "author_bio":    "準大手ゼネコンで施工管理を10年続けながら長期投資を実践。不動産失敗で約1,000万円の損失を経験後、新NISAでゼロから再建。現在NISA評価額約1,100万円（+44.7%）・総資産約1,950万円。失敗も数字もリアルに発信中。",
    "author_emoji":  "👷",
    "formspree_id":  "xdabnpkp",
    "utterances_repo": "ryomellow-hue/blog-comments",
    "blog_url":      "https://kensetsunosusume.blog",
}

# ────────────────────────────────────────────
# posts.js から記事データを読み込む
# ────────────────────────────────────────────
def load_posts_js():
    posts_file = Path(__file__).parent / "posts.js"
    if not posts_file.exists():
        print("❌ posts.js が見つかりません")
        sys.exit(1)
    return posts_file.read_text(encoding="utf-8")

def extract_posts_block(posts_js_text):
    """posts.js から CATEGORIES/POSTS/CAT_COUNTS を抽出して結合ブロックを返す"""
    cat_match   = re.search(r'const CATEGORIES = \[.*?\];', posts_js_text, re.DOTALL)
    posts_match = re.search(r'const POSTS = \[.*?\];',      posts_js_text, re.DOTALL)
    counts_match = re.search(r'const CAT_COUNTS = \{.*?\};', posts_js_text, re.DOTALL)

    if not all([cat_match, posts_match, counts_match]):
        print("❌ posts.js のデータ形式が不正です（CATEGORIES/POSTS/CAT_COUNTS が見つからない）")
        sys.exit(1)

    recent_js = 'const RECENT = POSTS.filter(p => p.status !== "draft").slice(0, 5);'
    return (
        cat_match.group() + "\n\n"
        + posts_match.group() + "\n"
        + counts_match.group() + "\n"
        + recent_js + "\n\n"
    )

# ────────────────────────────────────────────
# ContactPage / UtterancesComments コンポーネント
# ────────────────────────────────────────────
def build_components():
    fid  = CONFIG["formspree_id"]
    repo = CONFIG["utterances_repo"]
    return f"""
function ContactPage({{ setPage }}) {{
  const [status, setStatus] = React.useState("idle");
  const handleSubmit = async (e) => {{
    e.preventDefault();
    setStatus("sending");
    const data = new FormData(e.target);
    const res = await fetch("https://formspree.io/f/{fid}", {{
      method: "POST", body: data, headers: {{ Accept: "application/json" }},
    }});
    if (res.ok) {{ setStatus("done"); e.target.reset(); }}
    else {{ setStatus("error"); }}
  }};
  return (
    <div style={{{{ maxWidth: 680, margin: "0 auto", padding: "48px 24px" }}}}>
      <button onClick={{() => setPage("home")}} style={{{{ background: "none", border: "none", cursor: "pointer", fontSize: 13, marginBottom: 24, padding: 0 }}}}>← トップへ戻る</button>
      <h1 style={{{{ fontSize: 26, fontWeight: 700, marginBottom: 8 }}}}>お問い合わせ</h1>
      <p style={{{{ fontSize: 14, marginBottom: 32 }}}}>ご質問・ご意見はこちらからお気軽にどうぞ。</p>
      {{status === "done" ? (
        <div style={{{{ padding: 32, textAlign: "center" }}}}>✅ 送信が完了しました。ありがとうございます。</div>
      ) : (
        <form onSubmit={{handleSubmit}} style={{{{ display: "flex", flexDirection: "column", gap: 20 }}}}>
          <div><label style={{{{ display: "block", fontSize: 13, fontWeight: 700, marginBottom: 6 }}}}>お名前 *</label>
          <input name="name" required style={{{{ width: "100%", padding: "10px 14px", border: "1px solid #ddd", borderRadius: 6, fontSize: 14, boxSizing: "border-box" }}}} /></div>
          <div><label style={{{{ display: "block", fontSize: 13, fontWeight: 700, marginBottom: 6 }}}}>メールアドレス *</label>
          <input name="email" type="email" required style={{{{ width: "100%", padding: "10px 14px", border: "1px solid #ddd", borderRadius: 6, fontSize: 14, boxSizing: "border-box" }}}} /></div>
          <div><label style={{{{ display: "block", fontSize: 13, fontWeight: 700, marginBottom: 6 }}}}>件名</label>
          <input name="subject" style={{{{ width: "100%", padding: "10px 14px", border: "1px solid #ddd", borderRadius: 6, fontSize: 14, boxSizing: "border-box" }}}} /></div>
          <div><label style={{{{ display: "block", fontSize: 13, fontWeight: 700, marginBottom: 6 }}}}>メッセージ *</label>
          <textarea name="message" required rows={{6}} style={{{{ width: "100%", padding: "10px 14px", border: "1px solid #ddd", borderRadius: 6, fontSize: 14, boxSizing: "border-box", resize: "vertical" }}}} /></div>
          {{status === "error" && <div style={{{{ color: "#b04a3a", fontSize: 13 }}}}>送信に失敗しました。再度お試しください。</div>}}
          <button type="submit" disabled={{status === "sending"}} style={{{{ padding: "12px 32px", background: "#1a2942", color: "#fff", border: "none", borderRadius: 6, fontSize: 14, fontWeight: 700, cursor: "pointer", alignSelf: "flex-start" }}}}>
            {{status === "sending" ? "送信中..." : "送信する"}}
          </button>
        </form>
      )}}
    </div>
  );
}}

function UtterancesComments({{ postId }}) {{
  const ref = React.useRef(null);
  React.useEffect(() => {{
    if (!ref.current) return;
    ref.current.innerHTML = "";
    const s = document.createElement("script");
    s.src = "https://utteranc.es/client.js";
    s.setAttribute("repo", "{repo}");
    s.setAttribute("issue-term", "title");
    s.setAttribute("theme", "github-light");
    s.setAttribute("crossorigin", "anonymous");
    s.async = true;
    ref.current.appendChild(s);
  }}, [postId]);
  return <div ref={{ref}} style={{{{ marginTop: 8 }}}} />;
}}

"""

# ════════════════════════════════════════════
# フォーマット判別
# ════════════════════════════════════════════
def detect_format(html: str) -> str:
    """
    'uuid_bundle' : <script type="application/json"> または <script type="__bundler/manifest"> ブロブ形式
    'escaped'     : 旧エスケープ JS 文字列形式
    """
    if re.search(r'<script[^>]+type=["\']application/json["\']', html):
        return "uuid_bundle"
    if re.search(r'<script[^>]+type=["\']__bundler/manifest["\']', html):
        return "uuid_bundle"
    return "escaped"

# ════════════════════════════════════════════
# フォーマット2 (新): UUID+gzip+base64 対応
# ════════════════════════════════════════════
def decode_file(b64_gz: str) -> str:
    raw = base64.b64decode(b64_gz)
    return gzip.decompress(raw).decode("utf-8")

def encode_file(text: str) -> str:
    compressed = gzip.compress(text.encode("utf-8"), compresslevel=9)
    return base64.b64encode(compressed).decode("ascii")

def migrate_uuid_bundle(html: str, new_data_block: str, components: str) -> str:
    """UUID+gzip+base64 ブロブ形式の移行処理"""

    # JSON ブロブを抽出（application/json または __bundler/manifest 形式に対応）
    blob_match = re.search(
        r'(<script[^>]+type=["\'](?:application/json|__bundler/manifest)["\'][^>]*>)(.*?)(</script>)',
        html, re.DOTALL
    )
    if not blob_match:
        print("❌ JSONブロブ（<script type='application/json'> または <script type='__bundler/manifest'>）が見つかりません")
        sys.exit(1)

    tag_open  = blob_match.group(1)
    blob_json = blob_match.group(2)
    tag_close = blob_match.group(3)

    bundle = json.loads(blob_json)
    print(f"  ブロブ内ファイル数: {len(bundle)}")

    data_uuid = None  # CATEGORIES/POSTS を含むファイル
    app_uuid  = None  # ReactDOM / コンポーネントを含むファイル

    # UUID を走査して対象ファイルを特定
    # エントリは {"mime": ..., "compressed": true, "data": "..."} 形式の場合がある
    def get_entry_data(entry):
        """エントリから base64 データを取り出す（dict形式・文字列形式の両方に対応）"""
        if isinstance(entry, dict):
            return entry.get("data", "")
        return entry  # 旧形式：文字列直接

    def set_entry_data(bundle, uuid, encoded):
        """エントリの data フィールドのみを更新（dict構造を破壊しない）"""
        if isinstance(bundle[uuid], dict):
            bundle[uuid]["data"] = encoded
        else:
            bundle[uuid] = encoded  # 旧形式：文字列直接

    for uuid, entry in bundle.items():
        try:
            b64_gz = get_entry_data(entry)
            text = decode_file(b64_gz)
        except Exception:
            continue
        if "const CATEGORIES" in text and data_uuid is None:
            data_uuid = uuid
            print(f"  DATA ファイル特定: {uuid}")
        if ("ReactDOM" in text or "createRoot" in text) and app_uuid is None:
            app_uuid = uuid
            print(f"  APP ファイル特定:  {uuid}")
        if data_uuid and app_uuid:
            break

    if not data_uuid:
        print("❌ CATEGORIES を含むデータファイルが見つかりません")
        sys.exit(1)
    if not app_uuid:
        print("❌ ReactDOM を含むアプリファイルが見つかりません")
        sys.exit(1)

    # ── DATA ファイル置換 ──
    data_text = decode_file(get_entry_data(bundle[data_uuid]))
    cat_start = data_text.find("const CATEGORIES")
    recent_end = data_text.find(";", data_text.rfind("const RECENT")) + 1
    if cat_start < 0 or recent_end <= cat_start:
        print("⚠ DATAファイル内でCATEGORIES〜RECENTブロックが見つかりません。先頭に追記します")
        data_text = new_data_block + data_text
    else:
        data_text = data_text[:cat_start] + new_data_block + data_text[recent_end:]
    set_entry_data(bundle, data_uuid, encode_file(data_text))
    print("✓ 記事データ置換完了（UUID束形式）")

    # ── APP ファイル置換 ──
    app_text = decode_file(get_entry_data(bundle[app_uuid]))

    # ContactPage / UtterancesComments が未定義なら追加
    if "function ContactPage" not in app_text:
        anchor_patterns = [
            "ReactDOM.createRoot(document.getElementById('root')",
            'ReactDOM.createRoot(document.getElementById("root")',
        ]
        inserted = False
        for anchor in anchor_patterns:
            if anchor in app_text:
                app_text = app_text.replace(anchor, components + anchor, 1)
                inserted = True
                break
        if inserted:
            print("✓ ContactPage・UtterancesComments コンポーネント追加")
        else:
            print("⚠ ReactDOM.createRoot が見つかりません。コンポーネント追加をスキップ")
    else:
        print("ℹ ContactPage は既に存在します（スキップ）")

    set_entry_data(bundle, app_uuid, encode_file(app_text))

    # ブロブを再組み立て
    new_blob = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    html = html[:blob_match.start()] + tag_open + new_blob + tag_close + html[blob_match.end():]
    return html

# ════════════════════════════════════════════
# フォーマット1 (旧): エスケープ JS 文字列対応
# ════════════════════════════════════════════
def migrate_escaped(html: str, new_data_block: str, components: str) -> str:
    """旧エスケープ形式の移行処理"""

    # ── 記事データ置換 ──
    new_data_escaped = (
        new_data_block
        .replace('\\', '\\\\')
        .replace('"', '\\"')
        .replace('\n', '\\n')
    )
    cat_start   = html.find('const CATEGORIES')
    recent_pos  = html.rfind('const RECENT')
    recent_end  = html.find(';', recent_pos) + 1

    if cat_start > 0 and recent_end > cat_start:
        html = html[:cat_start] + new_data_escaped + html[recent_end:]
        print("✓ 記事データ置換完了（エスケープ形式）")
    else:
        print("⚠ CATEGORIES〜RECENT ブロックが見つかりません")

    # ── コンポーネント追加 ──
    anchor = 'ReactDOM.createRoot(document.getElementById(\\"root\\")'
    if anchor not in html:
        anchor = "ReactDOM.createRoot(document.getElementById('root')"

    if anchor in html:
        escaped_components = (
            components
            .replace('\\', '\\\\')
            .replace('"', '\\"')
            .replace('\n', '\\n')
        )
        html = html.replace(anchor, escaped_components + anchor, 1)
        print("✓ ContactPage・UtterancesComments コンポーネント追加（エスケープ形式）")
    else:
        print("⚠ ReactDOM.createRoot が見つかりません")

    return html

# ════════════════════════════════════════════
# メイン
# ════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("使い方: python3 migrate.py 新しいデザイン.html")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"❌ {input_file} が見つかりません")
        sys.exit(1)

    print(f"\n🚀 移行開始: {input_file.name}")
    print("=" * 55)

    html = input_file.read_text(encoding="utf-8")
    posts_js_text = load_posts_js()

    new_data_block = extract_posts_block(posts_js_text)
    components     = build_components()

    fmt = detect_format(html)
    print(f"  フォーマット検出: {fmt}")

    if fmt == "uuid_bundle":
        html = migrate_uuid_bundle(html, new_data_block, components)
    else:
        html = migrate_escaped(html, new_data_block, components)

    output_file = Path(__file__).parent / "index.html"
    output_file.write_text(html, encoding="utf-8")
    size_mb = output_file.stat().st_size / 1024 / 1024

    print("=" * 55)
    print(f"✅ 完了! → {output_file}  ({size_mb:.1f} MB)")
    print(f"   生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("次のステップ:")
    print("  1. index.html を Cloudflare Workers ダッシュボードにアップロード")
    print("  2. git add . && git commit -m '新デザイン適用' && git push")

if __name__ == "__main__":
    main()
