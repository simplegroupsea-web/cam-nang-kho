import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Cẩm Nang Vận Hành Kho", page_icon="🤖", layout="centered")
st.title("🤖 Trợ Lý Vận Hành Phong Boutique")

st.info("📱 **Mẹo cho người dùng điện thoại Samsung:**\n\nNếu app không nhận diện được Tiếng Việt, với điện thoại Samsung tìm mục: **Bàn Phím Samsung** (thường là biểu tượng bánh răng ⚙️ trên bàn phím luôn) ➔ chọn mục **'Nhập bằng giọng nói'** ➔ chọn mục **'Nhập bằng giọng nói của Google'**.")

# 2. HỆ THỐNG MẬT KHẨU BẢO VỆ
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

# 3. KẾT NỐI AI VÀ ĐỌC DỮ LIỆU
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

# Bộ luật ngầm
luat_ngam = f"""
Ngươi là trợ lý vận hành nội bộ của Phong Boutique. 
Dưới đây là toàn bộ quy trình của cửa hàng:
{kho_du_lieu}

QUY TẮC BẮT BUỘC:
1. Nếu nhân viên hỏi về việc xem ảnh sản phẩm, áo hình gì, form dáng thế nào, TUYỆT ĐỐI KHÔNG tìm trong dữ liệu. Hãy trả lời chính xác câu này: "Bạn vào app này tìm ảnh theo tên nhé: https://tim-anh-san-pham.streamlit.app"
2. Với các câu hỏi khác, chỉ sử dụng thông tin trong DỮ LIỆU VẬN HÀNH để trả lời.
3. Nếu câu hỏi không có trong DỮ LIỆU VẬN HÀNH, phải trả lời nguyên văn: "Với câu hỏi này bạn hỏi quản lý để được giải đáp chính xác nhất."
4. Nếu trong dữ liệu có chứa các đoạn mã [ANH: ten_file.jpg], phải giữ nguyên TẤT CẢ các đoạn mã đó trong câu trả lời của ngươi.
"""

# Khởi tạo bản Pro 1.0 Quốc dân (Không bao giờ lỗi NotFound)
model = genai.GenerativeModel(model_name="gemini-pro")

# Khởi tạo bộ nhớ chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "images" in msg and msg["images"]:
            cols = st.columns(2)
            for i, img_path in enumerate(msg["images"]):
                with cols[i % 2]:
                    st.image(img_path, use_container_width=True)

# 4. XỬ LÝ KHUNG CHAT
if prompt := st.chat_input("Nhập câu hỏi hoặc bấm Micro trên bàn phím để nói..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Trộn bộ luật ngầm vào chung với câu hỏi của nhân viên
            cau_hoi_day_du = f"{luat_ngam}\n\nCâu hỏi của nhân viên: {prompt}"
            
            response = model.generate_content(cau_hoi_day_du)
            bot_reply = response.text
            
            images_to_show = []
            matches = re.findall(r'\[ANH:\s*(.*?)\s*\]', bot_reply)
            for img_name in matches:
                full_img_path = os.path.join("images_quy_trinh", img_name.strip())
                if os.path.exists(full_img_path):
                    images_to_show.append(full_img_path)

            clean_reply = re.sub(r'\[ANH:\s*.*?\s*\]', '', bot_reply).strip()
            
            st.markdown(clean_reply)
            
            if images_to_show:
                cols = st.columns(2)
                for i, img_path in enumerate(images_to_show):
                    with cols[i % 2]:
                        st.image(img_path, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": clean_reply, "images": images_to_show})
            
        except Exception as e:
            st.error(f"Lỗi kết nối AI: {e}. Vui lòng thử lại sau.")
