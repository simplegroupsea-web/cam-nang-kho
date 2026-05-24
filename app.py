import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
import re

# 1. CẤU HÌNH GIAO DIỆN APP
st.set_page_config(page_title="Cẩm Nang Vận Hành Kho", page_icon="🤖", layout="centered")
st.title("🤖 Trợ Lý Vận Hành Phong Boutique")

st.info("📱 **Mẹo cho người dùng điện thoại Samsung:**\n\nNếu app không nhận diện được Tiếng Việt, với điện thoại Samsung tìm mục: **Bàn Phím Samsung** (thường là biểu tượng bánh răng ⚙️ trên bàn phím luôn) ➔ chọn mục **'Nhập bằng giọng nói'** ➔ chọn mục **'Nhập bằng giọng nói của Google'**.")

# 2. HỆ THỐNG MẬT KHẨU BẢO VỆ NỘI BỘ
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.warning("Vui lòng nhập mật khẩu nội bộ để truy cập hệ thống.")
    pwd = st.text_input("Mật khẩu:", type="password")
    if st.button("Đăng nhập"):
        if pwd == "phong123": 
            st.session_state.authenticated = True
            st.rerun()
    st.stop() 

# 3. KẾT NỐI AI VÀ ĐỌC DỮ LIỆU TỪ FILE CSV
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data
def load_knowledge_base():
    try:
        df = pd.read_csv("quy_trinh.csv")
        knowledge = "DỮ LIỆU VẬN HÀNH:\n"
        for index, row in df.iterrows():
            knowledge += f"- {row['Vấn đề']}: {row['Nội dung quy trình (kèm tên ảnh nếu có)']}\n"
        return knowledge
    except Exception as e:
        return "Chưa có dữ liệu quy trình."

kho_du_lieu = load_knowledge_base()

# Bộ luật ngầm - Định hình "nhân cách" miền Nam dễ mến cho AI
system_instruction = f"""
Bạn là một trợ lý vận hành nội bộ cực kỳ thân thiện, nhiệt tình và lanh lẹ của Phong Boutique. 
ĐẶC BIỆT: Bạn BẮT BUỘC phải dùng văn phong, từ vựng và cách nói chuyện đặc trưng của người miền Nam (giọng Sài Gòn). Hãy xưng "mình" và gọi người hỏi là "bạn" hoặc "mọi người". Thường xuyên đệm các từ ngữ dễ thương của miền Nam như: "nha", "nghen", "ha", "xài", "vô", "coi", "chút xíu", "thiệt", "giùm mình"...

Dưới đây là DỮ LIỆU VẬN HÀNH của cửa hàng:
{kho_du_lieu}

QUY TẮC PHẢI TUÂN THỦ TUYỆT ĐỐI:
1. Trả lời linh hoạt, tự nhiên dựa trên DỮ LIỆU VẬN HÀNH. Không được copy-paste y hệt dữ liệu thô mà hãy diễn đạt lại theo giọng miền Nam cho dễ hiểu, gần gũi.
2. Nếu nhân viên hỏi về việc xem ảnh sản phẩm, form dáng, màu áo... hãy từ chối khéo và điều hướng: "Mấy vụ hình dáng, màu sắc này bạn vô app này tra cứu tên áo rồi coi giùm mình nghen: https://tim-anh-san-pham.streamlit.app"
3. Nếu câu hỏi nằm ngoài dữ liệu, hãy xin lỗi nhẹ nhàng: "Chết mồ, vụ này mình chưa được update. Bạn hỏi lại quản lý giùm mình để được giải đáp chuẩn xác nhất nha!"
4. QUAN TRỌNG NHẤT VỀ ẢNH: Nếu trong DỮ LIỆU VẬN HÀNH có chứa mã [ANH: ten_file.xxx], bạn BẮT BUỘC phải giữ nguyên xi đoạn mã [ANH: ten_file.xxx] đó và chèn vào cuối câu trả lời của bạn. Không được tự ý xóa hoặc sửa đoạn mã này!
"""

# Khởi tạo mô hình AI thế hệ mới với bản 3.1 Flash-Lite tối ưu tốc độ
model = genai.GenerativeModel(
    model_name="gemini-3.1-flash-lite",
    system_instruction=system_instruction
)

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị các câu chat cũ ra màn hình
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "images" in msg and msg["images"]:
            cols = st.columns(2)
            for i, img_path in enumerate(msg["images"]):
                with cols[i % 2]:
                    st.image(img_path, use_container_width=True)

# 4. XỬ LÝ KHI NHÂN VIÊN CHAT
if prompt := st.chat_input("Nhập câu hỏi hoặc bấm Micro trên bàn phím để nói..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Gửi câu hỏi cho AI xử lý
            response = model.generate_content(prompt)
            bot_reply = response.text
            
            # Quét tìm mã ảnh [ANH: ...] trong câu trả lời của AI
            images_to_show = []
            matches = re.findall(r'\[ANH:\s*(.*?)\s*\]', bot_reply)
            for img_name in matches:
                full_img_path = os.path.join("images_quy_trinh", img_name.strip())
                if os.path.exists(full_img_path):
                    images_to_show.append(full_img_path)

            # Xóa đoạn mã [ANH: ...] thô để text hiển thị đẹp mắt hơn
            clean_reply = re.sub(r'\[ANH:\s*.*?\s*\]', '', bot_reply).strip()
            
            # Trả lời văn bản bằng giọng miền Nam
            st.markdown(clean_reply)
            
            # Bung ảnh ra (nếu có mã ảnh trùng khớp)
            if images_to_show:
                cols = st.columns(2)
                for i, img_path in enumerate(images_to_show):
                    with cols[i % 2]:
                        st.image(img_path, use_container_width=True)

            # Lưu vào lịch sử chat
            st.session_state.messages.append({"role": "assistant", "content": clean_reply, "images": images_to_show})
            
        except Exception as e:
            st.error(f"Lỗi kết nối AI: {e}. Vui lòng thử lại sau.")
