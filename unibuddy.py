import streamlit as st
import requests
import json
import pandas as pd
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os
import urllib3
from supabase import create_client

introduce_content = """
Hello! I am Uni Buddy, a chatbot designed to provide legal information and useful insights for international students who are newly enrolling at Kyung Hee University's Seoul Campus.  
I can assist you in the following areas:

### 🛂 Immigration/Departure Procedures
- Passport, visa, and residency period management.

### 📝 Visa
- Issuance and extension.

### 🏡 Residence and Living
- Residency management, accommodation, and foreigner registration (Alien Registration Card).

### 🎓 Admission and Campus Life
- Admission, language courses, academic programs, clubs, and overseas studies.

### 💳 Finance
- Currency exchange and credit card use.

### 🚗 Transportation
- Driver’s license and vehicle registration.

### 📞 Communication
- Phone, internet, and postal services.

### 🏥 Healthcare
- Health insurance and benefits.

### 💼 Employment and Part-Time Work
- Part-time jobs and employment guidance.

### 💻 Tax and Import Declarations
- Tax guidance and import declarations.

### 🛡️ Guidance from the Global Education Support Team
- Proxy services, training, academic schedules, graduation, and student IDs.


Uni Buddy is here to make your life in Korea easier and more seamless. Feel free to ask me anything!
"""

introduce_content_side = """
### 🛂 Immigration/Departure Procedures
- Passport, visa, and residency period management.

### 📝 Visa
- Issuance and extension.

### 🏡 Residence and Living
- Residency management, accommodation, and foreigner registration (Alien Registration Card).

### 🎓 Admission and Campus Life
- Admission, language courses, academic programs, clubs, and overseas studies.

### 💳 Finance
- Currency exchange and credit card use.

### 🚗 Transportation
- Driver’s license and vehicle registration.

### 📞 Communication
- Phone, internet, and postal services.

### 🏥 Healthcare
- Health insurance and benefits.

### 💼 Employment and Part-Time Work
- Part-time jobs and employment guidance.

### 💻 Tax and Import Declarations
- Tax guidance and import declarations.

### 🛡️ Guidance from the Global Education Support Team
- Proxy services, training, academic schedules, graduation, and student IDs.


Uni Buddy is here to make your life in Korea easier and more seamless. Feel free to ask me anything!
"""

# Supabase 설정
SUPABASE_URL = "https://uosuvgsfvgjhwhjnfnnl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvc3V2Z3NmdmdqaHdoam5mbm5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzIxMDU5MjMsImV4cCI6MjA0NzY4MTkyM30.IMOL836x4bWIUX9MYRzbDJmFgcmi-tAGrtr7dICdw-I"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SENDER_EMAIL = 'aalynm@gmail.com'#os.getenv("SENDER_EMAIL")
RECEIVER_EMAIL = 'aalynm@gmail.com'#os.getenv("RECEIVER_EMAIL")
EMAIL_PASSWORD = 'xgixcsgkttlxzlle' #os.getenv("EMAIL_PASSWORD")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

CHAT_BOT_HASH ="cf57364da8481c9be184052760448e4221f2b84fdae38a74a5ff050c6e09bf6b"
EMAIL_BOT_HASH ="084cec75b48cec949c79eb1189eb4eb4f45dc8befc112eca0e7af4d3726fb3b3"

def fetch_results():
    """
    Inquiry와 Answer 테이블을 Left Outer Join하여 결과를 구성합니다.
    """
    try:
        # inquiries 데이터 가져오기
        inquiries_response = supabase.table("inquiries").select("*").execute()
        inquiries = inquiries_response.data if inquiries_response.data else []

        # answers 데이터 가져오기
        answers_response = supabase.table("answers").select("*").execute()
        answers = answers_response.data if answers_response.data else []

        # Left Outer Join 수행
        results = []
        for inquiry in inquiries:
            # answers에서 해당 inquiry_id와 일치하는 데이터를 찾음
            matching_answer = next((answer for answer in answers if answer["inquiry_id"] == inquiry["id"]), None)

            # 결과 데이터 구성
            results.append({
                "Inquiry ID": inquiry["id"],
                "User Email": inquiry["user_email"],
                "User Name": inquiry["user_name"],
                "Original Inquiry": inquiry["original_inquiry"],
                "Translated Inquiry": inquiry["translated_inquiry"],
                "Translated Subject": inquiry["translated_subject"],
                "Email Send Allowed": inquiry["email_send_allowed"],
                "Email Send Not Allowed Reason": inquiry["email_send_not_allowed_reason"],
                "Answer Text": matching_answer["answer_text"] if matching_answer else "No Answer"
            })

        return results

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return []
def fetch_unanswered_inquiries():
    """
    Supabase를 사용하여 Answer가 없는 Inquiry를 필터링합니다.
    """
    try:
        # inquiries 데이터 가져오기
        inquiries_response = supabase.table("inquiries").select("*").execute()
        inquiries = inquiries_response.data if inquiries_response.data else []

        # answers 데이터 가져오기
        answers_response = supabase.table("answers").select("*").execute()
        answers = answers_response.data if answers_response.data else []

        # Answer가 없는 Inquiry 필터링
        unanswered_inquiries = []
        for inquiry in inquiries:
            # answers에서 해당 inquiry_id와 매칭되는 데이터가 없는 경우 추가
            has_answer = any(answer["inquiry_id"] == inquiry["id"] for answer in answers)
            if not has_answer and inquiry["email_send_allowed"]:
                unanswered_inquiries.append(inquiry)

        return unanswered_inquiries

    except Exception as e:
        logging.error(f"Error fetching unanswered inquiries: {e}")
        return []
    
def fetch_selected_inquiry(selected_inquiry_id):
    """
    Supabase를 사용하여 선택된 Inquiry를 가져옵니다.
    """
    try:
        # Supabase에서 특정 Inquiry ID에 해당하는 데이터 가져오기
        response = (
            supabase.table("inquiries")
            .select("*")
            .eq("id", selected_inquiry_id)  # ID가 선택된 Inquiry ID와 일치하는 조건
            .single()  # 단일 행만 반환
            .execute()
        )

        # 데이터 반환
        if response.data:
            return response.data
        else:
            return None

    except Exception as e:
        logging.error(f"Error fetching selected inquiry: {e}")
        return None
    
def insert_answer(inquiry_id, answer_text):
    """
    Supabase를 사용하여 Answer 데이터를 삽입합니다.

    :param inquiry_id: 연결된 Inquiry의 ID
    :param answer_text: 저장할 답변 텍스트
    """
    try:
        # Supabase에 Answer 데이터 삽입
        response = supabase.table("answers").insert({
            "inquiry_id": inquiry_id,
            "answer_text": answer_text
        }).execute()

        if response.data:
            logging.info("Answer inserted successfully.")
            return True
        else:
            logging.error("Failed to insert answer.")
            return False

    except Exception as e:
        logging.error(f"Error inserting answer: {e}")
        return False
# 저장 버튼 동작 정의
def save_answer():
    if answer_text.strip():
        # Supabase를 통해 Answer 데이터 삽입
        success = insert_answer(st.session_state["selected_inquiry_id"], answer_text)
        if success:
            st.success(f"Answer saved for Inquiry ID {st.session_state['selected_inquiry_id']}!")
            st.session_state["selected_inquiry_id"] = None  # 상태 초기화
        else:
            st.error("Failed to save the answer.")
    else:
        st.error("Answer cannot be empty.")

def get_exchange_rate(target_name):
    # 경고 비활성화
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 현재 날짜를 "YYYYMMDD" 형식으로 가져오기
    current_date = datetime.now().strftime("%Y%m%d")
    
    # API 요청 보내기
    exchange_api = f"https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {
        "authkey": "dVe9TS2xAJ8YdsCJedb7wFzXGJtonk7Z",
        "searchdate": current_date,
        "data": "AP01"
    }
    
    try:
        response = requests.get(exchange_api, params=params, verify=False)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                if target_name in item.get("cur_nm", ""):
                    return {"currency": item["cur_nm"], "rate": item["kftc_deal_bas_r"]}
            return {"error": "Currency not found"}
        else:
            return {"error": f"API request failed with status code {response.status_code}"}
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while making the API request: {str(e)}")
        logging.error(f"An error occurred while making the API request: {str(e)}")
        return {"error": f"An error occurred while making the API request: {str(e)}"}


# 이메일 발송 함수
def send_email(subject: str, sender_email: str, receiver_email: str, email_password: str, email_content: str, timezone):
    """
    이메일을 발송하는 함수.

    :param subject: 이메일 제목
    :param sender_email: 발신자 이메일 주소
    :param receiver_email: 수신자 이메일 주소
    :param email_password: 발신자 이메일 비밀번호
    :param email_content: 이메일 본문 내용 (HTML 형식)
    :param timezone: 타임존 객체 (datetime 모듈에서 사용)
    :return: None
    """
    # 이메일 메시지 생성
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"{subject} ({datetime.now(timezone).strftime('%Y-%m-%d')})"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.attach(MIMEText(email_content, 'html', 'utf-8'))

    try:
        # Gmail SMTP 서버에 연결
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, email_password)
            server.send_message(msg)
            logging.info("이메일 발송 완료")
    except Exception as e:
        logging.error(f"이메일 발송 실패: {str(e)}")
        raise


# Streamlit 앱의 새로운 버튼: Answer가 없는 행에 데이터를 추가
if "selected_inquiry_id" not in st.session_state:
    st.session_state["selected_inquiry_id"] = None  # 초기화

# 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "is_toggled" not in st.session_state:
    st.session_state["is_toggled"] = False

if "is_email" not in st.session_state:
    st.session_state["is_email"] = False

if "main" not in st.session_state:
    st.session_state["main"] = True

if "page_state" not in st.session_state:
    st.session_state["page_state"] = "Go Admin Page"

def change_page():
    if st.session_state["main"]:
        st.session_state["main"]=False
    else:
        st.session_state["main"]=True
    if st.session_state["page_state"] == "Go Admin Page":
        st.session_state["page_state"] = "Go Main Page"
    else:
        st.session_state["page_state"] = "Go Admin Page"

# 선택된 Inquiry ID를 저장하는 함수
def select_inquiry(inquiry_id):
    st.session_state["selected_inquiry_id"] = inquiry_id

# 선택된 Inquiry ID를 저장하는 함수
def select_inquiry(inquiry_id):
    st.session_state["selected_inquiry_id"] = inquiry_id


def change_mode():
    if st.session_state["is_toggled"]:
        st.session_state["is_toggled"] = False
    else:
        st.session_state["is_toggled"] = True

def insert_inquiry_from_content(content_data):
    """
    content_data에서 데이터를 추출해 Inquiry 테이블에 삽입합니다.
    """
    # content_data에서 필요한 데이터 추출
    user_email = content_data.get("userEmail", "")
    user_name = content_data.get("userName", "")  # Masked Inquiry를 user_name으로 변경
    original_inquiry = content_data.get("originalInquiry", "")
    translated_inquiry = content_data.get("translatedInquiry", "")
    translated_subject = content_data.get("translatedSubject", "")
    email_send_allowed = content_data.get("emailSendAllowed", False)
    email_send_not_allowed_reason = content_data.get("emailSendNotAllowedReason", "")

    # Supabase에 데이터 삽입
    try:
        response = supabase.table("inquiries").insert({
            "user_email": user_email,
            "user_name": user_name,
            "original_inquiry": original_inquiry,
            "translated_inquiry": translated_inquiry,
            "translated_subject": translated_subject,
            "email_send_allowed": email_send_allowed,
            "email_send_not_allowed_reason": email_send_not_allowed_reason
        }).execute()

        if response.status_code == 201:  # 성공적으로 삽입된 경우
            print("Inquiry inserted successfully!")
            return response.data  # 삽입된 데이터 반환
        else:
            print(f"Failed to insert inquiry: {response.status_code}, {response}")
            return None

    except Exception as e:
        print(f"Error inserting inquiry: {e}")
        return None

# API 호출 함수
def get_response(processed_q, hash_val, *args):
    print("start")
    headers = {
        "project": project_code,
        "apiKey": api_key,
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "hash": hash_val,
        "params": {
            "task": "모든 응답을 사용자가 입력한 언어와 동일한 언어로 구성하여 한국에 온 해외 유학생들이 주로 궁금해 하는 정보를 친절하게 알려주는 봇"
        },
        "messages": [
            {
                "role": "user",
                "content": processed_q
            }
        ]
    }
    if args:        
        body["messages"]=[args]
        # 튜플을 제거한 messages 표준화
        body['messages'] = [msg[0] if isinstance(msg, tuple) else msg for msg in body['messages']]
        print("body")
        print(body)
    try:
        response = requests.post(laas_chat_url, headers=headers, json=body)
        print(response.json())
        print("//")
        return response.json()

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# API 관련 설정
project_code = "KHU_PROMPTHON_022"
api_key = "3855624d8f05c68db4372704c3cbec3d87ceeeabfb83752e5090e8aaf608a8d5"
laas_chat_url = "https://api-laas.wanted.co.kr/api/preset/v2/chat/completions"

# 기본 설정
st.set_page_config(page_title="UniBuddy Chatbot", page_icon="🤖", layout="centered")

# 헤더 및 주요 텍스트 색상 스타일 추가
st.markdown(
    """
    <style>


    div.stButton > button {
        color: #000000;
        background-color: #ffffff;
        border: 1px solid #000000;
        border-radius: 5px;
        padding: 8px 16px;
        font-size: 16px;
    }

    [data-testid="stSidebar"] {
        background-color: #71AEE2;
    }
    textarea::placeholder {
        color: #b3b3b3;
    }
    .sidebar-divider {
        border-top: 1px dotted #ffffff;
        margin: 15px 0;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

# 페이지 헤더
st.title("UniBuddy Chatbot")

# 사이드바 정보
st.sidebar.header("🤝UniBuddy Chatbot for Students")
st.sidebar.write("This chatbot, powered by LAAS AI, assists international students in navigating university policies and other essential information.")
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

# 사이드바 - About
st.sidebar.subheader("About")
st.sidebar.write("This chatbot is designed specifically to support international students by answering questions related to university regulations and general guidance.")
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

# 사이드바 - Contact Us
st.sidebar.subheader("Contact Us")
st.sidebar.write("For more information, please contact:")
st.sidebar.write("hione@khu.ac.kr")
st.sidebar.button(st.session_state["page_state"],on_click=change_page)


if st.session_state["main"]:
    st.write("Ask your questions here 👇")
    # 사용자 입력 영역
    st.write("## Chat with our AI")

    if st.session_state["is_toggled"]:
        introduction_text = "Please type your inquiry in the following structure: Email, Name, Inquiry Details."
    else:
        introduction_text = "Type your question here..."

    question = st.chat_input(introduction_text)




    # API 호출 및 대화 기록 업데이트
    if question:
        st.session_state["is_email"] = False
        # 토글 상태에 따라 hash_value 변경
        if st.session_state["is_toggled"]:
            hash_value = EMAIL_BOT_HASH
            processed_q = question
        else:
            hash_value = CHAT_BOT_HASH
            processed_q = "mode_1"+ f"<{question}>"
        st.session_state["messages"].append({"role": "user", "content": question})
        with st.spinner("Connecting to LAAS AI..."):
            api_response = get_response(processed_q, hash_value)
            try:
                function_name = api_response['choices'][0]['message']['tool_calls'][0]['function']['name']
            except (KeyError, IndexError):
                function_name = None
            if "error" in api_response:
                assistant_message = api_response["error"]
            else:
                if st.session_state["is_toggled"]:
                    # content 필드 접근
                    content_raw = api_response["choices"][0]["message"]["content"]
                    # JSON 문자열을 Python 딕셔너리로 변환
                    content_data = json.loads(content_raw)
                    # emailSendAllowed 값 추출
                    email_send_allowed = content_data.get("emailSendAllowed", None)
                    if email_send_allowed == False:
                        assistant_message = content_data.get("emailSendNotAllowedReason")
                    else:
                        api_response_2 = get_response("mode_2 "+content_data.get("originalInquiry", None), CHAT_BOT_HASH)
                        content =api_response_2.get("choices", [{}])[0].get("message", {}).get("content", "No response received.")
                        # 첫 글자와 나머지 내용 분리
                        first_char = content[0]
                        assistant_message = content[1:].strip()  # 첫 글자 이후 내용
                        if first_char == "4":
                            st.session_state["is_email"] = True
                            st.session_state["c_d"] = content_data
                        else:
                            assistant_message = content_data.get("successMessage", None)
                            insert_inquiry_from_content(content_data)
                else:
                    if function_name == "get_exchange_rate":
                        arg = api_response['choices'][0]['message']['tool_calls'][0]['function']['arguments']
                        arguments_dict = json.loads(arg)
                        arg = arguments_dict.get("ques", "Value not found")
                        exchange_rate = get_exchange_rate(arg)
                        exchange_rate = json.dumps(exchange_rate, ensure_ascii=False)
                        print(exchange_rate)
                        tool_call_response = {
                        "role": "user",
                        "content": exchange_rate,
                        "toolCallId": api_response['choices'][0]['message']['tool_calls'][0]['id']
                                                }
                        api_response_3 = get_response(processed_q, hash_value, tool_call_response)
                        assistant_message = api_response_3.get("choices", [{}])[0].get("message", {}).get("content", "No response received.")
                    else:
                        assistant_message = api_response.get("choices", [{}])[0].get("message", {}).get("content", "No response received.")[1:].strip()
            st.session_state["messages"].append({"role": "assistant", "content": assistant_message})

    st.chat_message("assistant").write(introduce_content, unsafe_allow_html=True)


    # 채팅 메시지 출력
    for i, msg in enumerate(st.session_state["messages"]):
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    # 종료 버튼 동작 정의
    def exit_button_yes():
        st.session_state["is_email"] = False
        st.session_state["messages"].append({"role": "assistant", "content": st.session_state["c_d"].get("successMessage", None)})
        insert_inquiry_from_content(st.session_state["c_d"])

    # 종료 버튼 동작 정의
    def exit_button_no():
        st.session_state["is_email"] = False      

    if st.session_state["is_email"]:
        container = st.container()
        with container:
            col1, col2 = st.columns(2)  # 두 개의 열로 나누기

            # 첫 번째 버튼
            with col1:
                st.button("YES", on_click=exit_button_yes)

            # 두 번째 버튼
            with col2:
                st.button("NO", on_click=exit_button_no)

        # 토글 UI 생성
    is_toggled = st.checkbox("To Report", on_change=change_mode, value= st.session_state["is_toggled"] )

else:
    input_headers = {
                    "Content-Type": "application/json",
                    "apiKey": api_key,
                    "project": project_code
                        }
    # 데이터베이스 삭제 함수
    def delete_row_by_id(id_to_delete):
        # Step 1: 대상 행의 email_send_allowed 값 가져오기
        response_allowed = supabase.table("inquiries").select("email_send_allowed").eq("id", id_to_delete).execute()
        response_check = supabase.table("answers").select("id").eq("inquiry_id", id_to_delete).execute()
        # 삭제 작업 수행
        response_in = supabase.table("inquiries").delete().eq("id", id_to_delete).execute()

        if response_allowed and len(response_check.data) > 0:
            response_vector = requests.delete(f"https://api-laas.wanted.co.kr/api/document/JJIN_MAK/{id_to_delete}", headers=input_headers)
            print(response_vector)
            print("Yes")
        
        else:
            print("No")
        return f"{id_to_delete} is deleted!"

    st.write("Welcome to the Admin Page! 😊")
        # 두 개의 열 생성
    col1, col2, col3 = st.columns([2,1,1])

    # 첫 번째 열: 환영 메시지
    with col1:
        # Left Outer Join으로 Inquiry와 Answer 조인
        st.markdown("""
    #### 📋 Inquiry Database Overview (Admin Page)
    """, unsafe_allow_html=True)

    # 두 번째 열: ID 입력 및 삭제 버튼
    with col2:
        id_to_delete = st.text_input("Enter ID to Delete")
    with col3:
        if st.button("Delete Row"):
            if id_to_delete.isdigit():
                result_message = delete_row_by_id(int(id_to_delete))
            else:
                st.write("Please enter a valid numeric ID.")
    
    
    # 결과 호출
    results = fetch_results()

        # 데이터를 DataFrame으로 변환
    data = [
        {
            "Inquiry ID": row["Inquiry ID"],  # 딕셔너리 키를 사용해 접근
            "User Email": row["User Email"],
            "User Name": row["User Name"],
            "Original Inquiry": row["Original Inquiry"],
            "Translated Inquiry": row["Translated Inquiry"],
            "Translated Subject": row["Translated Subject"],
            "Email Send Allowed": row["Email Send Allowed"],
            "Email Send Not Allowed Reason": row["Email Send Not Allowed Reason"],
            "Answer Text": row.get("Answer Text", "No Answer")  # 키가 없으면 기본값 설정
        }
        for row in results
    ]

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)  # Streamlit에서 테이블 형태로 출력
    else:
        st.write("No data available in the database.")
        

    if st.button("✉️ Answer to Unanswered Inquiries"):
    # 호출 및 결과 출력
        unanswered_inquiries = fetch_unanswered_inquiries()
        if unanswered_inquiries:
            st.write("#### Answers to Unanswered Inquiries")
            
            # 나눌 열 개수 설정
            num_columns = (len(unanswered_inquiries) // 10) + (1 if len(unanswered_inquiries) % 10 != 0 else 0)
            cols = st.columns(num_columns)  # 열 생성
            
            for col_index, col in enumerate(cols):
                with col:
                    # 해당 열에 들어갈 아이템 추출
                    start_index = col_index * 10
                    end_index = start_index + 10
                    inquiries_in_column = unanswered_inquiries[start_index:end_index]
                    
                    for idx, inquiry in enumerate(inquiries_in_column, start=start_index + 1):
                        index = f"{idx}. "
                        # 버튼 표시
                        st.button(
                            label=f"{index}작성자: {inquiry['user_name']} / 제목: {inquiry['translated_subject']}",
                            key=f"title_{inquiry['id']}",
                            on_click=select_inquiry,  # 함수 호출
                            args=(inquiry["id"],)  # 함수에 전달할 인수
                        )
        else:
            st.info("No unanswered inquiries found.")

    # 답변 입력 창
    if st.session_state["selected_inquiry_id"]:
        # 선택된 Inquiry 가져오기
        selected_inquiry = fetch_selected_inquiry(st.session_state["selected_inquiry_id"])

        if selected_inquiry:
            st.write(f"#### 제목: {selected_inquiry['translated_subject']} / 작성자: {selected_inquiry['user_name']}")
            st.write(f"**Translated Inquiry**: {selected_inquiry['translated_inquiry']}")
            st.write(f"**Original Inquiry**: {selected_inquiry['original_inquiry']}")


            # 사용자로부터 답변 입력받기
            answer_text_ep = st.text_area("Enter your answer", key="answer_input")
            
            # 저장 버튼 동작 정의
            def save_answer():
                if answer_text_ep.strip():
                    # Answer 데이터 삽입 실행
                    if selected_inquiry and answer_text_ep.strip():  # 선택된 Inquiry와 답변 텍스트가 있는 경우
                        response = supabase.table("answers").insert({
                            "inquiry_id": selected_inquiry["id"],  # 선택된 Inquiry ID
                            "answer_text": answer_text_ep  # 입력된 답변 텍스트
                        }).execute()
                    else:
                        st.warning("Please provide an answer text and select an inquiry.")
                    try:
                        send_email(
                            subject="RE:" + selected_inquiry["translated_subject"],
                            sender_email=SENDER_EMAIL,
                            receiver_email=selected_inquiry["user_email"],
                            email_password=EMAIL_PASSWORD,
                            email_content = f"""
                            Your inquiry:<br>{selected_inquiry['original_inquiry']}<br><br>
                            Answer:<br>{answer_text_ep}
                            """,
                            timezone=datetime.now().astimezone().tzinfo
                        )
                        input_data = {
                            "text": "질의:"+selected_inquiry["original_inquiry"]+" 답변: "+answer_text_ep
                        }   
                        doc_id=selected_inquiry["original_inquiry"]
                        laas_doc_url = f"https://api-laas.wanted.co.kr/api/document/JJIN_MAK/{doc_id}"
                        r = requests.put(laas_doc_url, headers=input_headers, json=input_data)
                            # Handle response
                        if r.status_code == 200:
                            print("Document updated successfully!")
                            print("Response data:", r.json())
                        else:
                            print(f"Failed to update document. Status code: {r.status_code}")
                            print("Error details:", r.text)
                    except Exception as e:
                        print(f"에러 발생: {e}")
                    st.session_state["selected_inquiry_id"] = None  # 상태 초기화
                else:
                    st.error("Answer cannot be empty.")

            # 종료 버튼 동작 정의
            def exit_answer():
                st.session_state["selected_inquiry_id"] = None

            # Save Answer 버튼
            st.button("Save Answer", on_click=save_answer)

            # Exit 버튼
            st.button("Exit", on_click=exit_answer)






