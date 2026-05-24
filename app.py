import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
import re

# ==========================================
# 1. TÌM ẢNH AVATAR SIÊU CẤP (TÌM MỌI NGÓC NGÁCH)
# ==========================================
avatar_path = None
# Quét cả thư mục gốc lẫn thư mục ảnh quy trình
possible_paths = [
    "avatar.png", "avatar.jpg", "avatar.jpeg",
    "images_quy_trinh/avatar.png", "images_quy_trinh/avatar.jpg", "images_quy_trinh/avatar.jpeg"
]
for path in possible_paths:
    if os.path.exists(path):
        avatar_path = path
        break

# ==========================================
# 2. GIAO DIỆN A CHÂU
# ==========================================
st.set_page_config(page_title="A Châu - Trợ Lý Vận Hành", page_icon=avatar_path if avatar_path else "👩‍💼")

col1, col2 = st.columns([1, 4])
with col1:
    if avatar_path:
        st.image(avatar_path, use_container_width=True)
    else:
        st.write("👩‍💼 (Đang tải ảnh...)")
with col2:
    st.title("A Châu - Trợ Lý Vận Hành")

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    pwd = st.text_input("Mật khẩu:", type="password")
    if st.button("Đăng nhập") and pwd == "phong123":
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# ==========================================
# 3. KẾT NỐI AI VÀ ĐỌC DỮ LIỆU
# ==========================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("quy_trinh.csv")
        return "\n".join([f"- {row['Vấn đề']}: {row['Nội dung quy trình (kèm tên ảnh nếu có)']}" for _, row in df.iterrows()])
    except:
        return "Chưa có dữ liệu."

system_instruction = f"""
Bạn là A Châu, trợ lý Phong Boutique, giọng miền Nam (nha, nghen, vô, coi, thiệt).
DỮ LIỆU: {load_data()}

QUY TẮC:
1. Trả lời nhiệt tình, giọng miền Nam.
2. Nếu câu hỏi không có trong dữ liệu: "Chết mồ, vụ này A Châu chưa được update. Bạn hỏi quản lý giùm mình nha!"
3. Nếu dòng dữ liệu CÓ chứa [ANH: ...], BẮT BUỘC đưa mã đó vào cuối câu trả lời.
"""

model = genai.GenerativeModel("gemini-3.1-flash-lite", system_instruction=system_instruction)

# ==========================================
# 4. XỬ LÝ KHUNG CHAT
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=avatar_path if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])
        if "images" in msg:
            cols = st.columns(2)
            for i, img in enumerate(msg["images"]):
                with cols[i % 2]: st.image(img)

if prompt := st.chat_input("Hỏi A Châu..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant", avatar=avatar_path):
        try:
            response = model.generate_content(prompt).text
            
            found_images = []
            for match in re.findall(r'\[ANH:\s*(.*?)\s*\]', response):
                img_path = os.path.join("images_quy_trinh", match.strip())
                if os.path.exists(img_path): found_images.append(img_path)
                
            clean_reply = re.sub(r'\[ANH:\s*.*?\s*\]', '', response).strip()
            st.markdown(clean_reply)
            
            if found_images:
                cols = st.columns(2)
                for i, img in enumerate(found_images):
                    with cols[i % 2]: st.image(img)
                    
            st.session_state.messages.append({"role": "assistant", "content": clean_reply, "images": found_images})
        except Exception as e:
            st.error(f"A Châu đang bận xíu, bạn thử lại nha! (Lỗi: {e})")
