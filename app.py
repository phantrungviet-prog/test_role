import os 
import streamlit as st
from google import genai
from google.genai import types

# 1. Cấu hình trang Streamlit
st.set_page_config(page_title="PoC Trợ lý Pháp lý & Kiểm toán Hợp đồng AI", layout="wide")
st.title("🏛️ PoC: Trợ lý AI Pháp lý Du lịch & PCCC (Gemini Agent)")

# 2. Nhập API Key (Hoặc set cứng biến môi trường)
# api_key = st.sidebar.text_input("Nhập Google Gemini API Key:", type="password")
# api_key = "AQ.Ab8RN6LtWmc4hgyN-U_QhpFBkqDB2D0pP0QN-yvmlhFA98ZAGA"
api_key = st.secrets["GEMINI_API_KEY"]
if not api_key:
    st.warning("Vui lòng nhập API Key để bắt đầu sử dụng.")
    st.stop()

# Khởi tạo Gemini Client
client = genai.Client(api_key=api_key)

# 3. Khu vực Upload tài liệu pháp luật và hợp đồng
st.sidebar.header("📁 Kho tài liệu & Hợp đồng đầu vào")
uploaded_files = st.sidebar.file_uploader(
    "Tải lên các file Luật (PDF) và Hợp đồng cần kiểm tra:",
    type=["pdf", "txt", "docx"],
    accept_multiple_files=True
)

# 4. Định nghĩa System Prompt (Rất quan trọng để ép AI tuân thủ)
SYSTEM_INSTRUCTION = """
Bạn là một Trợ lý AI Pháp lý và Kiểm toán viên Tuân thủ chuyên nghiệp, chuyên gia về quy định ngành Du lịch, Khách sạn, Lữ hành và Phòng cháy chữa cháy (PCCC) tại Việt Nam.

NGUỒN DỮ LIỆU:
- Bạn CHỈ ĐƯỢC PHÉP sử dụng các văn bản pháp luật có trong các file được người dùng đính kèm làm căn cứ pháp lý.
- Tuyệt đối KHÔNG tự bịa đặt điều luật ngoài đời nếu không có trong tài liệu.

NHIỆM VỤ:
1. Trả lời câu hỏi tra cứu luật của người dùng kèm trích dẫn chính xác (Tên văn bản, Điều, Khoản).
2. Khi người dùng tải lên hợp đồng/chứng từ, hãy đối chiếu với file luật đính kèm, phát hiện thiếu sót hoặc vi phạm và lập Báo cáo kiểm toán với các mức độ: [ĐẠT], [CẢNH BÁO RỦI RO], [VI PHẠM PHÁP LUẬT].
"""

# 5. Giao diện Chat chính
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_query = st.chat_input("Nhập câu hỏi pháp lý hoặc yêu cầu kiểm tra hợp đồng...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("AI đang đọc tài liệu và phân tích..."):
            try:
                # Xử lý các file được upload để đưa vào ngữ cảnh của Gemini
                contents = []
                
                # Nếu có file upload, ta lưu tạm và đính kèm vào request
                if uploaded_files:
                    for file in uploaded_files:
                        bytes_data = file.read()
                        # Đính kèm file trực tiếp vào luồng gọi Gemini
                        contents.append(
                            types.Part.from_bytes(
                                data=bytes_data,
                                mime_type=file.type if file.type else "application/pdf"
                            )
                        )
                
                # Thêm câu hỏi người dùng vào cuối contents
                contents.append(user_query)

                # Gọi model Gemini 2.5 Flash (tối ưu tốc độ và context lớn)
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1, # Giảm sáng tạo để đảm bảo tính chính xác pháp lý
                    )
                )


                
                bot_reply = response.text
                st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi gọi Gemini API: {e}")
