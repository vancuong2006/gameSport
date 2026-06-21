# config.py
"""
Cấu hình hệ thống trò chơi (Game Configuration)
Project: Trò chơi bóng đá 2D Top-down (Sports Pack Soccer)
Sinh viên thực hiện: LÊ VĂN CƯỜNG - MSSV: 2124110288
"""

import os
import pygame

# Kích thước màn hình
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Đường dẫn thư mục tài nguyên
ASSETS_DIR = "kenney_sports-pack"
PNG_DIR = os.path.join(ASSETS_DIR, "PNG")

# Cấu hình sân bóng
FIELD_LEFT = 60
FIELD_RIGHT = SCREEN_WIDTH - 60
FIELD_TOP = 100
FIELD_BOTTOM = SCREEN_HEIGHT - 40
FIELD_WIDTH = FIELD_RIGHT - FIELD_LEFT
FIELD_HEIGHT = FIELD_BOTTOM - FIELD_TOP

CENTER_X = FIELD_LEFT + FIELD_WIDTH // 2
CENTER_Y = FIELD_TOP + FIELD_HEIGHT // 2

# Cấu hình khung thành (Goal)
GOAL_HEIGHT = 160
GOAL_TOP = CENTER_Y - GOAL_HEIGHT // 2
GOAL_BOTTOM = CENTER_Y + GOAL_HEIGHT // 2
GOAL_DEPTH = 40

# Kích thước vật thể
PLAYER_RADIUS = 22
BALL_RADIUS = 12

# Vật lý học (Physics)
BALL_FRICTION = 0.978       # Lực ma sát làm chậm bóng nhiều hơn một chút để tránh trơn trượt
PLAYER_FRICTION = 0.88      # Lực ma sát làm chậm cầu thủ
BOUNCE_COEFF = 0.70         # Độ nảy khi va chạm tường/cột dọc
MAX_KICK_POWER = 13.5       # Lực sút tối đa vừa phải
DRIBBLE_DISTANCE = 32.0     # Khoảng cách tối đa để rê bóng/khống chế bóng

# Vận tốc di chuyển mặc định
PLAYER_SPEED = 3.8          # Giảm nhẹ tốc độ cầu thủ
AI_SPEED = 3.2              # Giảm nhẹ tốc độ AI để dễ điều khiển
AI_GK_SPEED = 2.4           # Tốc độ thủ môn vừa phải

# Bảng màu sắc (Color Palette)
COLOR_GRASS_LIGHT = (46, 204, 113)  # Màu cỏ sáng
COLOR_GRASS_DARK = (39, 174, 96)    # Màu cỏ tối (kẻ sọc)
COLOR_LINE = (255, 255, 255)        # Màu đường biên (trắng)
COLOR_GOAL_NET = (200, 230, 201)    # Màu lưới khung thành

COLOR_BG_UI = (44, 62, 80)          # Màu nền bảng điều khiển (Dark slate)
COLOR_TEXT_LIGHT = (236, 240, 241)  # Màu chữ sáng
COLOR_TEXT_DARK = (44, 62, 80)      # Màu chữ tối
COLOR_ACCENT = (231, 76, 60)        # Màu đỏ nhấn mạnh
COLOR_ACCENT_BLUE = (52, 152, 219)  # Màu xanh dương nhấn mạnh
COLOR_ACCENT_YELLOW = (241, 196, 15)# Màu vàng nhấn mạnh

# Phím điều khiển
# Người chơi 1 (Blue team - ARROWS + D/S)
P1_UP = pygame.K_UP
P1_LEFT = pygame.K_LEFT
P1_DOWN = pygame.K_DOWN
P1_RIGHT = pygame.K_RIGHT
P1_KICK = pygame.K_d
P1_PASS = pygame.K_s

# Người chơi 2 (Red team - WASD + J/K)
P2_UP = pygame.K_w
P2_LEFT = pygame.K_a
P2_DOWN = pygame.K_s
P2_RIGHT = pygame.K_d
P2_KICK = pygame.K_j
P2_PASS = pygame.K_k
