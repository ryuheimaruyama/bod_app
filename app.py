import streamlit as st
import pymysql
import datetime

# データベース接続の設定（XAMPPの初期設定です）
def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='', # 初期設定はパスワードなし
        db='water_quality',
        charset='utf8mb4'
    )

st.title("水質分析 計算＆DB登録アプリ")

# 1. 測定値の入力フォーム
st.header("COD分析の入力")
analysis_date = st.date_input("分析日", datetime.date.today())

col1, col2 = st.columns(2)
with col1:
    sample_vol = st.number_input("検水量 (mL)", value=100.0)
    titration_sample = st.number_input("サンプルの滴定量 (mL)", value=5.00, step=0.01)

with col2:
    factor = st.number_input("ファクター (f)", value=1.000, step=0.001)
    titration_blank = st.number_input("ブランクの滴定量 (mL)", value=0.50, step=0.01)

# 2. 計算と保存
if st.button("計算してMySQLに保存"):
    # 計算処理（(サンプル - ブランク) * f * 1000 / 検水量）
    result = (titration_sample - titration_blank) * factor * 1000 / sample_vol
    st.success(f"計算結果: {result:.2f} mg/L")
    
    # データベースへ保存
    try:
        # DBに接続
        conn = get_connection()
        cursor = conn.cursor()
        
        # データを挿入するSQL文
        sql = """
        INSERT INTO cod_results 
        (analysis_date, sample_vol, titration_sample, titration_blank, factor, result_mg_l)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # SQLを実行
        cursor.execute(sql, (analysis_date, sample_vol, titration_sample, titration_blank, factor, result))
        conn.commit() # 変更を確定させる
        
        st.info("🎉 MySQLへのデータ保存が完了しました！")
        
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        
    finally:
        # 最後に必ず接続を閉じる
        if 'conn' in locals() and conn.open:
            cursor.close()
            conn.close()