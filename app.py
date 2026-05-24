import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
import re

# ==========================================
# 1. TÌM ẢNH AVATAR THÔNG MINH
# ==========================================
# Tự động tìm ảnh dù đuôi là jpg, jpeg hay png
avatar_path = None
for ext in ["avatar.jpeg", "avatar.jpg", "avatar.png", "avatar.JPG", "avatar.JPEG"]:
    if os.path.exists(ext):
        avatar_path = ext
        break

# ==========================================
# 2. CẤU HÌNH GIAO DIỆN VÀ THƯƠNG HIỆU A CHÂU
# ==========================================
st.set_page_config(page_title="A Châu - Trợ Lý Vận Hành", page_icon="👩‍💼", layout="centered")

# Thiết kế Layout: Ảnh A Châu bên trái, Tiêu đề bên phải
col1, col2 = st.columns([1, 4])
with col1:
    if avatar_path:
        # Bo tròn ảnh cho đẹp (Streamlit mặc định hiển thị ảnh vuông, ta dùng css bo tròn nhẹ)
        st.image(avatar_path, use_container_width=True)
    else:
        st.write("👩‍💼 (Chưa tải ảnh)")

with col2:
    st.title("A Châu - Trợ Lý Vận Hành")

st.info("📱 **Mẹo cho điện thoại Samsung:** Nếu app không nhận Tiếng Việt ➔ Tìm: **Bàn Phím Samsung** (biểu tượng ⚙️) ➔ **Nhập bằng giọng nói** ➔ **Nhập bằng giọng nói của Google**.")

# ==========================================
# 3. HỆ THỐNG MẬT KHẨU BẢO VỆ
# ==========================================
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

# ==========================================
# 4. KẾT NỐI AI VÀ ĐỌC DỮ LIỆU TỪ FILE CSV
# ==========================================
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

system_instruction = f"""
Bạn tên là A Châu, là một trợ lý vận hành nội bộ cực kỳ thân thiện, nhiệt tình và lanh lẹ của Phong Boutique. 
ĐẶC BIỆT: Bạn BẮT BUỘC phải dùng văn phong, từ vựng và cách nói chuyện đặc trưng của người miền Nam (giọng Sài Gòn). Hãy xưng "A Châu" hoặc "mình" và gọi người hỏi là "bạn" hoặc "mọi người". Thường xuyên đệm các từ: "nha", "nghen", "ha", "xài", "vô", "coi", "chút xíu", "thiệt", "giùm mình"...

Dưới đây là DỮ LIỆU VẬN HÀNH của cửa hàng:
{kho_du_lieu}

QUY TẮC PHẢI TUÂN THỦ TUYỆT ĐỐI:
1. Trả lời linh hoạt, tự nhiên dựa trên DỮ LIỆU VẬN HÀNH. Diễn đạt lại theo giọng miền Nam, không copy-paste khô khan.
2. Nếu nhân viên hỏi về việc xem ảnh sản phẩm, form dáng, màu áo... hãy từ chối khéo: "Mấy vụ hình dáng, màu sắc này bạn vô app này tra cứu tên áo rồi coi giùm A Châu nghen: https://tim-anh-san-pham.streamlit.app"
3. Nếu câu hỏi nằm ngoài dữ liệu: "Chết mồ, vụ này A Châu chưa được update. Bạn hỏi lại quản lý giùm mình nha!"
4. QUAN TRỌNG NHẤT VỀ ẢNH: CHỈ ĐƯỢC PHÉP chèn đoạn mã [ANH: ten_file.xxx] vào câu trả lời NẾU ĐÚNG DÒNG QUY TRÌNH ĐÓ CÓ CHỨA MÃ. Tuyệt đối KHÔNG lấy mã ảnh của quy trình này gắn sang câu trả lời của quy trình khác.
"""

model = genai.GenerativeModel(
    model_name="gemini-3.1-flash-lite",
    system_instruction=system_instruction
)

# ==========================================
# 5. XỬ LÝ KHUNG CHAT & HIỂN THỊ LỊCH SỬ
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    # Nếu là bot thì hiện mặt A Châu, nếu là user thì dùng icon mặc định
    chat_avatar = avatar_path if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=chat_avatar):
        st.markdown(msg["content"])
        if "images" in msg and msg["images"]:
            cols = st.columns(2)
            for i, img_path in enumerate(msg["images"]):
                with cols[i % 2]:
                    st.image(img_path, use_container_width=True)

if prompt := st.chat_input("Hỏi A Châu về quy trình kho..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=avatar_path):
        try:
            response = model.generate_content(prompt)
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
            st.error(f"A Châu đang bận chút xíu, bạn thử lại sau nha! Lỗi: {e}")
