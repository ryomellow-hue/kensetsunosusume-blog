#!/usr/bin/env python3
"""
migrate.py — 新しいデザインHTMLに全設定を自動適用するスクリプト
使い方: python3 migrate.py 新しいデザイン.html
"""

import sys, re, json, datetime
from pathlib import Path

# ────────────────────────────────────────────
# 設定（変更が必要な場合はここを編集）
# ────────────────────────────────────────────
CONFIG = {
    "author_name": "SALUT",
    "author_title": "ゼネコン勤務のサラリーマン長期投資家",
    "author_bio": "建設業界に従事しながら資産形成、長期投資について自身がしてきた失敗例、成功例を基に情報発信をしています。将来に不安をなくすためのお金の知識を日々発信中。",
    "author_emoji": "👷",
    "formspree_id": "xdabnpkp",
    "utterances_repo": "ryomellow-hue/blog-comments",
    "blog_url": "https://kensetsunosusume.blog",
}

CATEGORIES_JS = """const CATEGORIES = [
  { id: "investment",    label: "新NISA・長期投資", color: "#1d6fa4" },
  { id: "household",     label: "家計管理",         color: "#2d8a5e" },
  { id: "construction",  label: "建設・キャリア",   color: "#7a5230" },
  { id: "failure",       label: "失敗談",           color: "#b04a3a" },
  { id: "ai",            label: "AI・ブログ活用",   color: "#6a3ea8" },
];"""

# ────────────────────────────────────────────
# posts.js から記事データを読み込む
# ────────────────────────────────────────────
def load_posts_js():
    posts_file = Path(__file__).parent / "posts.js"
    if not posts_file.exists():
        print("❌ posts.js が見つかりません")
        sys.exit(1)
    return posts_file.read_text(encoding="utf-8")

# ────────────────────────────────────────────
# バンドルHTMLを解析して各セクションを置換
# ────────────────────────────────────────────
def find_and_replace_data(content, posts_js_text):
    """CATEGORIES / POSTS / CAT_COUNTS / RECENT を置換"""
    # postsデータをposts.jsから抽出
    cat_match = re.search(r'const CATEGORIES = \[.*?\];', posts_js_text, re.DOTALL)
    posts_match = re.search(r'const POSTS = \[.*?\];', posts_js_text, re.DOTALL)
    counts_match = re.search(r'const CAT_COUNTS = \{.*?\};', posts_js_text)

    if not all([cat_match, posts_match, counts_match]):
        print("❌ posts.js のデータ形式が不正です")
        sys.exit(1)

    cats_js = cat_match.group()
    posts_data_js = posts_match.group()
    counts_js = counts_match.group()
    recent_js = 'const RECENT = POSTS.filter(p => p.status !== "draft").slice(0, 5);'

    new_data_block = f"{cats_js}\n\n{posts_data_js}\n{counts_js}\n{recent_js}\n\n"

    # バンドル内の既存データブロックを置換（エスケープ形式対応）
    is_escaped = '\\n' in content[18000000:18010000] if len(content) > 18000000 else False

    if is_escaped:
        new_data_escaped = new_data_block.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        # 既存CATEGORIESからRECENTまでを置換
        cat_start = content.find('const CATEGORIES')
        recent_end_idx = content.find(';', content.find('const RECENT')) + 1
        if cat_start > 0 and recent_end_idx > cat_start:
            content = content[:cat_start] + new_data_escaped + content[recent_end_idx:]
            print("✓ 記事データ置換（エスケープ形式）")
        else:
            print("⚠ 既存データブロックが見つかりません。手動確認が必要です")
    else:
        cat_start = content.find('const CATEGORIES')
        recent_end_idx = content.find(';', content.find('const RECENT')) + 1
        if cat_start > 0 and recent_end_idx > cat_start:
            content = content[:cat_start] + new_data_block + content[recent_end_idx:]
            print("✓ 記事データ置換")

    return content

def add_components(content):
    """ContactPage・UtterancesComments コンポーネントを追加"""
    anchor = 'ReactDOM.createRoot(document.getElementById(\\"root\\")'
    if anchor not in content:
        anchor = "ReactDOM.createRoot(document.getElementById('root')"

    contact_page = f"""
function ContactPage({{ setPage }}) {{
  const [status, setStatus] = React.useState("idle");
  const handleSubmit = async (e) => {{
    e.preventDefault();
    setStatus("sending");
    const data = new FormData(e.target);
    const res = await fetch("https://formspree.io/f/{CONFIG['formspree_id']}", {{
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
    s.setAttribute("repo", "{CONFIG['utterances_repo']}");
    s.setAttribute("issue-term", "title");
    s.setAttribute("theme", "github-light");
    s.setAttribute("crossorigin", "anonymous");
    s.async = true;
    ref.current.appendChild(s);
  }}, [postId]);
  return <div ref={{ref}} style={{{{ marginTop: 8 }}}} />;
}}

"""

    if anchor in content:
        escaped = contact_page.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        content = content.replace(anchor, escaped + anchor, 1)
        print("✓ ContactPage・UtterancesComments コンポーネント追加")
    else:
        print("⚠ ReactDOM.createRoot が見つかりません")

    return content

def main():
    if len(sys.argv) < 2:
        print("使い方: python3 migrate.py 新しいデザイン.html")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"❌ {input_file} が見つかりません")
        sys.exit(1)

    print(f"\n🚀 移行開始: {input_file.name}")
    print("=" * 50)

    content = input_file.read_text(encoding="utf-8")
    posts_js_text = load_posts_js()

    # 各処理を実行
    content = find_and_replace_data(content, posts_js_text)
    content = add_components(content)

    # 出力
    output_file = Path(__file__).parent / "index.html"
    output_file.write_text(content, encoding="utf-8")

    print("=" * 50)
    print(f"✅ 完了! → {output_file}")
    print("\n次のステップ:")
    print("1. index.html を Cloudflare Workers にアップロード")
    print("2. git add . && git commit -m '新デザイン適用' && git push")

if __name__ == "__main__":
    main()
