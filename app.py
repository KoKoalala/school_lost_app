import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 앱 페이지 설정
st.set_page_config(page_title="학교 분실물 센터 v2", page_icon="🔍", layout="centered")
st.title("🏫 우리 학교 통합 분실물 센터 (공동 DB형)")
st.write("데이터베이스 연동으로 새로고침해도 데이터가 영구히 유지됩니다.")

# 2. SQLite 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect("lost_and_found.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT,
            item_name TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

# 앱 실행 시 자동으로 DB 파일 생성 및 연결
init_db()

# 데이터베이스 연결 도우미 함수들
def get_all_items():
    conn = sqlite3.connect("lost_and_found.db")
    df = pd.read_sql_query("SELECT * FROM lost_items ORDER BY id DESC", conn)
    conn.close()
    return df

def insert_item(item_name, location, description):
    conn = sqlite3.connect("lost_and_found.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        INSERT INTO lost_items (date_time, item_name, location, description)
        VALUES (?, ?, ?, ?)
    """, (now, item_name, location, description))
    conn.commit()
    conn.close()

# 3. 탭 구성
tab1, tab2 = st.tabs(["🔍 분실물 찾기 / 현황", "✍️ 분실물 등록"])

# [분실물 등록] 탭 구현
with tab2:
    st.subheader("📝 새로운 분실물 등록")
    with st.form("register_form", clear_on_submit=True):
        item_name = st.text_input("물품명 (필수, 예: 에어팟, 체육복)")
        location = st.text_input("습득 장소 (필수, 예: 기숙사 면학실, 운동장)")
        description = st.text_area("상세 특징 (예: 케이스에 오버액션토끼 스티커 부착)")
        submitted = st.form_submit_button("DB에 등록하기")
        
        if submitted:
            if item_name.strip() and location.strip():
                insert_item(item_name, location, description)
                st.success(f"🎉 '{item_name}'이(가) 중앙 데이터베이스에 안전하게 기록되었습니다!")
                st.rerun()  # 화면 즉시 새로고침하여 반영
            else:
                st.error("물품명과 습득 장소는 필수 입력 사항입니다.")

# [분실물 찾기 / 현황] 탭 구현
with tab1:
    st.subheader("📋 실시간 분실물 목록 조회")
    search_query = st.text_input("🔍 찾으시는 물품명을 입력하세요 (실시간 필터링)")
    
    # 데이터베이스에서 실시간으로 불러오기
    df = get_all_items()
    
    if not df.empty:
        if search_query:
            filtered_df = df[df['item_name'].str.contains(search_query, case=False)]
        else:
            filtered_df = df
            
        if not filtered_df.empty:
            for idx, row in filtered_df.iterrows():
                with st.expander(f"📦 [{row['item_name']}] - {row['location']} ({row['date_time']})"):
                    st.write(f"**습득 일시:** {row['date_time']}")
                    st.write(f"**습득 장소:** {row['location']}")
                    st.write(f"**상세 특징:** {row['description'] if row['description'] else '특징 없음'}")
        else:
            st.info("검색 조건에 일치하는 분실물이 없습니다.")
    else:
        st.info("현재 등록된 분실물이 없습니다. 깨끗한 학교 환경! 👏")