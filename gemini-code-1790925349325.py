import streamlit as st
import requests
import random

# 페이지 기본 설정
st.set_page_config(page_title="소설 인물과의 대화", layout="centered")

# 세션 상태(State) 초기화 - 새로고침해도 데이터 유지 및 보안 처리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'turn_count' not in st.session_state:
    st.session_state.turn_count = 0
if 'wrong_answer_turn' not in st.session_state:
    st.session_state.wrong_answer_turn = 0

# --- 1단계: 로그인 화면 ---
if not st.session_state.logged_in:
    st.title("🔒 관리자 접근")
    pwd = st.text_input("교사 설정 화면 접근 비밀번호를 입력해주세요.", type="password")
    if st.button("확인"):
        if pwd == "6460":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")

# --- 2단계: 교사 설정 화면 ---
elif st.session_state.logged_in and not st.session_state.setup_complete:
    st.title("⚙️ 수업 및 챗봇 설정")
    
    api_key = st.text_input("OpenAI API 키 (학생에게 절대 노출되지 않습니다)", type="password")
    title = st.text_input("소설 제목", placeholder="예: 동백꽃, 소나기 등")
    chars = st.text_input("등장인물 (쉼표로 구분하여 여러 명 입력 가능)", placeholder="예: 점순이, '나'")
    novel_text = st.text_area(
        "소설 본문 및 참고 학습 자료", 
        placeholder="소설의 핵심 내용이나 인물 성격 등을 요약해서 넣어주세요.",
        height=200
    )
    st.caption("※ 전체 본문이 너무 길면 오류가 발생할 수 있으니, 핵심 줄거리와 주요 갈등 상황 위주로 요약해서 입력해 주세요.")
    
    if st.button("설정 완료 및 수업 시작하기", type="primary", use_container_width=True):
        if api_key and title and chars and novel_text:
            st.session_state.api_key = api_key
            st.session_state.novel_title = title
            # 쉼표 기준으로 나누고 공백 제거
            st.session_state.characters = [c.strip() for c in chars.split(",") if c.strip()]
            st.session_state.novel_text = novel_text
            # 1~5 턴 중에서 오답을 낼 턴을 무작위로 하나 생성
            st.session_state.wrong_answer_turn = random.randint(1, 5)
            st.session_state.setup_complete = True
            st.rerun()
        else:
            st.warning("모든 항목을 꼼꼼히 입력해주세요.")

# --- 3단계: 학생용 대화 화면 ---
elif st.session_state.setup_complete:
    st.title(f"📖 '{st.session_state.novel_title}' 인물과의 대화")
    
    # 상단 메뉴 구성 (인물 선택 & 남은 턴 수 표시)
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_char = st.selectbox("대화할 인물을 선택하세요:", st.session_state.characters)
    with col2:
        st.info(f"남은 질문: **{5 - st.session_state.turn_count}번**")

    # 채팅 내역 화면에 출력
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if st.session_state.turn_count == 0:
        st.info("인물을 선택하고 대화를 시작해보세요!")

    # 대화 5턴 종료 시 처리
    if st.session_state.turn_count >= 5:
        st.success("모든 대화가 종료되었습니다. 결과물을 다운로드하거나 화면을 캡처하여 패들렛에 공유하고 오류를 찾아보세요!")
        
        # 다운로드용 텍스트 생성
        chat_export = f"[{st.session_state.novel_title} - {selected_char} 인물과의 대화 내역]\n\n"
        for m in st.session_state.chat_history:
            role_name = "학생" if m["role"] == "user" else selected_char
            chat_export += f"{role_name}: {m['content']}\n\n"
            
        st.download_button(
            label="📥 대화 내역 다운로드 (텍스트 파일)",
            data=chat_export,
            file_name=f"{st.session_state.novel_title}_대화내역.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        # 질문 입력 (st.chat_input은 턴 종료 시 렌더링되지 않아 자연스럽게 비활성화됨)
        user_input = st.chat_input("인물에게 궁금한 점을 물어보세요...")
        
        if user_input:
            # 학생 메시지 화면에 띄우고 저장
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.turn_count += 1
            
            # OpenAI API 요청용 시스템 프롬프트 조립
            system_prompt = f"너는 '{st.session_state.novel_title}'의 등장인물인 '{selected_char}'야. 제공된 [소설 본문 및 참고자료]를 바탕으로 그 인물에 완벽하게 빙의해 1인칭 시점으로 대답해.\n\n"
            system_prompt += f"[소설 본문 및 참고자료]:\n{st.session_state.novel_text}\n\n"
            system_prompt += "[기본 설정 및 안전장치]:\n"
            system_prompt += "1. 비속어 및 중학생에게 부적절한 어휘는 절대 사용하지 마.\n"
            system_prompt += "2. 학생이 소설과 무관한 장난스러운 질문이나 현실 세계의 질문을 던지면, 인물의 말투를 유지한 채 '무슨 뚱딴지같은 소리야? 그보다 (소설 속 핵심 사건) 때문에 머리가 아프네'와 같이 방어하며 자연스럽게 소설 내용으로 화제를 돌려.\n\n"
            
            # 핵심: 무작위 생성된 오답 턴일 경우 프롬프트 강제 주입
            if st.session_state.turn_count == st.session_state.wrong_answer_turn:
                system_prompt += "[중요: 의도된 오답 조건]:\n이번 답변에는 반드시 '사건의 원인과 결과를 교묘하게 왜곡'하거나 '인물의 진짜 속마음을 정반대로 표현'하는 매력적이고 그럴듯한 거짓말(오류)을 1개 이상 섞어서 논리적 모순이 발생하게 답변해.\n"
            else:
                system_prompt += "이번 답변은 소설의 내용과 인물의 성격에 완벽히 일치하게 사실만을 기반으로 답변해.\n"
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(st.session_state.chat_history)
            
            # 로딩 애니메이션 (spinner) 및 API 호출
            with st.chat_message("assistant"):
                with st.spinner("인물이 답변을 생각하고 있습니다..."):
                    try:
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {st.session_state.api_key}"
                        }
                        data = {
                            "model": "gpt-4o-mini",
                            "messages": messages,
                            "temperature": 0.7,
                            "max_tokens": 400
                        }
                        # 외부 라이브러리 최소화를 위해 openai 패키지 대신 requests 사용
                        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
                        response.raise_for_status() # HTTP 에러 발생 시 예외 처리
                        
                        ai_reply = response.json()["choices"][0]["message"]["content"]
                        st.markdown(ai_reply)
                        
                        # AI 답변 저장 후 화면 새로고침
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"API 호출 중 오류가 발생했습니다. API 키나 인터넷 연결을 확인해주세요.")
                        st.session_state.turn_count -= 1 # 오류 시 턴 수 차감 복구