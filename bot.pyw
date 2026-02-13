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

from collections import OrderedDict
import hashlib
import time
import json

# [PATCH FIX] VÁ LỖI GENKIT ALPHA

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

# === Cấu hình đường dẫn ===

if getattr(sys, 'frozen', False):
    # Nếu đang chạy bằng file EXE, lấy đường dẫn của file EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Nếu đang chạy bằng file .py, lấy đường dẫn của file code
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename):
    return os.path.join(BASE_DIR, filename)

# === Load/Create config.json ===
def load_config():

    config_path = get_path('config.json')
    
    # Template mặc định
    default_config = {
        "api_id": "NHAP_API_ID_TELEGRAM",
        "api_hash": "NHAP_API_HASH_TELEGRAM",
        "gemini_api_key": "NHAP_KEY_GOOGLE_AI",
        "target_group_ids": [-123456789, -987654321],
        "auto_shutdown_hour": 13
    }
    
    # Nếu file chưa tồn tại, tạo file mẫu
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Lần đầu chạy Bot",
                f"File config.json đã được tạo tại:\n{config_path}\n\n"
                "Vui lòng mở file và điền đầy đủ thông tin API, sau đó chạy lại bot."
            )
            # Mở file config cho người dùng
            try:
                os.startfile(config_path)
            except:
                pass
            sys.exit(0)
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("LỖI", f"Không thể tạo file config:\n{e}")
            sys.exit(1)
    
    # Đọc file config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate: kiểm tra xem người dùng đã điền thông tin chưa
        api_id = config.get('api_id', '')
        api_hash = config.get('api_hash', '')
        gemini_key = config.get('gemini_api_key', '')
        
        if (str(api_id).startswith('NHAP_') or 
            str(api_hash).startswith('NHAP_') or 
            str(gemini_key).startswith('NHAP_')):
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Thiếu cấu hình",
                f"File config.json chưa được điền đầy đủ!\n\n"
                f"Vui lòng mở file tại:\n{config_path}\n\n"
                "và thay thế các giá trị 'NHAP_...' bằng API thật."
            )
            # Mở file config
            try:
                os.startfile(config_path)
            except:
                pass
            sys.exit(1)
        
        # Parse API_ID sang int
        try:
            config['api_id'] = int(api_id)
        except:
            raise ValueError(f"api_id phải là số nguyên, nhận được: {api_id}")
        
        return config
        
    except json.JSONDecodeError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Lỗi định dạng JSON",
            f"File config.json có lỗi cú pháp:\n{e}\n\nVui lòng kiểm tra lại định dạng."
        )
        sys.exit(1)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("LỖI", f"Không thể đọc config:\n{e}")
        sys.exit(1)

# Load config ngay khi khởi động
config = load_config()
API_ID = config['api_id']
API_HASH = config['api_hash']
GEMINI_API_KEY = config['gemini_api_key']
GROUP_ID = config.get('target_group_ids', [])
AUTO_SHUTDOWN_HOUR = config.get('auto_shutdown_hour', 13)

# === CACHE THÔNG MINH CHO MENU CÔNG TY ===
CACHE_FILE = get_path('menu_cache.json')
MAX_CACHE_SIZE = 20
CACHE_TTL = 604800  # 7 ngày

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

def load_cache():
    if not os.path.exists(CACHE_FILE):
        print(f"📂 [Cache] File chưa tồn tại, tạo file mới: {CACHE_FILE}")
        # Tạo file JSON rỗng
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return OrderedDict()
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        current__time = time.time()
        valid_cache = OrderedDict()
        expired_count = 0

        for img_hash, (is_menu, cached_time) in cache_data.items():
            age = current__time - cached_time
            if age < CACHE_TTL:
                valid_cache[img_hash] = (is_menu, cached_time)
            else:
                expired_count += 1
        
        if expired_count > 0:
            print(f"--- [Cache] Đã xóa {expired_count} mục hết hạn.")
        
        print(f"--- [Cache] Tải {len(valid_cache)} mục hợp lệ từ cache.")
        if expired_count > 0:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(dict(valid_cache), f, ensure_ascii=False, indent=2)
        
        return valid_cache
    except FileNotFoundError:
        print(f"--- [Cache] Không tìm thấy file cache. Tạo mới.")
        return OrderedDict()
    except Exception as e:
        print(f"--- [Cache] Lỗi khi tải cache: {e}")
        return OrderedDict()
    
menu_cache = load_cache()

def save_cache():
    """Lưu cache vào file JSON"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(dict(menu_cache), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ [Cache] Lỗi ghi file: {e}")

def validate_is_menu_image(image_bytes):
    """
    Kiểm tra nhanh xem ảnh có phải là thực đơn món ăn không.
    Trả về True nếu là menu, False nếu không phải.

    Cải tiến:
    - Tạo "normalized" JPEG bytes (loại metadata, convert RGB, fixed quality) để hash ổn định
    - Thêm logging thời gian để biết đâu tốn thời gian (cache vs AI)
    """
    start_time = time.perf_counter()
    try:
        # Tạo bản normalized để đảm bảo hash ổn định dù image metadata thay đổi
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            norm_buf = io.BytesIO()
            # Lưu với quality cố định, không giữ metadata
            img.save(norm_buf, format='JPEG', quality=90, optimize=True)
            norm_bytes = norm_buf.getvalue()
            img_hash = hashlib.md5(norm_bytes).hexdigest()
            size_kb = len(norm_bytes) / 1024
            w, h = img.size
        except Exception:
            # Fallback: hash raw bytes
            img_hash = hashlib.md5(image_bytes).hexdigest()
            size_kb = len(image_bytes) / 1024
            w, h = (None, None)

        # Cache check
        if img_hash in menu_cache:
            is_menu, cached_time = menu_cache[img_hash]
            age = time.time() - cached_time
            if age < CACHE_TTL:
                menu_cache.move_to_end(img_hash)  # Cập nhật LRU
                day_left = int((CACHE_TTL - age) / 86400)
                hours_ago = int(age / 3600)
                elapsed = (time.perf_counter() - start_time)
                print(f"💾 [Cache HIT] hash={img_hash} size={size_kb:.1f}KB {w}x{h} age={hours_ago}h left={day_left}d (checked in {elapsed:.2f}s)")
                return is_menu
            else:
                print(f"💾 [Cache EXPIRED] hash={img_hash}, kiểm tra lại với AI.")
                del menu_cache[img_hash]
                save_cache()

        print(f"--- [Validation] Đang kiểm tra ảnh... (hash={img_hash}, size={size_kb:.1f}KB, {w}x{h})")

        # Dùng optimized image cho lần gọi AI để giảm payload và thời gian
        img_for_ai = Image.open(io.BytesIO(image_bytes))
        img_base64 = optimize_image_for_ai(img_for_ai)

        # Prompt đơn giản chỉ để phân loại
        prompt_text = """
Bạn là chuyên gia phân loại ảnh. Hãy xác định ảnh này có phải là THỰC ĐƠN MÓN ĂN không.

Thực đơn món ăn thường có:
- Danh sách các món ăn (cơm, phở, bún, canh, v.v.)
- Các ngày trong tuần (Thứ 2, Thứ 3, ...)
- Tên quán ăn hoặc căng tin
- Giá tiền món ăn

KHÔNG PHẢI thực đơn nếu là:
- Tài liệu văn bản thông thường
- Ảnh chụp màn hình
- Biểu đồ, báo cáo
- Ảnh cá nhân, phong cảnh
- Meme, poster quảng cáo

Trả về JSON:
{
  "is_menu": true/false,
  "reason": "Giải thích ngắn gọn"
}
        """

        ai_start = time.perf_counter()
        response = model.generate_content(
            [prompt_text, img_for_ai],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        ai_elapsed = time.perf_counter() - ai_start

        result = json.loads(response.text)
        is_menu = result.get('is_menu', False)
        reason = result.get('reason', 'Không rõ')

        elapsed = time.perf_counter() - start_time
        print(f"🔍 [Validation]: {reason} (AI took {ai_elapsed:.2f}s, total {elapsed:.2f}s)")
        print(f"📋 Kết quả: {'✅ Là menu' if is_menu else '❌ Không phải menu'}")

        # Lưu vào cache dùng hash normalized
        menu_cache[img_hash] = (is_menu, time.time())
        menu_cache.move_to_end(img_hash)

        # 🗑️ Xóa ảnh cũ nhất nếu cache đầy
        if len(menu_cache) > MAX_CACHE_SIZE:
            oldest_hash, oldest_data = menu_cache.popitem(last=False)
            days_ago = int((time.time() - oldest_data[1]) / 86400)
            print(f"🗑️ [Cache FULL] Đã xóa ảnh cũ nhất (check {days_ago} ngày trước)")

        # 💾 LƯU VÀO FILE
        save_cache()

        print(f"💾 [Cache SAVED] Tổng: {len(menu_cache)} ảnh | TTL: 7 ngày")

        return is_menu

    except Exception as e:
        print(f"⚠️ Lỗi validation: {e}")
        # Nếu lỗi, cho qua để không làm gián đoạn bot
        return True

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

        # Checkbox để chọn 'Ít cơm' (mặc định vô hiệu, chỉ bật khi có món được load)
        self.less_rice_var = tk.BooleanVar(value=False)
        self.chk_less_rice = tk.Checkbutton(self.root, text="Ít cơm", variable=self.less_rice_var, state=tk.DISABLED)
        self.chk_less_rice.pack(pady=6)

        # Cho phép double-click để chốt nhanh
        self.listbox.bind("<Double-Button-1>", lambda e: self.confirm())

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
            # Đảm bảo checkbox bị vô hiệu nếu không có món
            try:
                self.chk_less_rice.config(state=tk.DISABLED)
                self.less_rice_var.set(False)
            except Exception:
                pass
            self.root.after(2000, self.root.destroy)
            return
        self.lbl_status.config(text=f"✅ Menu {self.day_str}", fg="black")
        self.listbox.delete(0, tk.END)
        for d in dishes: self.listbox.insert(tk.END, d)
        # Bật nút chốt và checkbox
        self.btn.config(state=tk.NORMAL)
        try:
            self.chk_less_rice.config(state=tk.NORMAL)
            # Mặc định không chọn 'Ít cơm'
            self.less_rice_var.set(False)
        except Exception:
            pass
        if self.listbox.size() > 0: self.listbox.selection_set(0)
        self.root.focus_force()

    def confirm(self):
        if self.listbox.curselection():
            self.selected_dish = self.listbox.get(self.listbox.curselection())
            # Lưu giá trị checkbox TRƯỚC KHI destroy window để tránh lỗi
            try:
                is_less_rice = self.less_rice_var.get()
            except Exception:
                is_less_rice = False
            
            # Nếu người dùng muốn ăn ít cơm, thêm chú thích
            if is_less_rice:
                self.selected_dish = f"{self.selected_dish} (ít cơm)"
            
            self.root.destroy()

# ================= USERBOT LOGIC =================
session_path = get_path('my_userbot')
client = TelegramClient(session_path, API_ID, API_HASH, connection_retries=None)

@client.on(events.NewMessage())
async def main_handler(event):
    # Kiểm tra xem tin nhắn có từ nhóm được chỉ định không
    if event.chat_id not in GROUP_ID:
        return  # Bỏ qua nếu không phải nhóm mục tiêu
    
    is_menu = False
    if event.photo: is_menu = True
    elif event.document and event.file.mime_type and event.file.mime_type.startswith('image/'): is_menu = True
    if not is_menu: return

    today = get_today_vietnamese()
    if today == "CN": return

    print(f"\n>> Phát hiện ảnh! Đang kiểm tra...")
    
    # [TỐI ƯU] Tải ảnh vào RAM (io.BytesIO) thay vì ổ cứng
    memory_file = io.BytesIO()
    
    # Tải ảnh trước để validate
    try:
        dl_start = time.perf_counter()
        await event.download_media(file=memory_file)
        dl_elapsed = time.perf_counter() - dl_start
        print(f"⬇️ [Download] Tải ảnh xong trong {dl_elapsed:.2f}s")
        memory_file.seek(0)
        image_bytes = memory_file.getvalue()
        
        # VALIDATION: Kiểm tra có phải ảnh menu không
        if not validate_is_menu_image(image_bytes):
            print(">> ⏭️ Bỏ qua - Không phải ảnh menu")
            memory_file.close()
            return
        
        print(">> ✅ Xác nhận là menu! Khởi động GUI...")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi tải/validate ảnh: {e}")
        memory_file.close()
        return
    
    popup = MenuPopup(today)
    
    try:
        # Ảnh đã được tải và validate rồi, giờ chỉ cần phân tích món
        print("\n>> Đang đọc món ăn...")
        popup.start_analysis(image_bytes) # Truyền bytes vào
        
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

    # ⚠️ Auto-shutdown: tự động ngắt sau giờ đã đặt để tiết kiệm RAM
    async def _auto_shutdown_at_13(client, hour: int = AUTO_SHUTDOWN_HOUR, minute: int = 0):
        try:
            now = datetime.datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if now >= target:
                # Nếu đã qua giờ giới nghiêm tại thời điểm khởi động, tiếp tục chạy bình thường
                print(f"⏰ [Auto-shutdown] Đã vượt quá {hour}:00, bot sẽ tiếp tục chạy.")
                return  # Không tắt, cho phép bot hoạt động bình thường
            else:
                # Nếu chưa đến giờ, lên lịch tắt
                delta = (target - now).total_seconds()
                print(f"⏰ [Auto-shutdown] Lên lịch dừng sau {delta/60:.1f} phút (lúc {target.time()}).")
                await asyncio.sleep(delta)

                # Thử ngắt kết nối client một cách từ từ
                try:
                    await client.disconnect()
                    print("[Auto-shutdown] Đã ngắt kết nối client.")
                except Exception as e:
                    print(f"[Auto-shutdown] Lỗi khi ngắt kết nối: {e}")

                # Thông báo qua GUI (nếu có) rồi exit ngay để giải phóng RAM
                try:
                    messagebox.showinfo("Tự động tắt", f"Bot sẽ dừng hoạt động lúc {hour}:00 để tiết kiệm RAM.")
                except Exception:
                    pass

                # Dừng tiến trình ngay lập tức
                os._exit(0)
        except Exception as e:
            print(f"⚠️ [Auto-shutdown] Lỗi: {e}")

    # Tạo task nền để tự động dừng vào 13:00
    try:
        asyncio.create_task(_auto_shutdown_at_13(client))
    except Exception as e:
        print(f"⚠️ Không thể lên lịch auto-shutdown: {e}")

    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(login_with_gui())