import os
import sys
import asyncio
import datetime
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
# ================= CẤU HÌNH =================
# Điền Token và API Key của bạn vào đây
TELEGRAM_TOKEN = "8498324006:AAGxhhGdeHJiZxAmJjPdkO4IAR3UNVhiudc"
GEMINI_API_KEY = "AIzaSyCbZItAr37w9o8qy6rHOhnWIbypStY015E"
GROUP_ID = -5162755092 

# Cấu hình Client AI theo chuẩn mới (google-genai)
client = genai.Client(api_key=GEMINI_API_KEY)
# print("--- ĐANG KIỂM TRA CÁC MODEL KHẢ DỤNG ---")
# try:
#     # Lấy danh sách model
#     for m in client.models.list():
#         # Chỉ in ra tên model để bạn copy
#         print(f"✅ ID: {m.name}")
#         # print(f"   Tên: {m.display_name}") # Bỏ comment nếu muốn xem tên đầy đủ
#         print("-" * 20)
        
# except Exception as e:
#     print(f"❌ Lỗi: {e}")

# ================= HÀM XỬ LÝ LOGIC =================

def get_today_vietnamese():
    weekday = datetime.datetime.now().weekday()
    days = {0: "THỨ 2", 1: "THỨ 3", 2: "THỨ 4", 3: "THỨ 5", 4: "THỨ 6", 5: "THỨ 7", 6: "CN"}
    return days.get(weekday, "CN")

def analyze_menu_with_ai(image_path, day_str):
    print(f"--- Đang gửi ảnh sang AI để đọc menu ngày {day_str}...")
    
    # SỬA 1: Prompt "gắt" hơn, chỉ rõ vị trí
    # Prompt mới: KẾT HỢP KIỂM TRA + TRÍCH XUẤT + LÀM SẠCH
    prompt = f"""
    Bạn là một trợ lý kiểm duyệt và trích xuất thực đơn.
    
    Nhiệm vụ 1: KIỂM TRA ẢNH (Quan trọng nhất)
    - Hãy nhìn kỹ bức ảnh. Đây có phải là ảnh chụp "Thực đơn ăn uống" (Menu) có danh sách món ăn và ngày tháng không?
    - Nếu đây là ảnh người, phong cảnh, màn hình máy tính, tài liệu văn bản không phải menu, hoặc ảnh linh tinh -> Hãy trả về ĐÚNG 1 CỤM TỪ duy nhất: "KHONG_PHAI_MENU" và dừng lại ngay.

    Nhiệm vụ 2: TRÍCH XUẤT (Chỉ thực hiện nếu Nhiệm vụ 1 đã qua)
    - Tìm khu vực danh sách món ăn của ngày: "{day_str}".
    - Nếu không tìm thấy ngày "{day_str}" trong menu -> Trả về: "KHONG_THAY_NGAY".
    
    Nhiệm vụ 3: ĐỊNH DẠNG (Nếu tìm thấy món)
    - Trích xuất tên món ăn, mỗi món một dòng.
    - TUYỆT ĐỐI LOẠI BỎ các thành phần sau:
      + Số thứ tự (1, 2, 3... hoặc 1), 2)...).
      + Tiêu đề ngày (Không chép lại chữ "{day_str}").
      + Giá tiền (nếu có).
      + Dấu gạch đầu dòng, dấu sao markdown.
    - Không được tự bịa ra món ăn nếu chữ quá mờ.
    """
            prompt_text = f"""
        Bạn là một API đọc thực đơn thông minh.
        
        NHIỆM VỤ:
        Hãy phân tích hình ảnh và trích xuất món ăn cho ngày mục tiêu: "{day_str}".
        
        HƯỚNG DẪN XỬ LÝ:
        1. is_menu: 
           - Đặt là True nếu ảnh chứa danh sách món ăn (Menu).
           - Đặt là False nếu là ảnh người, phong cảnh, selfie...
           
        2. has_requested_day:
           - Tìm kiếm ngày "{day_str}" trong ảnh.
           - Hãy linh hoạt, tìm cả các từ khóa tương đương: {current_aliases}.
           - Chú ý: Thực đơn thường chia theo ô, hãy nhìn kỹ cả các góc ảnh.
           - Nếu tìm thấy ngày này -> Đặt True. Ngược lại -> False.
           
        3. dishes:
           - Nếu has_requested_day là True, hãy liệt kê các món ăn bên dưới ngày đó.
           - QUY TẮC LỌC MÓN:
             + Chỉ lấy tên món ăn tiếng Việt.
             + LOẠI BỎ số thứ tự đầu dòng (ví dụ: "1)", "2.", "3").
             + LOẠI BỎ giá tiền.
             + Mỗi món là một chuỗi trong danh sách.
        """
    try:
        img = Image.open(image_path)
        
        # SỬA 2: Đổi về 'gemini-1.5-flash' để đọc cột chính xác hơn
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-09-2025", 
            contents=[prompt, img]
        )
        
        text_result = response.text.strip()
        print(f"[AI Trả lời]:\n{text_result}\n----------------")

        if "KHONG_THAY_NGAY" in text_result or "KHONG_PHAI_MENU" in text_result: return []
        
       # Làm sạch dữ liệu
        import re
        dishes = []
        for line in text_result.split('\n'):
            line = line.strip()
            if not line or line.upper() == day_str.upper(): continue
            clean_line = re.sub(r'^[\d\-\*\+\.]+\s*[\)\.]?\s*', '', line)
            if len(clean_line) > 2: dishes.append(clean_line)
            
        return dishes

    except Exception as e:
        print(f"Lỗi AI: {e}")
        return []

class MenuPopup:
    def __init__(self, image_path, day_str):
        self.image_path = image_path
        self.day_str = day_str
        self.selected_dish = None
        
        # Tạo cửa sổ chính
        self.root = tk.Tk()
        self.root.title(f"Bot Đặt Cơm - {day_str}")
        
        # Cấu hình cửa sổ: Luôn nổi, không viền (nếu thích), kích thước
        self.root.attributes("-topmost", True)
        self.root.geometry("400x500")
        
        # Căn giữa màn hình
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width - 400) / 2)
        y = int((screen_height - 500) / 2)
        self.root.geometry(f"400x500+{x}+{y}")
        
        # Label trạng thái
        self.lbl_status = tk.Label(self.root, text="⏳ Đang đọc menu từ AI...", font=("Arial", 12, "bold"), fg="blue")
        self.lbl_status.pack(pady=20)
        
        # Listbox chứa món ăn (Ban đầu ẩn đi hoặc rỗng)
        self.listbox = tk.Listbox(self.root, font=("Arial", 11), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Nút chọn (Ban đầu Disable)
        self.btn_select = tk.Button(self.root, text="CHỌN MÓN NÀY", command=self.confirm_selection, state=tk.DISABLED, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_select.pack(pady=10, fill=tk.X, padx=20)
        
        # Chạy luồng xử lý AI riêng để không treo giao diện
        threading.Thread(target=self.process_ai, daemon=True).start()
        
        # Bắt đầu vòng lặp giao diện
        self.root.focus_force() # Ép lấy focus
        self.root.mainloop()

    def process_ai(self):
        """Chạy ngầm việc gọi AI"""
        dishes = analyze_menu_with_ai(self.image_path, self.day_str)
        
        # Cập nhật giao diện từ luồng phụ (cần dùng after hoặc gọi trực tiếp trong tk đơn giản)
        # Trong Tkinter đơn giản, ta có thể gọi hàm cập nhật
        self.root.after(0, self.update_ui_with_dishes, dishes)

    def update_ui_with_dishes(self, dishes):
        """Hiển thị danh sách món sau khi AI trả về"""
        self.listbox.delete(0, tk.END)
        
        if not dishes:
            self.lbl_status.config(text="❌ Không tìm thấy món nào!", fg="red")
            messagebox.showerror("Lỗi", "AI không đọc được menu hoặc không phải menu.")
            self.root.destroy()
            return
            
        self.lbl_status.config(text=f"✅ Tìm thấy {len(dishes)} món ({self.day_str})", fg="green")
        
        for idx, dish in enumerate(dishes):
            self.listbox.insert(tk.END, f"{idx+1}. {dish}")
            
        self.btn_select.config(state=tk.NORMAL)
        # Tự động chọn món đầu tiên
        self.listbox.selection_set(0)
        self.listbox.focus_set()

    def confirm_selection(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            raw_text = self.listbox.get(index)
            # Cắt bỏ số thứ tự "1. " ở đầu
            self.selected_dish = raw_text.split(". ", 1)[-1]
            self.root.destroy()
        else:
            messagebox.showwarning("Chưa chọn", "Vui lòng bấm vào một món ăn!")

def show_popup_loading(image_path, day_str):
    """Hàm wrapper để gọi class Popup"""
    popup = MenuPopup(image_path, day_str)
    return popup.selected_dish
# ================= TÍNH NĂNG TỰ TẮT =================

# async def check_time_shutdown(context: ContextTypes.DEFAULT_TYPE):
#     now = datetime.datetime.now()
#     if now.hour >= 13: 
#         print(f"Quá 13h rồi ({now.strftime('%H:%M')}). Tắt bot để tiết kiệm tài nguyên!")
#         os._exit(0)

# ================= BOT TELEGRAM =================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Kiểm tra ID nhóm (quan trọng)
    chat_id = update.effective_chat.id
    print(f"\n[DEBUG] Nhận tin nhắn từ ID: {chat_id}") 
    
    if GROUP_ID == 0:
        print(f"⚠️ Chưa cấu hình GROUP_ID. ID hiện tại là: {chat_id}")
        return
    
    if chat_id != GROUP_ID:
        print(f"Bỏ qua tin nhắn từ nơi khác (Không phải Group Công Ty)")
        return

    # 2. Kiểm tra thời gian (CN nghỉ)
    today_str = get_today_vietnamese()  
    if today_str == "CN": return

    # 3. Lấy file ảnh (Xử lý cả trường hợp Ảnh nén và File ảnh)
    message = update.message
    file_id = None

    if message.photo: file_id = message.photo[-1].file_id
    elif message.document and 'image' in message.document.mime_type: file_id = message.document.file_id
    else: return

    print(f"\n>> Nhận ảnh từ {chat_id}. Đang tải...")
    # 4. Tải và Xử lý
    try:
        new_file = await context.bot.get_file(file_id)
        image_path = "menu_temp.jpg"
        await new_file.download_to_drive(image_path)
        
        print(">> Đang bật Popup trên màn hình...")
        # Gọi AI phân tích
        dishes = analyze_menu_with_ai(image_path, today_str)
        
        chosen_dish = show_popup_loading(image_path, today_str)
        
        if chosen_dish:
            print(f">> Đã chọn: {chosen_dish}")
            await context.bot.send_message(
                chat_id=chat_id, 
                text=f"Dev Java chọn món: {chosen_dish}",
                reply_to_message_id=message.id
            )
        else:
            print(">> Người dùng đã hủy hoặc tắt Popup.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    if os.path.exists(image_path): os.remove(image_path)

if __name__ == '__main__':
    print("Bot đang chạy...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    app.run_polling()