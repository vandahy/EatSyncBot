import os
import sys
import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import datetime
from typing import Optional
import io       
import base64   
import genkit.core.schema

# ==============================================================================
# [PATCH FIX] VÁ LỖI GENKIT ALPHA
# ==============================================================================
_original_to_json_schema = genkit.core.schema.to_json_schema
def _safe_to_json_schema(schema_or_type):
    try:
        return _original_to_json_schema(schema_or_type)
    except Exception:
        return {"type": "object", "description": "Skipped due to serialization error"}
genkit.core.schema.to_json_schema = _safe_to_json_schema

# === IMPORT THƯ VIỆN GENKIT ===
import google.generativeai as genai 
import json
from pydantic import BaseModel, Field

# Thư viện ảnh và Telegram
from PIL import Image
from telethon import TelegramClient, events
from dotenv import load_dotenv

# === Cấu hình đường dẫn ===
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# def get_path(filename):
#     return os.path.join(BASE_DIR, filename)
if getattr(sys, 'frozen', False):
    # Nếu đang chạy bằng file EXE, lấy đường dẫn của file EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Nếu đang chạy bằng file .py, lấy đường dẫn của file code
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename):
    return os.path.join(BASE_DIR, filename)
# === Load file .env ===
env_path = get_path('.env')
load_dotenv(env_path)

# === Kiểm tra biến môi trường ===
try:
    VAR_ID = os.getenv("API_ID")
    VAR_HASH = os.getenv("API_HASH")
    VAR_KEY = os.getenv("GEMINI_API_KEY")

    if not VAR_ID or not VAR_HASH or not VAR_KEY:
        raise ValueError(f"File .env bị thiếu thông tin!\nĐang đọc từ: {env_path}")

    API_ID = int(VAR_ID)
    API_HASH = VAR_HASH
    GEMINI_API_KEY = VAR_KEY

except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("LỖI CẤU HÌNH BOT", f"❌ Bot không thể khởi động!\n\nNguyên nhân: {e}")
    sys.exit()

GROUP_ID = [-268078931, -5162755092]

# === 1. KHỞI TẠO GOOGLE AI (RAW SDK) ===
# Genkit Alpha đang lỗi Pydantic/Serialization, chuyển sang dùng SDK gốc cho ổn định
genai.configure(api_key=GEMINI_API_KEY)

# Sử dụng model đã test thành công
MODEL_NAME = 'models/gemini-2.5-flash-preview-09-2025' 
model = genai.GenerativeModel(MODEL_NAME)

# === 2. ĐỊNH NGHĨA SCHEMA ===
class MenuResult(BaseModel):
    is_menu: bool = Field(description="True nếu là ảnh menu.")
    has_requested_day: bool = Field(description="True nếu tìm thấy ngày yêu cầu.")
    reason: str = Field(description="Giải thích ngắn gọn vị trí tìm thấy hoặc lý do không tìm thấy.")
    dishes: list[str] = Field(description="Danh sách món ăn.")

class MenuInput(BaseModel):
    image_base64: str = Field(description="Ảnh thực đơn đã mã hóa Base64.")
    day_str: str = Field(description="Ngày cần tìm món (Ví dụ: THỨ 2).")

# === [HÀM MỚI] TỐI ƯU ẢNH SIÊU TỐC ===
def optimize_image_for_ai(pil_image: Image.Image) -> str:
    """
    Resize ảnh nếu quá lớn và nén JPEG chất lượng cao để gửi nhanh hơn.
    Giữ nguyên độ nét text bằng subsampling=0.
    """
    # 1. Resize nếu ảnh quá to (trên 2000px) để giảm tải upload
    # Gemini Flash đọc tốt ở mức 1500-2000px, 4000px là thừa thãi
    max_dimension = 2048
    width, height = pil_image.size
    
    if max(width, height) > max_dimension:
        scale_factor = max_dimension / max(width, height)
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        # Dùng LANCZOS để giữ nét chữ khi thu nhỏ
        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 2. Convert sang RGB để lưu JPEG (phòng trường hợp ảnh gốc là RGBA/PNG)
    if pil_image.mode in ("RGBA", "P"):
        pil_image = pil_image.convert("RGB")

    # 3. Lưu vào RAM dưới dạng JPEG Quality 95
    # subsampling=0: QUAN TRỌNG, giúp chữ màu đỏ trên nền đen không bị nhòe
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=95, subsampling=0)
    
    # 4. Encode Base64
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# === 3. HÀM LOGIC AI ===
# @ai.flow() <--- Bỏ decorator Genkit
async def analyze_menu_flow(input_data: MenuInput) -> MenuResult:
    try:
        # Lấy dữ liệu từ input object
        img_str = input_data.image_base64
        day_str = input_data.day_str
        
        # Decode base64 thành PIL Image để gửi cho Gemini SDK
        image = Image.open(io.BytesIO(base64.b64decode(img_str)))

        aliases_map = {
            "THỨ 2": "Thứ Hai, T2, Mon",
            "THỨ 3": "Thứ Ba, T3, Tue",
            "THỨ 4": "Thứ Tư, T4, Wed",
            "THỨ 5": "Thứ Năm, T5, Thu",
            "THỨ 6": "Thứ Sáu, T6, Fri",
            "THỨ 7": "Thứ 7, Thứ Bảy, T7, Sat, Saturday, Cuối tuần", 
            "CN": "Chủ Nhật, Sun"
        }
        current_aliases = aliases_map.get(day_str, day_str)

        prompt_text = f"""
Bạn là chuyên gia đọc thực đơn. Đây là thực đơn tuần có nhiều ngày.

Nhiệm vụ: Tìm món ăn cho ngày {day_str}

Các tên gọi khác có thể là: {current_aliases}

Hướng dẫn:
- Đọc kỹ toàn bộ ảnh, tìm chữ {day_str} ở bất kỳ vị trí nào
- Lấy danh sách món ăn bên dưới hoặc kế bên ngày đó
- Nếu không tìm thấy, trả về has_requested_day = false

Trả về JSON với cấu trúc:
{{
  "is_menu": bool,
  "has_requested_day": bool,
  "reason": "text",
  "dishes": ["mon1", "mon2"]
}}
        """
        
        # Gọi Gemini SDK trực tiếp
        response = model.generate_content(
            [prompt_text, image],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        # Parse kết quả JSON
        try:
            result_json = json.loads(response.text)
            return MenuResult(**result_json)
        except Exception as parse_error:
            return {"is_menu": False, "has_requested_day": False, "dishes": [], "reason": f"Lỗi parse JSON: {parse_error}"}

    except Exception as e:
        print(f"Lỗi GenAI: {e}")
        return {"is_menu": False, "has_requested_day": False, "dishes": [], "reason": str(e)}

# === CÁC HÀM TIỆN ÍCH ===
def get_today_vietnamese():
    weekday = datetime.datetime.now().weekday()
    days = {0: "THỨ 2", 1: "THỨ 3", 2: "THỨ 4", 3: "THỨ 5", 4: "THỨ 6", 5: "THỨ 7", 6: "CN"}
    return days.get(weekday, "CN")

def run_genkit_sync(image_bytes, day_str):
    try:
        print(f"--- [Genkit] Đang gửi dữ liệu (Optimized)...")
        # Xử lý ảnh trước khi vào flow để tránh lỗi JSON serialization
        img = Image.open(io.BytesIO(image_bytes))
        img_base64 = optimize_image_for_ai(img)
        input_payload = MenuInput(image_base64=img_base64, day_str=day_str)
        result = asyncio.run(analyze_menu_flow(input_payload))
        
        # [FIX] Xử lý kết quả trả về từ Pydantic Model (hoặc dict nếu lỗi)
        if isinstance(result, MenuResult):
            # Ưu tiên dùng model_dump (Pydantic v2) hoặc dict (v1)
            if hasattr(result, 'model_dump'):
                data = result.model_dump()
            elif hasattr(result, 'dict'):
                data = result.dict()
            else:
                data = result.__dict__
        else:
            data = result # Trường hợp là dict lỗi

        reason = data.get('reason', 'Không có lý do')
        print(f"🧐 [AI]: {reason}")

        if not data.get('is_menu') or not data.get('has_requested_day'):
            return []
            
        dishes = data.get('dishes', [])
        print(f"✅ [AI] Món: {dishes}")
        return dishes
    except Exception as e:
        print(f"Lỗi Wrapper: {e}")
        return []


class MenuPopup:
    def __init__(self, day_str):
        self.day_str = day_str
        self.selected_dish = None
        self.image_bytes = None # Lưu bytes thay vì path
        self.root = tk.Tk()
        self.root.title(f"Genkit Speed - {day_str}")
        self.root.attributes("-topmost", True)
        
        # UI căn giữa
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = int((sw - 400) / 2)
        y = int((sh - 500) / 2)
        self.root.geometry(f"400x500+{x}+{y}")
        
        self.lbl_status = tk.Label(self.root, text="🚀 Đang khởi tạo...", fg="blue", font=("Arial", 12, "bold"))
        self.lbl_status.pack(pady=20)
        self.lbl_progress = tk.Label(self.root, text="0%", fg="gray", font=("Arial", 10))
        self.lbl_progress.pack(pady=5)
        self.listbox = tk.Listbox(self.root, font=("Arial", 11))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10)
        self.btn = tk.Button(self.root, text="CHỐT MÓN NÀY", command=self.confirm, state=tk.DISABLED, bg="green", fg="white")
        self.btn.pack(pady=10, fill=tk.X)
        self.auto_close_job = None

    def update_download_progress(self, percent, size_mb):
        self.lbl_status.config(text=f"⬇️ Đang tải RAM...", fg="orange")
        self.lbl_progress.config(text=f"{percent:.1f}% ({size_mb:.2f} MB)")
        self.root.update()

    def start_analysis(self, image_bytes):
        self.image_bytes = image_bytes
        self.lbl_status.config(text="🤖 Genkit đang đọc menu...", fg="blue")
        self.lbl_progress.config(text="") 
        self.auto_close_job = self.root.after(60000, self.root.destroy)
        threading.Thread(target=self.run_ai, daemon=True).start()
        self.root.mainloop()

    def run_ai(self):
        dishes = run_genkit_sync(self.image_bytes, self.day_str)
        self.root.after(0, self.update_list, dishes)

    def update_list(self, dishes):
        if not dishes:
            self.lbl_status.config(text="❌ Không đọc được!", fg="red")
            self.root.after(2000, self.root.destroy)
            return
        self.lbl_status.config(text=f"✅ Menu {self.day_str}", fg="black")
        self.listbox.delete(0, tk.END)
        for d in dishes: self.listbox.insert(tk.END, d)
        self.btn.config(state=tk.NORMAL)
        if self.listbox.size() > 0: self.listbox.selection_set(0)
        self.root.focus_force()

    def confirm(self):
        if self.listbox.curselection():
            self.selected_dish = self.listbox.get(self.listbox.curselection())
            self.root.destroy()

# ================= USERBOT LOGIC =================
session_path = get_path('my_userbot')
client = TelegramClient(session_path, API_ID, API_HASH, connection_retries=None)

@client.on(events.NewMessage(chats=GROUP_ID))
async def main_handler(event):
    is_menu = False
    if event.photo: is_menu = True
    elif event.document and event.file.mime_type and event.file.mime_type.startswith('image/'): is_menu = True
    if not is_menu: return

    today = get_today_vietnamese()
    if today == "CN": return

    print(f"\n>> Phát hiện ảnh! Khởi động Popup...")
    
    # [TỐI ƯU] Tải ảnh vào RAM (io.BytesIO) thay vì ổ cứng
    memory_file = io.BytesIO()
    
    popup = MenuPopup(today)
    
    def progress_callback(current, total):
        percent = (current / total) * 100
        size_mb = current / (1024 * 1024)
        popup.update_download_progress(percent, size_mb)
        print(f"\r>> Tải: {percent:.1f}%", end="")

    try:
        # Tải thẳng vào biến memory_file
        await event.download_media(file=memory_file, progress_callback=progress_callback)
        memory_file.seek(0) # Đưa con trỏ về đầu file để đọc
        
        print("\n>> Tải xong. Chuyển sang đọc AI...")
        popup.start_analysis(memory_file.getvalue()) # Truyền bytes vào
        
        if popup.selected_dish:
            print(f">> Chốt: {popup.selected_dish}")
            await event.reply(f"{popup.selected_dish}")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        try: popup.root.destroy()
        except: pass
    finally:
        memory_file.close()

async def login_with_gui():
    # Kết nối tới server Telegram
    await client.connect()
    
    # Kiểm tra xem đã đăng nhập chưa (dựa vào file .session)
    if not await client.is_user_authorized():
        # 1. Yêu cầu nhập số điện thoại qua GUI
        phone = simpledialog.askstring("Đăng nhập Telegram", "Nhập số điện thoại (VD: +84912345678):")
        if not phone:
            sys.exit()
            
        # Gửi mã OTP
        sent_code = await client.send_code_request(phone)
        
        # 2. Yêu cầu nhập mã OTP qua GUI
        code = simpledialog.askstring("Đăng nhập Telegram", "Nhập mã OTP gửi về Telegram của bạn:")
        
        try:
            # Thực hiện đăng nhập
            await client.sign_in(phone, code)
        except Exception as e:
            # Nếu có lỗi (sai mã, hoặc cần mật khẩu 2 lớp)
            if "password" in str(e).lower():
                pwd = simpledialog.askstring("Bảo mật 2 lớp", "Nhập mật khẩu Cloud Password của bạn:", show='*')
                await client.sign_in(password=pwd)
            else:
                messagebox.showerror("Lỗi", f"Đăng nhập thất bại: {e}")
                sys.exit()

    print(f"--- BOT GENKIT ĐANG CHẠY TẠI: {BASE_DIR} ---")
    messagebox.showinfo("Thành công", "Bot đã kết nối thành công!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(login_with_gui())