# main.py
"""
Điểm xuất phát chính của Trò chơi (Main Entry Point)
Khởi tạo cửa sổ Pygame, thiết lập quản lý trạng thái, chạy vòng lặp game chính (Game Loop)
và giải phóng tài nguyên khi thoát game.

"""

import pygame
import sys
import shutil
import os

# Tự động sao chép tài nguyên (screenshot & logo) vào thư mục dự án
src_img = r"C:\Users\ADMIN\.gemini\antigravity\brain\9cf31341-6aab-4d41-8d31-46818ac19d6f\media__1782061770085.png"
dst_img = r"d:\gameSport Py\screenshot.png"
if os.path.exists(src_img) and not os.path.exists(dst_img):
    try:
        shutil.copy(src_img, dst_img)
    except Exception:
        pass

src_logo = r"C:\Users\ADMIN\.gemini\antigravity\brain\9cf31341-6aab-4d41-8d31-46818ac19d6f\game_logo_1782062673886.png"
dst_logo = r"d:\gameSport Py\logo.png"
if os.path.exists(src_logo) and not os.path.exists(dst_logo):
    try:
        shutil.copy(src_logo, dst_logo)
    except Exception:
        pass

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from states.state_manager import StateManager
from states.menu_state import MenuState
from states.playing_state import PlayingState
from states.game_over_state import GameOverState

def main():
    # 1. Khởi tạo Pygame
    pygame.init()
    
    # 2. Thiết lập màn hình hiển thị
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TOP-DOWN SOCCER CHAMPIONSHIP - LÊ VĂN CƯỜNG")
    
    # Khởi tạo đồng hồ để kiểm soát FPS
    clock = pygame.time.Clock()
    
    # 3. Thiết lập Trình quản lý trạng thái (State Manager)
    manager = StateManager(screen)
    
    # Đăng ký các trạng thái (Menu, Trận đấu, Kết quả)
    manager.register_state("MENU", MenuState())
    manager.register_state("PLAYING", PlayingState())
    manager.register_state("GAMEOVER", GameOverState())
    
    # Bắt đầu tại màn hình Menu
    manager.change_state("MENU")
    
    # 4. Vòng lặp trò chơi chính (Main Game Loop)
    running = True
    while running:
        # Lấy tất cả sự kiện trong frame hiện tại
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                
        # Gửi sự kiện cho trạng thái hiện tại xử lý
        manager.handle_events(events)
        
        # Cập nhật logic game
        manager.update()
        
        # Vẽ đồ họa giao diện
        manager.draw()
        
        # Cập nhật hiển thị màn hình
        pygame.display.flip()
        
        # Giới hạn tốc độ khung hình (FPS)
        clock.tick(FPS)
        
    # 5. Giải phóng tài nguyên và thoát game
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
