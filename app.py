import streamlit as st
import requests
import json
import time

# ==========================================
# 🔐 1. Verkada 단기 API Token 발급 함수
# ==========================================
def get_verkada_token(api_key):
    """최상위 API Key를 사용해 30분짜리 단기 토큰을 발급받습니다."""
    url = "https://api.verkada.com/token"
    # 토큰 발급 시에는 'x-api-key' 헤더를 사용합니다.
    headers = {
        "x-api-key": api_key, 
        "accept": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("token")
        else:
            st.error(f"❌ 토큰 발급 실패 (상태 코드: {response.status_code})")
            st.json(response.json())
            return None
    except Exception as e:
        st.error(f"❌ 토큰 요청 중 오류 발생: {e}")
        return None

# ==========================================
# 🖥️ 2. Streamlit 앱 UI 및 메인 로직
# ==========================================

# 앱 기본 설정
st.set_page_config(page_title="Verkada Helix POS Simulator", layout="centered")

st.title("🛒 Verkada Helix POS 시뮬레이터")
st.markdown("Verkada Command API와 Helix 연동을 테스트하기 위한 실습용 웹 앱입니다.")

st.divider()

# --- Section 1: 시스템 설정 ---
st.subheader("1. 연동 정보 설정")
st.markdown("Verkada 시스템과 통신하기 위한 4가지 필수 값을 입력하세요.")

col_sys1, col_sys2 = st.columns(2)
with col_sys1:
    api_key = st.text_input("Verkada API Key", type="password", help="Command에서 발급받은 최상위 API Key (x-api-key)")
    org_id = st.text_input("Org ID", placeholder="예: 61b8824a-...")
    
with col_sys2:
    camera_id = st.text_input("Camera ID", placeholder="예: 1234abcd-...")
    event_type_uid = st.text_input("Helix Event Type UID", placeholder="예: d60f92a4-...")

st.divider()

# --- Section 2: POS 데이터 입력 ---
st.subheader("2. POS 데이터 입력")

col_data1, col_data2 = st.columns(2)

with col_data1:
    transaction_type = st.selectbox("Transaction Type", ["Sale", "Refund", "Void"])
    item = st.text_input("Item", value="Americano")
    number_of_items = st.number_input("Number of Items", min_value=1, value=1, step=1)
    price = st.number_input("Price (정수)", min_value=0, value=5000, step=100)

with col_data2:
    payment_type = st.selectbox("Payment Type", ["Credit Card", "Cash", "Mobile Pay"])
    # 🔥 수정된 부분: Discount 필드를 Yes/No 선택 방식으로 변경
    discount = st.selectbox("Discount (적용 여부)", ["No", "Yes"])
    discount_percentage = st.number_input("Discount Percentage (정수)", min_value=0, max_value=100, value=0, step=1)

st.divider()

# --- Section 3: 데이터 전송 ---
st.subheader("3. Helix로 데이터 전송")

# 현재 시간을 밀리초(ms) 단위로 변환
current_time_ms = int(time.time() * 1000)

# Org ID를 활용하여 동적으로 엔드포인트 URL 생성
api_url = f"https://api.verkada.com/cameras/v1/video_tagging/event?org_id={org_id}"

# 페이로드 생성 (Discount 필드는 선택한 "Yes" 또는 "No" 문자열로 전송됨)
payload = {
    "attributes": {
        "Discount": str(discount),                   # "Yes" 또는 "No"
        "Discount Percentage": int(discount_percentage),
        "Item": str(item),
        "Number of Items": int(number_of_items),
        "Payment Type": str(payment_type),
        "Price": int(price),
        "Transaction Type": str(transaction_type)
    },
    "event_type_uid": event_type_uid,
    "camera_id": camera_id,
    "time_ms": current_time_ms
}

st.markdown("**전송될 JSON 데이터 (Payload):**")
st.json(payload)

# 전송 버튼 클릭 시 동작
if st.button("🚀 토큰 발급 및 Helix 메시지 전송", use_container_width=True):
    if not api_key or not org_id or not camera_id or not event_type_uid:
        st.warning("⚠️ [1. 연동 정보 설정]의 4가지 항목을 모두 입력해주세요!")
    else:
        # 단계 1: 토큰 발급 진행
        with st.spinner("🔑 1단계: API 인증 토큰을 발급받는 중..."):
            short_lived_token = get_verkada_token(api_key)
            
        # 단계 2: 토큰 발급 성공 시 Helix 이벤트 전송
        if short_lived_token:
            with st.spinner("📡 2단계: Helix로 POS 데이터를 전송하는 중..."):
                headers = {
                    "content-type": "application/json",
                    "x-verkada-auth": short_lived_token 
                }
                
                try:
                    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
                    
                    if response.status_code == 200:
                        st.success("✅ Helix 이벤트 전송 성공!")
                        st.json(response.json())
                    else:
                        st.error(f"❌ 전송 실패 (상태 코드: {response.status_code})")
                        st.json(response.json())
                        
                except Exception as e:
                    st.error(f"❌ 데이터 통신 중 오류가 발생했습니다: {e}")
