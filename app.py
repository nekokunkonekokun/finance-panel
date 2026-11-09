import io
import japanize_matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import pandas as pd
import streamlit as st
import yfinance as yf

# ページ設定
st.set_page_config(page_title="日経平均アノマリーカード", layout="centered")
st.title("📈 日経平均 アノマリー分析")

# 1. スマホで操作しやすいUI（月・日の選択）
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("月", options=list(range(1, 13)), index=10)  # 初期値: 11月
with col2:
    day = st.selectbox("日", options=list(range(1, 32)), index=9)     # 初期値: 10日

# 2. データ取得処理（キャッシュ化して2回目以降を爆速にする）
@st.cache_data(ttl=3600)
def load_nikkei_data():
    df = yf.download("^N225", start="1994-01-01", progress=False)
    close = df["Close"].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df["Close"]
    data = pd.DataFrame({"Close": close.dropna()})
    data["Pct"] = data["Close"].pct_change() * 100
    return data

@st.cache_data(ttl=900)
def get_latest_price():
    return float(yf.Ticker("^N225").history(period="5d")["Close"].iloc[-1])

# 3. アノマリーカード描画関数
def generate_card(data, latest_price, month, day):
    target = data[(data.index.month == month) & (data.index.day == day) & (data.index.year >= 1995)].dropna()
    total = len(target)
    
    if total == 0:
        return None, f"{month}月{day}日の過去取引データが見つかりませんでした（休日の可能性があります）。"

    wins = len(target[target["Pct"] > 0])
    win_rate = wins / total * 100
    avg_vol = target["Pct"].abs().mean()
    min_row = target.loc[target["Pct"].idxmin()]
    max_drop, min_year = min_row["Pct"], min_row.name.year

    fig, ax = plt.subplots(figsize=(8.5, 5.2), facecolor="#090d16")
    ax.set_facecolor("#090d16")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def draw_card_patch(x, y, w, h, bg, border):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2.5",
                               fc=bg, ec=border, lw=1.8, zorder=1)
        ax.add_patch(patch)

    Y_COLOR = "#fbbf24"
    W_COLOR = "#ffffff"
    M_COLOR = "#94a3b8"

    # 1. ヘッダー
    ax.text(5, 92, f"日経平均 アノマリー【{month}月{day}日】", fontsize=18, fontweight="bold", color=Y_COLOR)
    ax.text(95, 92, f"過去30年 ({total}戦) 検証", fontsize=11, fontweight="bold", color=M_COLOR, ha="right", va="center")

    # 2. メインカード
    draw_card_patch(5, 53, 90, 32, "#131b2e", "#3b82f6")
    ax.text(50, 77, f"{month}/{day} の上昇確率（勝率）", fontsize=13, fontweight="bold", color=W_COLOR, ha="center", zorder=2)
    ax.text(50, 61, f"{win_rate:.1f}%", fontsize=38, fontweight="heavy", color=Y_COLOR, ha="center", zorder=2)
    ax.text(88, 62, f"{wins}勝 {total - wins}敗", fontsize=14, fontweight="bold", color=W_COLOR, ha="right", zorder=2)

    # 3. サブカード左
    draw_card_patch(5, 17, 43.5, 32, "#131b2e", "#38bdf8")
    ax.text(26.75, 41, "平均変動幅", fontsize=13, fontweight="bold", color=W_COLOR, ha="center", zorder=2)
    ax.text(26.75, 30, f"±{avg_vol:.2f}%", fontsize=28, fontweight="heavy", color=Y_COLOR, ha="center", zorder=2)
    ax.text(26.75, 22, f"(±{latest_price * avg_vol / 100:,.0f}円 相当)", fontsize=11, fontweight="bold", color=M_COLOR, ha="center", zorder=2)

    # 4. サブカード右
    draw_card_patch(51.5, 17, 43.5, 32, "#20111a", "#ef4444")
    ax.text(73.25, 41, "過去最大下落率", fontsize=13, fontweight="bold", color=W_COLOR, ha="center", zorder=2)
    ax.text(73.25, 30, f"{max_drop:.2f}%", fontsize=28, fontweight="heavy", color=Y_COLOR, ha="center", zorder=2)
    ax.text(73.25, 22, f"({min_year}年 / {latest_price * max_drop / 100:,.0f}円)", fontsize=11, fontweight="bold", color=M_COLOR, ha="center", zorder=2)

    # 5. フッター
    draw_card_patch(5, 4, 90, 8, "#1a162b", "#6366f1")
    ax.text(50, 8, f"[注意] 1日平均 ±{avg_vol:.2f}%（約{latest_price * avg_vol / 100:,.0f}円）上下に動く傾向があります。",
            fontsize=10.5, fontweight="bold", color="#e0e7ff", ha="center", va="center", zorder=2)

    plt.tight_layout()
    return fig, None

# 4. 実行＆表示
with st.spinner("データを取得・計算中..."):
    data = load_nikkei_data()
    latest_price = get_latest_price()

fig, err = generate_card(data, latest_price, month, day)

if err:
    st.warning(err)
else:
    # 画面表示
    st.pyplot(fig)
    
    # 画像ダウンロードボタン
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, facecolor=fig.get_facecolor(), bbox_inches="tight")
    st.download_button(
        label="📥 アノマリーカード画像を保存",
        data=buf.getvalue(),
        file_name=f"nikkei_card_{month:02d}_{day:02d}.png",
        mime="image/png",
        use_container_width=True
    )
