import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 1. 앱 페이지 설정
st.set_page_config(page_title="학교 분실물 센터 v3", page_icon="🔍", layout="centered")
st.title("마산제일고등학교 통합 분실물 센터")

# 2. SQLite 데이터베이스 초기화 및 자동 마이그레이션 함수
def init_db():
    conn = sqlite3.connect("lost_and_found.db")
    cursor = conn.cursor()
    # 기본 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT,
            item_name TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # ★ [구조 업그레이드 코드 추가] 기존 구버전 DB가 있을 경우 status 컬럼을 강제로 추가
    try:
        cursor.execute("ALTER TABLE lost_items ADD COLUMN status TEXT DEFAULT 'active'")
    except sqlite3.OperationalError:
        # 이미 status 컬럼이 존재하는 경우 발생하는 에러는 안전하게 무시합니다.
        pass
        
    conn.commit()
    conn.close()

# 앱 실행 시 자동으로 DB 초기화 및 구조 업데이트
init_db()

# 데이터베이스 조회 함수 (최근 3일 이내 완료된 것까지만 가져오거나 active인 것 가져오기)
def get_visible_items():
    conn = sqlite3.connect("lost_and_found.db")
    df = pd.read_sql_query("SELECT * FROM lost_items ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        return df
        
    # 현재 시간 기준으로 3일 전 계산
    three_days_ago = datetime.now() - timedelta(days=3)
    
    valid_indices = []
    for idx, row in df.iterrows():
        # 'status' 컬럼 안전장치 포함하여 필터링
        current_status = row.get('status', 'active')
        
        if current_status == 'active':
            valid_indices.append(idx)
        elif current_status == 'found':
            try:
                item_date = datetime.strptime(row['date_time'], "%Y-%m-%d %H:%M")
                if item_date >= three_days_ago:
                    valid_indices.append(idx)
            except:
                valid_indices.append(idx)
                
    return df.loc[valid_indices]

def insert_item(item_name, location, description):
    conn = sqlite3.connect("lost_and_found.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        INSERT INTO lost_items (date_time, item_name, location, description, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (now, item_name, location, description))
    conn.commit()
    conn.close()

# 진짜 삭제 대신 'found' 상태로 업데이트하는 함수 (논리 삭제)
def update_to_found(item_id):
    conn = sqlite3.connect("lost_and_found.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE lost_items SET status = 'found' WHERE id = ?", (item_id,))
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
                st.rerun()
            else:
                st.error("물품명과 습득 장소는 필수 입력 사항입니다.")

# [분실물 찾기 / 현황] 탭 구현
with tab1:
    st.subheader("📋 실시간 분실물 목록 조회")
    search_query = st.text_input("🔍 찾으시는 물품명을 입력하세요 (실시간 필터링)")
    
    df = get_visible_items()
    
    if not df.empty:
        if search_query:
            filtered_df = df[df['item_name'].str.contains(search_query, case=False)]
        else:
            filtered_df = df
            
        if not filtered_df.empty:
            for idx, row in filtered_df.iterrows():
                current_status = row.get('status', 'active')
                is_found = current_status == 'found'
                title_text = f"📦 {row['item_name']} - {row['location']} ({row['date_time']})"
                
                if is_found:
                    title_text = f"✅ ~~[회수완료] {row['item_name']} - {row['location']}~~"
                
                with st.expander(title_text):
                    if is_found:
                        st.warning("⚠️ 이미 주인이 찾아간 물품입니다. (장난으로 완료 처리된 경우 담당자에게 문의하세요.)")
                    st.write(f"**습득 일시:** {row['date_time']}")
                    st.write(f"**습득 장소:** {row['location']}")
                    st.write(f"**상세 특징:** {row['description'] if row['description'] else '특징 없음'}")
                    
                    if not is_found:
                        if st.button(f"✅ 주인 찾음 (줄표시 및 3일 뒤 자동삭제)", key=f"found_{row['id']}"):
                            update_to_found(row['id'])
                            st.success(f"'{row['item_name']}'의 상태가 '회수 완료'로 변경되었습니다.")
                            st.rerun()
        else:
            st.info("검색 조건에 일치하는 분실물이 없습니다.")
    else:
        st.info("현재 등록된 분실물이 없습니다.")
