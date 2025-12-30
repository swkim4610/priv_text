import streamlit as st
import pandas as pd
import re
import pickle
import os

# 페이지 설정
st.set_page_config(
    page_title="개인정보 마스킹 프로그램",
    page_icon="🔒",
    #layout="wide"
)

# 커스텀 CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #155a8a;
    }
    </style>
""", unsafe_allow_html=True)

def name_detect(text):
    """이름 감지 함수"""
    # 성, 이름 데이터 및 패턴 불러오기
    with open('firstnames.pkl', 'rb') as file:
        firstname_dict = pickle.load(file)
    with open('lastnames.pkl', 'rb') as file:
        lastname_dict = pickle.load(file)
    with open('name_patterns.pkl', 'rb') as file:
        patterns = pickle.load(file)

    names = set()
    non_detects = set(["어머", "아버"])
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            name = match.group().strip()
            # 이름은 이름 사전에 성과 이름 조합이 존재할 때만 추가됨
            if name not in non_detects and len(name) >=3 and name[0] in lastname_dict and name[1:] in firstname_dict:
                names.add(name)
            if name not in non_detects and len(name) == 2 and name in firstname_dict:
                names.add(name)
            

    return sorted(list(names))

def name_masker(text, names_to_mask):
    """이름 마스킹 함수"""
    if not names_to_mask:
        return text
    masked = text
    for name in names_to_mask:
        masked = masked.replace(name, '*' * len(name))
    return masked

def pins_masker(text):
    """PIN 번호 마스킹"""
    pattern = r"\d{3}\s\d{3}\s\d{3}"
    st.session_state.pin_count = 0
    matches = re.findall(pattern, text)
    st.session_state.pin_count += len(matches)
    return re.sub(pattern, '*** *** ***', text)

def phones_masker(text):
    """전화번호 마스킹"""
    patterns = [
        r'\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}',
        r'\d{10,11}',
    ]
    
    st.session_state.phone_count = 0
    masked = text
    for pattern in patterns:
        matches = re.findall(pattern, text)
        st.session_state.phone_count += len(matches)
        masked = re.sub(pattern, '***-****-****', masked)
    
    return masked

def emails_masker(text):
    """이메일 마스킹"""
    pattern = r'([a-zA-Z0-9._-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    st.session_state.email_count = 0
    matches = re.findall(pattern, text)
    st.session_state.email_count += len(matches)

    def replace_email(match):
        local = match.group(1)
        domain = match.group(2)
        masked_local = local[:2] + '***' if len(local) > 2 else '***'
        return f'{masked_local}@{domain}'
    
    return re.sub(pattern, replace_email, text)

def urls_masker(text):
    """URL의 개인식별 부분 마스킹"""
    pattern = r'(http://[^\s]+|https://[^\s]+)'
    st.session_state.url_count = 0  
    matches = re.findall(pattern, text)
    st.session_state.url_count += len(matches)
    masked = re.sub(r'http://[^\s]+', 'http://***', text)
    masked = re.sub(r'https://[^\s]+', 'https://***', masked)
    return masked

def address_masker(text):
    patterns = [r'^(?=.*\d)(?=.*ro)(?=.*gu)(?=.*korea).*$', r'^(?=.*\d)(?=.*길)(?=.*구)(?=.*시).*$', r'^(?=.*\d)(?=.*로)(?=.*구)(?=.*시).*$']
    st.session_state.address_count = 0
    masked = text
    for pattern in patterns:  
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        st.session_state.address_count += len(matches)
        masked = re.sub(pattern, '주소 ***', masked, flags=re.MULTILINE | re.IGNORECASE)
    return masked

def replacers(masked):
    with open('replacers.pkl', 'rb') as file:
        replace_dict = pickle.load(file)
    
    for key, value in replace_dict.items():
        masked = masked.replace(key, value)

    return masked

def apply_masking(text, selected_names):
    """모든 마스킹 적용"""
    masked = name_masker(text, selected_names)
    masked = urls_masker(masked)
    masked = pins_masker(masked)
    masked = phones_masker(masked)
    masked = emails_masker(masked)
    masked = address_masker(masked)
    masked = replacers(masked)

    st.write(f"**마스킹 요약:**"
             f" 이름: {len(selected_names)}개 |"
             f" PIN 번호: {st.session_state.pin_count}개 |" 
             f" 전화번호: {st.session_state.phone_count}개 |"
             f" 이메일: {st.session_state.email_count}개 |"
             f" 주소: {st.session_state.address_count}개 |"
             f" URL: {st.session_state.url_count}개")

    return masked

# ========== 메인 UI ==========

# 헤더
st.markdown('<div class="main-header"><h1 style="text-align: center;">🔒 개인정보 마스킹 프로그램</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">텍스트 파일의 개인정보를 안전하게 마스킹합니다</div>', unsafe_allow_html=True)

st.markdown("""
    <style>
    [data-testid="stSidebar"][aria-expanded="true"]{
        min-width: 350px;
        max-width: 350px;
    }
    </style>
    """, unsafe_allow_html=True)

# 사이드바 - 정보
with st.sidebar:
    st.header("ℹ️ 사용 방법")
    st.markdown("""
    1. **파일 선택**: 마스킹할 .txt 또는 .csv 파일 선택
    2. **이름 확인**: 감지된 이름 목록 확인
    3. **선택**: 마스킹할 이름 수정 및 선택
    4. **실행**: '마스킹 실행' 버튼 클릭
    
    ---
    
    ### 📋 마스킹 대상
    - ✅ 이름
    - ✅ PIN 번호
    - ✅ 전화번호
    - ✅ 이메일
    - ✅ 주소            
    - ✅ URL (http, https)
    """)
    
    st.markdown("---")
    st.caption("🔐 모든 처리는 로컬에서 안전하게 이루어집니다.")


st.subheader("📁 Step 1: 파일 선택")
uploaded_file = st.file_uploader("upload file", type={"csv", "txt"})
if uploaded_file is not None:
    try:
        # 텍스트로 읽기
        st.session_state.text = uploaded_file.read().decode('utf-8')
        file_size = len(st.session_state.text)
        st.info(f"📊 파일 크기: {file_size:,} 문자")
    except Exception as e:
        st.error(f"파일 읽기 오류: {e}")

# 이름 감지
    with st.spinner('🔍 개인정보를 검색하는 중...'):
        st.session_state.names = name_detect(st.session_state.text)


    if st.session_state.names is not None:
        st.subheader("👤 Step 2: 이름 선택")

    if len(st.session_state.names) == 0:
        st.info("🎉 감지된 이름이 없습니다.")
    else:
        st.success(f"✅ {len(st.session_state.names)}개의 이름이 감지되었습니다.")

    # 데이터프레임으로 이름 표시
    df = pd.DataFrame({
        '선택': [False] * len(st.session_state.names),
        '이름': st.session_state.names
    })

    edited_df = st.data_editor(
        df,
        hide_index=True,
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "마스킹",
                help="마스킹할 이름을 선택하세요",
                default=True,
            )
        },
        width=800,
    )

    selected_names = edited_df[edited_df['선택']]['이름'].tolist()

    st.write(f"**선택된 항목:** {len(selected_names)}개")

    # 마스킹 실행 버튼
    st.markdown("---")
    if st.button("🚀 마스킹 실행", type="primary", use_container_width=True):
        with st.spinner('🔒 마스킹 처리 중...'):
            masked_text = apply_masking(st.session_state.text, selected_names)
            
            output_filename = 'masked_' + uploaded_file.name
            
            try:
                with open(output_filename, 'w', encoding='utf-8') as file:
                    file.write(masked_text)
                
                st.markdown(f'<div class="success-box">✅ <strong>{output_filename}</strong> 파일이 생성되었습니다!</div>', unsafe_allow_html=True)
                
                # 다운로드 버튼
                st.download_button(
                    label="📥 마스킹된 파일 다운로드",
                    data=masked_text,
                    file_name=output_filename,
                    mime="text/plain",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ 파일 저장 오류: {str(e)}")

    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 1rem;'>
        <small>개인정보 보호를 위한 마스킹 도구 | Made in SleepBetterBaby</small>
    </div>

    """, unsafe_allow_html=True)




