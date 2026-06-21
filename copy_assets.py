# copy_assets.py
import shutil
import os

assets = [
    {
        "src": r"C:\Users\ADMIN\.gemini\antigravity\brain\9cf31341-6aab-4d41-8d31-46818ac19d6f\media__1782061770085.png",
        "dst": "screenshot.png",
        "name": "Ảnh chụp màn hình (screenshot.png)"
    },
    {
        "src": r"C:\Users\ADMIN\.gemini\antigravity\brain\9cf31341-6aab-4d41-8d31-46818ac19d6f\game_logo_1782062673886.png",
        "dst": "logo.png",
        "name": "Logo độc quyền của game (logo.png)"
    }
]

for asset in assets:
    if os.path.exists(asset["src"]):
        try:
            shutil.copy(asset["src"], asset["dst"])
            print(f"Copy thành công: {asset['name']}")
        except Exception as e:
            print(f"Lỗi khi copy {asset['name']}: {e}")
    else:
        print(f"Không tìm thấy file nguồn tạm của {asset['name']}.")
