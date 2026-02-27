╔══════════════════════════════════════════════════════════════════╗
║           HƯỚNG DẪN SỬ DỤNG BOT ĐẶT CƠM TỰ ĐỘNG v1.0           ║
╚══════════════════════════════════════════════════════════════════╝

📌 MÔ TẢ
---------
Bot tự động đọc thực đơn từ ảnh được gửi trong nhóm Telegram và giúp bạn
đặt món nhanh chóng bằng giao diện đơn giản.

💡 YÊU CẦU HỆ THỐNG
-------------------
✓ Windows 10/11 (64-bit)
✓ Kết nối Internet ổn định
✓ Tài khoản Telegram hoạt động

🚀 CÀI ĐẶT & KHỞI ĐỘNG LẦN ĐẦU
--------------------------------

BƯỚC 1: Lấy API Credentials từ Telegram
----------------------------------------
1. Truy cập: https://my.telegram.org
2. Đăng nhập bằng SĐT Telegram của bạn
3. Vào phần "API Development Tools"
4. Tạo ứng dụng mới (nếu chưa có):
   - App title: "Bot Đặt Cơm" (hoặc tên tùy ý)
   - Short name: "botdatcom" (hoặc tên tùy ý)
   - Platform: Desktop
5. SAO CHÉP 2 thông tin sau:
   ✦ api_id (dạng số, VD: 12345678)
   ✦ api_hash (chuỗi ký tự dài, VD: a1b2c3d4e5f6g7h8i9j0...)

BƯỚC 2: Lấy Gemini API Key
---------------------------
1. Truy cập: https://aistudio.google.com/apikey
2. Đăng nhập bằng tài khoản Google
3. Nhấn "Get API Key" hoặc "Create API Key"
4. SAO CHÉP API Key (VD: AIzaSyA...)

BƯỚC 3: Lấy ID của nhóm Telegram
---------------------------------
Có 2 cách:

🔹 Cách 1: Dùng Bot @userinfobot
   - Mở nhóm cần lấy ID
   - Forward 1 tin nhắn BẤT KỲ từ nhóm đó cho @userinfobot
   - Bot sẽ trả về thông tin, trong đó có "Chat ID" (VD: -1001234567890)

🔹 Cách 2: Dùng Bot @Rose
   - Thêm @MissRose_bot vào nhóm
   - Gõ lệnh: /id
   - Bot sẽ trả về ID nhóm

📝 LƯU Ý: ID nhóm luôn có dấu trừ (-) ở đầu!

BƯỚC 4: Cấu hình Bot
--------------------
1. Chạy file BotDatCom_v1.0.exe LẦN ĐẦU TIÊN
   → Bot sẽ tự tạo file "config.json" và mở ra

2. Điền thông tin vào file config.json:
   
   {
     "api_id": 12345678,                        ← Thay bằng API ID của bạn (SỐ, KHÔNG có dấu ngoặc)
     "api_hash": "a1b2c3d4e5f6g7h8i9j0",       ← Thay bằng API Hash của bạn
     "gemini_api_key": "AIzaSyA...",           ← Thay bằng Gemini Key của bạn
     "target_group_ids": [-1001234567890],     ← Thay bằng ID nhóm của bạn (có dấu -)
     "auto_shutdown_hour": 13                  ← Giờ tự động tắt (mặc định 13:00)
   }

3. LƯU FILE (Ctrl+S) và ĐÓNG LẠI

BƯỚC 5: Đăng nhập Telegram
---------------------------
1. Chạy lại file BotDatCom_v1.0.exe
2. Cửa sổ đăng nhập sẽ hiện ra:
   - Nhập SĐT Telegram (VD: +84912345678)
   - Nhấn OK
3. Nhập mã OTP được gửi về Telegram của bạn
4. (Nếu có) Nhập mật khẩu Cloud Password (bảo mật 2 lớp)
5. Một thông báo "Bot đã kết nối thành công!" sẽ hiện ra
6. Bot đã sẵn sàng!

📋 CÁCH SỬ DỤNG HÀNG NGÀY
--------------------------

1. ✅ BẬT BOT: Double-click vào file BotDatCom_v1.0.exe
   • Bot sẽ tự động kết nối (không cần đăng nhập lại)
   • Cửa sổ console (màn hình đen) sẽ hiện ra - KHÔNG ĐÓNG nó

2. 🍱 KHI CÓ ẢNH MENU:
   • Khi có ai đó gửi ảnh menu vào nhóm
   • Bot sẽ TỰ ĐỘNG:
     - Kiểm tra xem đó có phải ảnh menu không
     - Đọc món ăn của hôm nay
     - Hiện popup với danh sách món
   
3. 🖱️ CHỌN MÓN:
   • Nhấn chọn món muốn ăn trong danh sách
   • (Tùy chọn) Đánh dấu "Ít cơm" nếu muốn
   • Nhấn nút "CHỐT MÓN NÀY"
   • Bot sẽ TỰ ĐỘNG reply vào nhóm

4. ⏰ TỰ ĐỘNG TẮT:
   • Bot sẽ tự tắt vào 13:00 (hoặc giờ bạn đã cài đặt)
   • Để tiết kiệm RAM máy tính

⚠️ LƯU Ý QUAN TRỌNG
--------------------
❌ KHÔNG chia sẻ file config.json cho người khác (chứa API riêng tư)
❌ KHÔNG xóa file .session (chứa thông tin đăng nhập)
✅ Nếu đổi máy: Copy CẢ 2 FILE (BotDatCom_v1.0.exe + config.json)
✅ Nếu bị lỗi: Xóa file .session và đăng nhập lại

🐛 KHẮC PHỤC SỰ CỐ
-------------------

❓ Lỗi: "File config.json chưa được điền đầy đủ"
   → Mở file config.json, kiểm tra lại các giá trị
   → Đảm bảo không còn chữ "NHAP_..." nào

❓ Lỗi: "cannot find symbol" / JSON decode error
   → File config.json bị sai cú pháp
   → Kiểm tra: dấu phẩy, ngoặc, dấu ngoặc kép

❓ Lỗi: "Phone number invalid"
   → Nhập SĐT đầy đủ với mã quốc gia: +84...

❓ Bot không phản hồi khi có ảnh menu
   → Kiểm tra target_group_ids có đúng không
   → Thử gửi ảnh menu MẪU để kiểm tra

❓ Popup không hiện món
   → Ảnh có thể không rõ hoặc không đúng định dạng menu tuần
   → Thử chụp lại ảnh rõ hơn

📞 HỖ TRỢ
----------
Nếu gặp vấn đề không giải quyết được, hãy:
1. Chụp ảnh màn hình console (màn hình đen) khi có lỗi
2. Chụp ảnh nội dung file config.json (che API keys)
3. Liên hệ người phát triển để được hỗ trợ

═══════════════════════════════════════════════════════════════════
                           Phiên bản 1.0
═══════════════════════════════════════════════════════════════════
