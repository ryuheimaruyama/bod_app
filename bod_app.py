import os
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

# ページ設定
st.set_page_config(
    page_title="BOD分析 AI学習型シミュレーター",
    page_icon="icon.png",
    layout="wide",
)

# --- 簡易ログイン認証機能 ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 ログイン認証")
    st.write("BOD分析AIシミュレーターを利用するにはログインしてください。")

    with st.form("login_form"):
        input_id = st.text_input("ユーザーID")
        input_pass = st.text_input("パスワード", type="password")
        submit_button = st.form_submit_button("ログイン")

        if submit_button:
            if input_id == "water" and input_pass == "mizu":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("IDまたはパスワードが間違っています。")
    st.stop()  # 認証されるまでここでストップ

# --- ログイン成功後のメインアプリ ---
st.title("🧪 BOD分析 AI学習型シミュレーター")

# ログアウトボタンをサイドバーに配置
if st.sidebar.button("🚪 ログアウト"):
    st.session_state["authenticated"] = False
    st.rerun()

DATA_DIR = "sample_data"
MODEL_DIR = "sample_models"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# --- サイドバー：顧客名・試料名の選択と管理 ---
st.sidebar.header("📂 1. 顧客・試料の選択")

saved_files = [
    f.replace("_data.csv", "")
    for f in os.listdir(DATA_DIR)
    if f.endswith("_data.csv")
]

if not saved_files:
    default_name = "標準排水_A工場"
    saved_files = [default_name]
else:
    default_name = saved_files[0]

mode = st.sidebar.radio(
    "操作モード", ["既存の試料を呼び出す", "新しい試料を追加する"]
)

if mode == "新しい試料を追加する":
    new_customer = st.sidebar.text_input("顧客名", value="A社")
    new_sample = st.sidebar.text_input("試料名", value="処理水")
    target_name = f"{new_customer}_{new_sample}"
else:
    target_name = st.sidebar.selectbox("保存済みの試料を選択", saved_files)

DATA_FILE = os.path.join(DATA_DIR, f"{target_name}_data.csv")
MODEL_FILE = os.path.join(MODEL_DIR, f"{target_name}_model.pkl")

# --- 保存した試料データ自体の削除機能 ---
if mode == "既存の試料を呼び出す" and len(saved_files) > 0:
    if st.sidebar.button(f"🗑️ 選択中の試料「{target_name}」を削除"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        if os.path.exists(MODEL_FILE):
            os.remove(MODEL_FILE)
        st.sidebar.success(f"「{target_name}」を削除しました。")
        st.rerun()

st.sidebar.markdown(f"**現在選択中:** `{target_name}`")

# --- 2. 選択した試料の過去データ管理 ---
st.sidebar.markdown("---")
st.sidebar.header("📊 2. 過去データの管理")
st.sidebar.write("この試料のCOD・BOD測定データを編集・保存・削除します。")

default_data = pd.DataFrame(
    {
        "COD (mg/L)": [10.0, 25.0, 40.0, 60.0, 85.0, 100.0],
        "BOD (mg/L)": [8.5, 20.0, 35.0, 52.0, 74.0, 88.0],
    }
)

if os.path.exists(DATA_FILE):
    try:
        initial_data = pd.read_csv(DATA_FILE)
    except Exception:
        initial_data = default_data
else:
    initial_data = default_data

edited_df = st.sidebar.data_editor(
    initial_data, num_rows="dynamic", key=f"editor_{target_name}"
)

if st.sidebar.button("💾 この試料のデータを保存"):
    edited_df.to_csv(DATA_FILE, index=False)
    st.sidebar.success(f"「{target_name}」のデータを保存しました！")

# --- 3. AIモデルの自動学習 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 相関モデルの自動学習")

model_type = st.sidebar.selectbox(
    "学習アルゴリズム",
    ["線形回帰 (Linear)", "多項式回帰 (Poly)"],
    key=f"algo_{target_name}",
)

cod_vals = edited_df["COD (mg/L)"].dropna().values
bod_vals = edited_df["BOD (mg/L)"].dropna().values

is_data_ready = len(cod_vals) >= 2

if is_data_ready:
    X = cod_vals.reshape(-1, 1)
    y = bod_vals

    if model_type == "多項式回帰 (Poly)":
        model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
    else:
        model = LinearRegression()

    model.fit(X, y)
    joblib.dump(model, MODEL_FILE)
else:
    model = None

# 定数設定（ふらん瓶容量 100.0 mL）
BOTTLE_VOL = 100.0
INITIAL_DO = 8.0  # 溶存酸素の初期値 (mg/L)
IDEAL_CONSUMPTION = INITIAL_DO * 0.55  # 55%消費 (4.4 mg/L)

ALLOWED_VOLUMES = [
    100.0,
    70.0,
    50.0,
    40.0,
    30.0,
    25.0,
    20.0,
    15.0,
    12.0,
    10.0,
    8.0,
    6.0,
    5.0,
    3.0,
    1.5,
]

# --- 4. メイン画面：本日の検体データ入力と予測 ---
st.header("1. 本日の検体データ入力")
st.write(f"対象試料: **{target_name}**")

cod_input = st.number_input(
    "現在の検体のCOD値 (mg/L)", min_value=0, value=18, step=1, format="%d"
)

force_new_mode = st.checkbox(
    "🆕 新規検体として扱う（過去データを無視してCOD基準で幅広く取る）",
    value=not is_data_ready,
)

if force_new_mode or model is None or not is_data_ready:
    est_bod_center = float(cod_input)
    estimation_note = "（※新規モードのため、COD値を基準に算出）"
else:
    pred_input = np.array([[float(cod_input)]])
    est_bod_center = float(model.predict(pred_input)[0])
    estimation_note = f"（「{target_name}」の相関モデルによる推算）"

if est_bod_center < 0:
    est_bod_center = 1.0

bod_min_range = float(cod_input) * 0.5
bod_max_range = float(cod_input) * 3.0

st.info(
    f"💡 **予想BOD中心**: 約 **{est_bod_center:.1f} mg/L** {estimation_note}\n\n"
    f"📊 **BOD見込み範囲（CODの半分〜3倍）**: **{bod_min_range:.1f} 〜 {bod_max_range:.1f} mg/L**"
)

# --- 5. 理想値を真ん中に配置した6水準の自動生成 ---
st.header("2. 推奨される仕込み量（分取量）水準")

# 1. 理想的な原液換算の分取量を計算
v_orig_ideal = (IDEAL_CONSUMPTION * BOTTLE_VOL) / est_bod_center

# 2. 希釈が必要かどうかの判定（原液換算で1.5mL未満になる場合は10倍希釈を導入）
if v_orig_ideal < 1.5:
    pre_dilution = 10
    sample_label = "×10希釈液"
    v_sol_ideal = v_orig_ideal * pre_dilution
else:
    pre_dilution = 1
    sample_label = "原液"
    v_sol_ideal = v_orig_ideal

allowed_arr = np.array(ALLOWED_VOLUMES)

# 理想値に最も近い標準分取量のインデックスを探す
ideal_idx_in_allowed = np.abs(allowed_arr - v_sol_ideal).argmin()

# 6水準を作るため、理想値の前後からバランスよく選出する（理想値が真ん中付近にくるようにする）
start_idx = max(0, ideal_idx_in_allowed - 3)
end_idx = start_idx + 6
if end_idx > len(ALLOWED_VOLUMES):
    end_idx = len(ALLOWED_VOLUMES)
    start_idx = max(0, end_idx - 6)

selected_volumes = ALLOWED_VOLUMES[start_idx:end_idx]
# 大きい順（濃い方から薄い方へ）に並べ替え
selected_volumes = sorted(selected_volumes, reverse=True)

if pre_dilution > 1:
    st.warning(
        f"⚠️ **高濃度検体**のため、あらかじめ **【 {sample_label} 】**"
        "（10倍希釈液）を作成し、その液を分取して測定してください。"
    )

# --- 6水準の中で、一番理想値に近いインデックスを特定 ---
ideal_idx = min(
    range(len(selected_volumes)),
    key=lambda i: abs((selected_volumes[i] / pre_dilution) - v_orig_ideal),
)

# --- 結果のテーブル表示 ---
table_data = []
for i, v in enumerate(selected_volumes):
    v_orig_equiv = v / pre_dilution
    total_dilution_factor = (BOTTLE_VOL / v_orig_equiv) * pre_dilution

    expected_consumption = est_bod_center * (v_orig_equiv / BOTTLE_VOL)
    est_cons_percent = (expected_consumption / INITIAL_DO) * 100

    bod_cover_min = INITIAL_DO * 0.4 / (v_orig_equiv / BOTTLE_VOL)
    bod_cover_max = INITIAL_DO * 0.7 / (v_orig_equiv / BOTTLE_VOL)

    if i == ideal_idx:
        eval_text = "⭐ 理想的（55%前後）"
        color_type = "blue"
    elif i in [ideal_idx - 1, ideal_idx + 1]:
        eval_text = "◎ 適切（準ずる水準）"
        color_type = "green"
    elif i in [ideal_idx - 2, ideal_idx + 2, ideal_idx + 3]:
        eval_text = "⚠️ カバー範囲（要確認）"
        color_type = "green" if force_new_mode else "yellow"
    else:
        if est_cons_percent < 20:
            eval_text = "△ 低すぎる（<20%）"
        else:
            eval_text = "× 高すぎる（>85%・DO切れ注意）"
        color_type = "red"

    if total_dilution_factor >= 10:
        dilution_str = f"×{total_dilution_factor:.0f}"
    else:
        dilution_str = f"×{total_dilution_factor:.1f}"

    table_data.append(
        {
            "仕込み液": sample_label,
            "分取量 (mL)": f"{v:.1f} mL" if not v.is_integer() else f"{v:.0f} mL",
            "（参考）原液換算": (
                f"{v_orig_equiv:.2f} mL"
                if pre_dilution > 1
                else (
                    f"{v:.1f} mL" if not v.is_integer() else f"{v:.0f} mL"
                )
            ),
            "総合希釈倍率": dilution_str,
            "予想ボトル内消費量 (mg/L)": f"{expected_consumption:.2f}",
            "予想DO消費率 (%)": f"{est_cons_percent:.0f}%",
            "判定": eval_text,
            "✨ この仕込みがカバーできるBOD範囲": f"{bod_cover_min:.1f} 〜 {bod_cover_max:.1f} mg/L",
            "_color_type": color_type,
        }
    )

df = pd.DataFrame(table_data)
display_df = df.drop(columns=["_color_type"])


def color_rows_and_cells(row):
    ctype = df.loc[row.name, "_color_type"]
    if ctype == "blue":
        return [
            "background-color: #cce5ff; color: #004085; font-weight: bold;"
        ] * len(row)
    elif ctype == "green":
        return [
            "background-color: #d4edda; color: #155724; font-weight: bold;"
        ] * len(row)
    elif ctype == "yellow":
        return ["background-color: #fff3cd; color: #856404;"] * len(row)
    else:
        return ["background-color: #f8d7da; color: #721c24;"] * len(row)


st.dataframe(
    display_df.style.apply(color_rows_and_cells, axis=1),
    use_container_width=True,
)

# --- 6. 画面の一番下：CODとBODの相関グラフ表示 ---
st.markdown("---")
st.header("📈 3. CODとBODの相関関係グラフ")
st.write(
    f"「**{target_name}**」の過去データ（プロット）と、現在の学習モデルによる回帰線を表示しています。"
)

if is_data_ready:
    chart_df = pd.DataFrame({"COD": cod_vals, "BOD": bod_vals})
    current_point_df = pd.DataFrame(
        {"COD": [float(cod_input)], "BOD": [est_bod_center]}
    )

    x_min, x_max = max(0, cod_vals.min() * 0.8), cod_vals.max() * 1.2
    x_range = np.linspace(x_min, max(x_max, float(cod_input) * 1.1), 100)

    if model is not None:
        y_pred_range = model.predict(x_range.reshape(-1, 1))
    else:
        y_pred_range = x_range

    line_df = pd.DataFrame({"COD": x_range, "予測BOD": y_pred_range})

    import altair as chart_lib

    points = (
        chart_lib.Chart(chart_df)
        .mark_circle(size=80, color="steelblue")
        .encode(
            x=chart_lib.X("COD:Q", title="COD (mg/L)"),
            y=chart_lib.Y("BOD:Q", title="BOD (mg/L)"),
            tooltip=["COD", "BOD"],
        )
    )

    lines = (
        chart_lib.Chart(line_df)
        .mark_line(color="orange", strokeWidth=2)
        .encode(x="COD:Q", y="予測BOD:Q")
    )

    current_point = (
        chart_lib.Chart(current_point_df)
        .mark_point(size=150, shape="star", color="red")
        .encode(
            x="COD:Q",
            y="BOD:Q",
            tooltip=[
                chart_lib.Tooltip("COD:Q", title="本日のCOD"),
                chart_lib.Tooltip("BOD:Q", title="予想/基準BOD"),
            ],
        )
    )

    st.altair_chart(
        (points + lines + current_point).interactive(), use_container_width=True
    )
    st.caption(
        "💡 青い点：過去の測定データ ／ オレンジの線：選択中のAI学習モデル ／ 赤い星：本日の入力値（予測点）"
    )
else:
    st.info(
        "⚠️ グラフを表示するには、少なくとも2件以上の過去データが必要です。"
    )