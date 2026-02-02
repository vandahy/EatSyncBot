from telethon import TelegramClient
import asyncio

# === ĐIỀN THÔNG TIN CỦA BẠN VÀO ĐÂY ===
API_ID = 32205430  # THAY CỦA BẠN VÀO ĐÂY (Là số)
API_HASH = 'eb2c937788333abfaacbdebda490f21c' 

async def main():
    async with TelegramClient('get_id_session', API_ID, API_HASH) as client:
        print("--- DANH SÁCH CÁC NHÓM VÀ ID ---")
        # Lặp qua các cuộc trò chuyện (Dialogs)
        async for dialog in client.iter_dialogs():
            # Chỉ in ra nếu là Nhóm (Group hoặc Channel)
            if dialog.is_group or dialog.is_channel:
                print(f"Tên: {dialog.name} | ID: {dialog.id}")
        print("--------------------------------")

if __name__ == '__main__':
    asyncio.run(main())