# 🍱 EatSyncBot v1.1
> **Trợ lý đặt cơm trưa tự động qua Telegram** — Không cần nhớ, không cần gõ, chỉ cần click!

---

## 📖 Mục lục

- [Bot làm được gì?](#-bot-làm-được-gì)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt lần đầu](#-cài-đặt-lần-đầu)
- [Cách dùng hàng ngày](#-cách-dùng-hàng-ngày)
- [Khắc phục sự cố](#-khắc-phục-sự-cố)
- [Hỗ trợ](#-hỗ-trợ)

---

## 🤖 Bot làm được gì?

Mỗi khi có người gửi **ảnh thực đơn** vào nhóm Telegram, EatSyncBot sẽ:

1. 👀 **Tự động phát hiện** ảnh thực đơn ngay lập tức
2. 🧠 **Dùng AI đọc menu** và trích xuất danh sách món ăn trong ngày
3. 🖥️ **Bật bảng chọn món** ngay giữa màn hình máy tính của bạn
4. 💬 **Tự động nhắn tin** đặt món vào nhóm sau khi bạn bấm chốt

---

## 💻 Yêu cầu hệ thống

| Yêu cầu | Chi tiết |
|---|---|
| 🖥️ Hệ điều hành | Windows 10 / 11 |
| 🌐 Kết nối | Có Internet |
| 📱 Tài khoản | Telegram (số điện thoại đang dùng) |

---

## 🚀 Cài đặt lần đầu

> ⏱️ **Tổng thời gian:** khoảng 10 phút — Chỉ làm **1 lần duy nhất**

---

### Bước 1 — Lấy API Telegram

1. Truy cập **[my.telegram.org/apps](https://my.telegram.org/apps)** và đăng nhập bằng SĐT của bạn
2. Chọn mục **"API Development Tools"**
3. Nếu chưa có app, tạo mới với thông tin bất kỳ (VD: App title: `EatSyncBot`, Platform: `Desktop`)
4. Sao chép và lưu tạm 2 giá trị này vào Notepad:

```
api_id   → dạng số, VD: 12345678
api_hash → chuỗi ký tự dài, VD: a1b2c3d4e5f6...
```

---

### Bước 2 — Lấy Gemini API Key (AI đọc ảnh menu)

1. Truy cập **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**
2. Đăng nhập bằng tài khoản Gmail
3. Bấm **"Create API Key"**
4. Sao chép key (dạng `AIzaSyA...`) và lưu vào Notepad cùng bước 1

---

### Bước 3 — Lấy ID nhóm Telegram công ty

1. Mở nhóm chat cần đặt cơm trên Telegram
2. **Chuyển tiếp (Forward)** 1 tin nhắn bất kỳ từ nhóm đó cho bot **[@userinfobot](https://t.me/userinfobot)**
3. Bot sẽ trả về thông tin, tìm dòng **"Chat ID"** và sao chép lại

> ⚠️ **Lưu ý:** ID nhóm luôn có **dấu trừ (-)** ở đầu, VD: `-1001234567890`

---

### Bước 4 — Nhập thông tin vào EatSyncBot

1. **Nhấn đúp** vào file `bot.exe` để mở ứng dụng
2. Bảng cài đặt sẽ hiện ra — dán các thông tin đã chuẩn bị vào đúng ô
3. Bấm **"Lưu & Khởi động Bot"**

---

### Bước 5 — Đăng nhập Telegram

1. Nhập **số điện thoại** Telegram của bạn (có thể nhập dạng `0912345678` hoặc `+84912345678`)
2. Mở app Telegram để lấy **mã OTP** rồi nhập vào bot
3. Nếu có bật **bảo mật 2 lớp**, nhập thêm mật khẩu Cloud Password

🎉 Khi thấy thông báo **"Kết nối thành công"** — bot đã sẵn sàng hoạt động!

---

### Bước 6 — Cài đặt tự động chạy khi bật máy *(Khuyến nghị)*

1. Tìm file **`SETUP_AutoStartUp.bat`** trong cùng thư mục với `bot.exe`
2. **Nhấn đúp** vào file đó — xong trong 1 giây!
3. Từ ngày mai, mỗi khi bật máy, bot sẽ **tự động chạy ngầm** mà không cần làm gì thêm ✅

---

## 📋 Cách dùng hàng ngày

### ✅ Bật bot
- **Nếu đã làm Bước 6:** Không cần làm gì — bot tự chạy khi bật máy
- **Nếu chưa làm Bước 6:** Click đúp vào `bot.exe`, thu nhỏ cửa sổ đen xuống taskbar, **đừng tắt** nó

---

### 🍱 Khi có ảnh thực đơn trong nhóm

```
Nhóm Telegram có ảnh menu mới
         ↓
Bot tự động nhận diện & đọc món
         ↓
Bảng chọn món hiện ra giữa màn hình
         ↓
Bạn click chọn món → bấm "CHỐT MÓN NÀY"
         ↓
Bot tự nhắn tin đặt món vào nhóm 🎉
```

---

### 🖱️ Thao tác trên bảng chọn món

| Thao tác | Kết quả |
|---|---|
| Click chọn món | Chọn món muốn ăn |
| Double-click vào món | Chốt luôn không cần bấm nút |
| Tích ô **"Ít cơm"** | Thêm ghi chú ít cơm vào tin nhắn |
| Bấm **"CHỐT MÓN NÀY"** | Bot nhắn tin đặt món |

---

### ⏰ Tự động tắt lúc 13:00

Bot được lập trình tự tắt vào **13:00** mỗi ngày để giải phóng bộ nhớ máy tính. Nếu đã cài Bước 6, ngày hôm sau bot sẽ tự bật lại khi bạn mở máy.

---

## 🐛 Khắc phục sự cố

<details>
<summary><b>❓ Lỗi "Phone number invalid" khi đăng nhập</b></summary>

Nhập số điện thoại đúng định dạng. Bot hỗ trợ cả hai cách:
- Dạng nội địa: `0912345678`
- Dạng quốc tế: `+84912345678`

</details>

<details>
<summary><b>❓ Bot không hiện bảng chọn món khi có ảnh</b></summary>

Kiểm tra theo thứ tự:
1. **ID nhóm** đã điền đúng chưa? (phải có dấu `-` ở đầu)
2. **Ảnh menu có rõ nét không?** Bot dùng AI đọc chữ — ảnh mờ có thể không đọc được
3. Thử nhờ người gửi lại ảnh chụp rõ hơn

</details>

<details>
<summary><b>❓ Muốn đổi tài khoản hoặc chuyển sang máy mới</b></summary>

1. Copy **toàn bộ thư mục** EatSyncBot sang máy mới
2. Xóa file **`.session`** trong thư mục đó
3. Mở `bot.exe` và đăng nhập lại từ đầu

</details>

---

## 📞 Hỗ trợ

Đã thử mọi cách mà bot vẫn "đình công"? 😅

👉 Chụp màn hình lỗi và liên hệ **Văn Đahy** hoặc người phát triển để được hỗ trợ!

---

<div align="center">

**EatSyncBot v1.1** · Cập nhật ngày 14/03/2026

*Làm bởi 💙 để không ai bỏ lỡ bữa trưa*

</div>
