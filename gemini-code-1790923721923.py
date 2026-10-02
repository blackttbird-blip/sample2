import streamlit as st
import requests
import random
import os
from pypdf import PdfReader

# 페이지 설정
st.set_page_config(page_title="소설 인물과의 대화", layout="centered", page_icon="📖")

# 세션 상태(State) 초기화
if 'user_role' not in st.session_state:
    st.session_state.user_role = None  # 'admin' or 'student'
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
if 'novel_text' not in st.session_state:
    st.session_state.novel_text = ""

# API 키 가져오기 (Streamlit Secrets 또는 환경 변수)
def get_api_key():
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    return os.getenv("OPENAI_API_KEY", "")

# PDF/TXT 파일에서 텍스트 추출 함수
def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        if uploaded_file.name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8", errors="ignore")
        elif uploaded_file.name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            extracted_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            return extracted_text.strip()
    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
        return ""
    return ""

# ==========================================
# 0. 초기 화면: 교사 vs 학생 접근 분기
# ==========================================
if st.session_state.user_role is None:
    st.title("📚 국어 수업: 소설 인물과의 인터뷰")
    st.write("접속할 역할을 선택해 주세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 교사 (관리자 설정)", use_container_width=True):
            st.session_state.user_role = "admin"
            st.rerun()
    with col2:
        if st.button("👩‍🎓 학생 (대화 시작하기)", type="primary", use_container_width=True):
            st.session_state.user_role = "student"
            st.rerun()

# ==========================================
# 1. 교사 화면 (비밀번호 인증 -> 설정 창)
# ==========================================
elif st.session_state.user_role == "admin":
    # 비밀번호 인증 화면
    if not st.session_state.logged_in:
        st.title("🔒 교사 인증")
        pwd = st.text_input("접근 비밀번호를 입력해주세요.", type="password")
        
        col_ok, col_back = st.columns([1, 1])
        with col_ok:
            if st.button("확인", use_container_width=True):
                if pwd == "6460":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("비밀번호가 일치하지 않습니다.")
        with col_back:
            if st.button("첫 화면으로", use_container_width=True):
                st.session_state.user_role = None
                st.rerun()

    # 교사 설정 화면
    else:
        st.title("⚙️ 수업 챗봇 환경 설정")
        st.caption("작품 정보와 등장인물을 설정해주세요. API 키는 시스템 보안 설정에서 자동으로 불러옵니다.")

        title = st.text_input("소설 제목", value=st.session_state.get('novel_title', ''), placeholder="예: 동백꽃, 소나기 등")
        author = st.text_input("작가 이름", value=st.session_state.get('author_name', ''), placeholder="예: 김유정, 황순원 등")
        chars = st.text_input("등장인물 (쉼표로 구분)", value=",".join(st.session_state.get('characters', [])), placeholder="예: 점순이, '나'")
        
        # 파일 업로드 (선택 사항)
        uploaded_file = st.file_uploader(
            "소설 본문 및 참고 학습 자료 (선택 사항)", 
            type=["txt", "pdf"],
            help="파일이 없으면 비워두셔도 됩니다. 비워둘 경우 AI가 자체 학습 지식을 활용해 인물에 몰입합니다."
        )
        st.caption("※ 파일 업로드 없이 공백으로 두셔도 작품명과 작가를 바탕으로 AI가 웹/문학 데이터 기반으로 정확히 답변합니다.")

        col_save, col_home = st.columns([3, 1])
        with col_save:
            if st.button("설정 완료 및 수업 열기", type="primary", use_container_width=True):
                if not title.strip() or not author.strip() or not chars.strip():
                    st.warning("소설 제목, 작가 이름, 등장인물은 필수로 입력해야 합니다.")
                else:
                    st.session_state.novel_title = title.strip()
                    st.session_state.author_name = author.strip()
                    st.session_state.characters = [c.strip() for c in chars.split(",") if c.strip()]
                    
                    # 파일이 제공된 경우 텍스트 추출, 없으면 빈 문자열
                    if uploaded_file is not None:
                        st.session_state.novel_text = extract_text_from_file(uploaded_file)
                    else:
                        st.session_state.novel_text = ""
                    
                    # 1~5 턴 중 오답이 발생할 턴수 무작위 결정
                    st.session_state.wrong_answer_turn = random.randint(1, 5)
                    st.session_state.setup_complete = True
                    st.session_state.turn_count = 0
                    st.session_state.chat_history = []
                    
                    st.success("수업 설정이 저장되었습니다! 이제 학생 화면에서 바로 대화할 수 있습니다.")
        with col_home:
            if st.button("역할 전환", use_container_width=True):
                st.session_state.user_role = None
                st.rerun()

# ==========================================
# 2. 학생용 대화 화면
# ==========================================
elif st.session_state.user_role == "student":
    if not st.session_state.setup_complete:
        st.warning("⚠️ 선생님이 아직 수업 설정을 완료하지 않았습니다. 잠시만 기다려주세요!")
        if st.button("첫 화면으로 돌아가기"):
            st.session_state.user_role = None
            st.rerun()
    else:
        st.title(f"📖 '{st.session_state.novel_title}' 인물과의 인터뷰")
        st.caption(f"작가: {st.session_state.author_name}")

        # 인물 선택 및 질문 턴 현황
        top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
        with top_col1:
            selected_char = st.selectbox("대화할 인물을 선택하세요:", st.session_state.characters)
        with top_col2:
            st.metric("남은 질문", f"{5 - st.session_state.turn_count}회")
        with top_col3:
            if st.button("나가기"):
                st.session_state.user_role = None
                st.rerun()

        # 대화 내역 출력
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.turn_count == 0:
            st.info(f"인물에게 궁금한 점을 질문해보세요! 총 5회의 기회가 주어지며, 인물이 거짓말을 섞어 말할 수도 있으니 주의 깊게 들어보세요.")

        # 5턴 종료 시
        if st.session_state.turn_count >= 5:
            st.success("🎉 모든 대화가 종료되었습니다! 결과물을 캡처하거나 다운로드하여 패들렛에 공유하고 오류를 찾아보세요!")
            
            chat_export = f"[{st.session_state.novel_title} ({st.session_state.author_name}) - {selected_char} 인물 대화 기록]\n\n"
            for m in st.session_state.chat_history:
                sender = "학생" if m["role"] == "user" else selected_char
                chat_export += f"{sender}: {m['content']}\n\n"
                
            st.download_button(
                label="📥 대화 내역 텍스트 다운로드",
                data=chat_export,
                file_name=f"{st.session_state.novel_title}_대화기록.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            # 질문 입력
            user_input = st.chat_input("인물에게 궁금한 점을 물어보세요...")
            
            if user_input:
                api_key = get_api_key()
                if not api_key:
                    st.error("OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
                    st.stop()

                # 사용자 메시지 반영
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.turn_count += 1

                # 시스템 프롬프트 조립
                system_prompt = (
                    f"너는 {st.session_state.author_name} 작가의 소설 '{st.session_state.novel_title}'의 등장인물인 '{selected_char}'야. "
                    f"소설 속 해당 인물에 완벽하게 빙의하여 1인칭 시점으로 대답해.\n\n"
                )
                
                # 파일 자료 유무에 따른 프롬프트 분기
                if st.session_state.novel_text.strip():
                    system_prompt += f"[제공된 소설 본문 및 참고자료]:\n{st.session_state.novel_text}\n위 자료를 최우선으로 반영해 답변해줘.\n\n"
                else:
                    system_prompt += (
                        f"[지식 참고 지침]: 제공된 별도 파일이 없으므로, 네가 알고 있는 {st.session_state.author_name}의 "
                        f"소설 '{st.session_state.novel_title}'의 원작 줄거리, 사건, 인물 관계, 시대적 배경 지식을 총동원하여 완벽하게 고증해 대답해.\n\n"
                    )

                # 공통 안전장치 및 페르소나 유지
                system_prompt += (
                    "[언어 수준 및 안전장치]:\n"
                    "1. 비속어 및 중학생에게 부적절한 어휘는 절대 사용하지 마.\n"
                    "2. 학생이 소설과 무관한 장난스러운 질문이나 현실 세계의 최신 이슈를 물어보면, "
                    "인물의 말투를 유지한 채 '무슨 뚱딴지같은 소리야? 그보다 (소설 속 핵심 사건) 때문에 머리가 아프네'와 같이 "
                    "방어하며 자연스럽게 소설 내용으로 화제를 돌려.\n\n"
                )

                # 무작위 오답(오류) 조건 주입
                if st.session_state.turn_count == st.session_state.wrong_answer_turn:
                    system_prompt += (
                        "[의도된 오답 조건 - 매우 중요]:\n"
                        "이번 답변에는 반드시 '사건의 원인과 결과를 교묘하게 왜곡'하거나 '인물의 진짜 속마음을 정반대로 표현'하는 "
                        "매력적이고 그럴듯한 거짓말(오류)을 1개 이상 섞어서 논리적 모순이 발생하게 답변해. "
                        "학생이 꼼꼼히 읽으면 찾아낼 수 있을 정도의 그럴듯한 왜곡이어야 해.\n"
                    )
                else:
                    system_prompt += "이번 답변은 소설의 사실 관계와 인물의 진짜 마음에 완벽히 부합하게 진실만을 답변해.\n"

                # 메시지 패키징
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(st.session_state.chat_history)

                # API 통신
                with st.chat_message("assistant"):
                    with st.spinner("인물이 답변을 생각하고 있습니다..."):
                        try:
                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {api_key}"
                            }
                            data = {
                                "model": "gpt-4o-mini",
                                "messages": messages,
                                "temperature": 0.7,
                                "max_tokens": 400
                            }
                            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
                            res.raise_for_status()

                            ai_reply = res.json()["choices"][0]["message"]["content"]
                            st.markdown(ai_reply)

                            st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                            st.rerun()

                        except Exception as e:
                            st.error("답변 생성 중 오류가 발생했습니다. 네트워크 상태나 API 설정을 확인해주세요.")
                            st.session_state.turn_count -= 1
requirements.txt 업데이트
