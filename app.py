import streamlit as st
import pandas as pd
import time

# 1. 頁面設定
st.set_page_config(page_title="全港小學導師報更管理系統", layout="wide")

# --- 側邊欄：管理選單 ---
st.sidebar.header("🏫 系統管理")

# 強制重新讀取按鈕（點擊可直接繞過快取、強制抓最新表單資料）
if st.sidebar.button("🔄 立即同步最新資料"):
    st.cache_data.clear()
    st.rerun()

# 選擇學校選單（首頁預設：惇裕小學）
school_options = [
    "惇裕小學", 
    "錦田蒙養公立學校",
    "校友會小學",
    "寶覺小學", 
    "培恩小學", 
    "錦田通德學校"
]
school = st.sidebar.selectbox("請選擇學校", school_options)

# 2. 學校資料庫 (已更新寶覺小學最新連結與 GID)
config = {
    "錦田蒙養公立學校": {
        "id": "1pvWXSAjVgEhFpi6Zw26JPpBbjeSDxFazahH9d1_Uuno", 
        "gid": "1963975849"
    },
    "校友會小學": {
        "id": "1wcuNVbpnM2Eqv9j6slcA3pLcVR3QflCc8ubQXaYZVVI", 
        "gid": "2126516204"
    },
    "惇裕小學": {
        "id": "1Uj5ZwFw4CrUhCW67AKR929zhmDDzlBzaqQYeGnrsZrE", 
        "gid": "755675256"
    },
    "寶覺小學": {
        "id": "1_oWRiHKAqtAhzMPoiDTrVazGokVnuvBx9MRlin8oIN0", 
        "gid": "0"
    },
    "培恩小學": {
        "id": "1SE1tx9AlWe_dPdH_e3t67ienI71QKgQCeaLIJml-Fn0", 
        "gid": "1808477045"
    },
    "錦田通德學校": {
        "id": "1cWKdTvKzWppxhUH2vsXafvEsQLUA2CYfcLwth0Sdntw", 
        "gid": "147121661"
    }
}

SHEET_ID = config[school]["id"]
GID = config[school]["gid"]

st.title(f"🏫 {school} - 報更即時看板")

# 若尚未填寫 ID，顯示提示訊息
if not SHEET_ID or not GID:
    st.info("ℹ️ 該學校暫未設定試算表網址連結，請提供 Google 試算表網址以完成設定。")
else:
    # 使用動態時間戳 t 參數，強迫 Google 每次都生成最新的 CSV 資料，實現自行更新
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}&t={int(time.time())}"

    @st.cache_data(ttl=5) # 5 秒快取過期，實現近乎實時的更新
    def load_data(url):
        return pd.read_csv(url)

    try:
        df = load_data(csv_url)
        
        # 智慧識別欄位 (自動適應各校表單欄位名稱長度)
        name_col = next((c for c in df.columns if '姓名' in c or 'name' in c.lower()), df.columns[1])
        phone_col = next((c for c in df.columns if '電話' in c or 'Phone' in c), df.columns[2])
        # 找出所有包含日期格式的欄位
        date_cols = [c for c in df.columns if any(x in c for x in ['/', '2026', '月', '('])]

        # 側邊欄：導師管理
        st.sidebar.markdown("---")
        tutors = df[name_col].dropna().unique()
        sel_tutor = st.sidebar.selectbox("🔍 搜尋導師", tutors)
        st.caption(f"數據最後同步時間：{time.strftime('%H:%M:%S')}")

        # 主畫面分頁
        tab1, tab2 = st.tabs(["🗓️ 每日概覽", "👤 導師個人統計"])

        with tab1:
            if date_cols:
                target = st.selectbox("選擇日期", date_cols)
                # 篩選當天有填寫內容（不為空值）的導師
                daily = df[df[target].notna()][[name_col, phone_col, target]]
                daily.columns = ['導師姓名', '電話', '報更內容']
                st.success(f"{target} 共有 {len(daily)} 位導師報更")
                st.dataframe(daily, use_container_width=True)
            else:
                st.warning("⚠️ 此表單中暫時找不到有效的日期欄位，請檢查試算表標題是否包含年份、月份或斜線。")

        with tab2:
            st.subheader(f"{sel_tutor} 的報更詳情")
            t_data = df[df[name_col] == sel_tutor]
            schedule = []
            for d in date_cols:
                if d in t_data.columns:
                    val = t_data[d].values[0]
                    if pd.notna(val):
                        schedule.append({"日期": d, "內容": val})
            
            if schedule:
                st.metric("本月總報更天數", len(schedule))
                st.table(pd.DataFrame(schedule))
            else:
                st.info("該導師本月尚未有報更紀錄。")

    except Exception as e:
        st.error("🚨 資料讀取失敗")
        st.info("原因可能：\n1. 該學校的試算表尚未開啟『知道連結的人即可檢視』權限。\n2. 若剛調整完權限，請點擊左側『🔄 立即同步最新資料』按鈕重試。")
