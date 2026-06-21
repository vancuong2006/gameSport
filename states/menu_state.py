# states/menu_state.py
"""
Màn hình Menu chính (Main Menu State)
Cho phép người dùng chọn chế độ chơi (1 Player / 2 Players), thời gian trận đấu
"""

import pygame
import sys
import math
from states.state_manager import State
from config import (
    COLOR_BG_UI, COLOR_TEXT_LIGHT, COLOR_TEXT_DARK,
    COLOR_ACCENT, COLOR_ACCENT_BLUE, COLOR_ACCENT_YELLOW,
    SCREEN_WIDTH, SCREEN_HEIGHT
)
from utils.asset_loader import load_player, load_ball, get_font

class Button:
    def __init__(self, x, y, width, height, text, value, group_name):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.value = value
        self.group_name = group_name  # Phân loại nhóm để chọn 1 trong nhiều
        self.is_hovered = False
        self.is_selected = False

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, screen, font, active_color, normal_color):
        # Chọn màu nền dựa trên trạng thái chọn hoặc hover
        if self.is_selected:
            bg_color = active_color
            border_color = (255, 255, 255)
            text_color = COLOR_TEXT_LIGHT
        elif self.is_hovered:
            bg_color = [int(c * 1.2) if c * 1.2 <= 255 else 255 for c in normal_color]
            border_color = COLOR_TEXT_LIGHT
            text_color = COLOR_TEXT_LIGHT
        else:
            bg_color = normal_color
            border_color = (100, 110, 120)
            text_color = (200, 200, 200)

        # Vẽ bóng đổ (shadow) nhẹ
        shadow_rect = self.rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(screen, (20, 25, 30), shadow_rect, border_radius=8)

        # Vẽ nút chính
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)

        # Vẽ văn bản
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class MenuState(State):
    def __init__(self):
        super().__init__()
        self.font_title = None
        self.font_subtitle = None
        self.font_section = None
        self.font_btn = None
        self.font_credits = None
        
        # Các lựa chọn mặc định
        self.game_mode = "1p"       # "1p": vs AI, "2p": PvP local
        self.match_time = 60        # 60s, 120s, 180s
        
        # Danh sách nút bấm
        self.buttons = []
        
        # Quả bóng hoạt họa chạy quanh màn hình trang trí
        self.decor_ball_x = 100.0
        self.decor_ball_y = 100.0
        self.decor_ball_vx = 3.0
        self.decor_ball_vy = 2.0
        self.decor_ball_angle = 0
        self.ball_img = None
        self.p1_preview = None
        self.p2_preview = None
        
    def startup(self, **kwargs):
        """Khởi tạo tài nguyên khi màn hình Menu xuất hiện."""
        pygame.font.init()
        self.font_title = get_font(54, bold=True)
        self.font_subtitle = get_font(22, italic=True)
        self.font_section = get_font(20, bold=True)
        self.font_btn = get_font(16, bold=True)
        self.font_credits = get_font(14)
        
        # Khởi tạo nút bấm
        self.buttons = []
        
        # Nhóm nút Chế độ chơi (Game Mode)
        btn_1p = Button(SCREEN_WIDTH // 2 - 140, 310, 240, 42, "1 NGƯỜI CHƠI (VS AI)", "1p", "mode")
        btn_1p.is_selected = True # Mặc định
        btn_2p = Button(SCREEN_WIDTH // 2 + 140, 310, 240, 42, "2 NGƯỜI CHƠI (PVP)", "2p", "mode")
        self.buttons.extend([btn_1p, btn_2p])
        
        # Nhóm nút Thời gian (Match Time)
        btn_60s = Button(SCREEN_WIDTH // 2 - 160, 430, 120, 40, "1 PHÚT", 60, "time")
        btn_60s.is_selected = True # Mặc định
        btn_120s = Button(SCREEN_WIDTH // 2, 430, 120, 40, "2 PHÚT", 120, "time")
        btn_180s = Button(SCREEN_WIDTH // 2 + 160, 430, 120, 40, "3 PHÚT", 180, "time")
        self.buttons.extend([btn_60s, btn_120s, btn_180s])
        
        # Nút Bắt đầu lớn ở dưới cùng
        self.btn_start = Button(SCREEN_WIDTH // 2, 600, 350, 55, "BẮT ĐẦU TRẬN ĐẤU (START)", "start", "action")
        self.buttons.append(self.btn_start)
        
        # Nạp ảnh hoạt họa trang trí
        self.ball_img = load_ball(30) # Quả bóng lớn trang trí
        self.p1_preview = load_player("blue", 1, (70, 70))
        self.p2_preview = load_player("red", 1, (70, 70))
        
        # Đặt lại vị trí quả bóng trang trí ngẫu nhiên
        self.decor_ball_x = float(SCREEN_WIDTH // 2)
        self.decor_ball_y = 120.0
        self.decor_ball_vx = 3.5
        self.decor_ball_vy = 2.5

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        
        for btn in self.buttons:
            btn.check_hover(mouse_pos)
            
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Xử lý nhấn chuột trái
                for btn in self.buttons:
                    if btn.is_hovered:
                        if btn.group_name == "mode":
                            # Chọn 1 chế độ duy nhất
                            for b in self.buttons:
                                if b.group_name == "mode":
                                    b.is_selected = False
                            btn.is_selected = True
                            self.game_mode = btn.value
                        elif btn.group_name == "time":
                            # Chọn 1 thời gian duy nhất
                            for b in self.buttons:
                                if b.group_name == "time":
                                    b.is_selected = False
                            btn.is_selected = True
                            self.match_time = btn.value
                        elif btn.group_name == "action" and btn.value == "start":
                            # Bắt đầu trận đấu, chuyển sang PLAYING state
                            self.manager.change_state("PLAYING", game_mode=self.game_mode, match_time=self.match_time)

    def update(self):
        # Di chuyển quả bóng hoạt họa trang trí nảy xung quanh màn hình gôn
        self.decor_ball_x += self.decor_ball_vx
        self.decor_ball_y += self.decor_ball_vy
        self.decor_ball_angle += 2
        
        # Nảy tường trái/phải
        if self.decor_ball_x - 30 < 0 or self.decor_ball_x + 30 > SCREEN_WIDTH:
            self.decor_ball_vx = -self.decor_ball_vx
            self.decor_ball_x += self.decor_ball_vx
            
        # Nảy tường trên/dưới
        if self.decor_ball_y - 30 < 0 or self.decor_ball_y + 30 > SCREEN_HEIGHT:
            self.decor_ball_vy = -self.decor_ball_vy
            self.decor_ball_y += self.decor_ball_vy

    def draw(self, screen):
        # Vẽ nền màn hình menu chính với gradient hoặc màu tối sang trọng
        screen.fill(COLOR_BG_UI)
        
        # Vẽ các vạch sân bóng mờ trang trí phía dưới
        # Sân bóng mờ nhạt làm background
        bg_grass = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_grass.fill((30, 45, 60))
        # Vẽ vòng tròn trung tâm lớn mờ
        pygame.draw.circle(bg_grass, (40, 60, 80), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150, 4)
        pygame.draw.line(bg_grass, (40, 60, 80), (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 4)
        screen.blit(bg_grass, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Vẽ quả bóng nảy trang trí phía sau chữ
        if self.ball_img:
            rotated_ball = pygame.transform.rotate(self.ball_img, self.decor_ball_angle)
            ball_rect = rotated_ball.get_rect(center=(int(self.decor_ball_x), int(self.decor_ball_y)))
            # Tạo hiệu ứng bóng đổ cho quả bóng trang trí
            shadow_surf = pygame.Surface(ball_rect.size, pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (10, 15, 20, 120), (ball_rect.width // 2 + 5, ball_rect.height // 2 + 5), 25)
            screen.blit(shadow_surf, ball_rect.topleft)
            screen.blit(rotated_ball, ball_rect.topleft)

      
        title_surf = self.font_title.render("TOP-DOWN SOCCER CHAMPION", True, COLOR_ACCENT_YELLOW)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 110))
        # Tạo bóng đổ cho chữ tiêu đề (Text shadow)
        shadow_title = self.font_title.render("TOP-DOWN SOCCER CHAMPION", True, (15, 20, 25))
        screen.blit(shadow_title, title_rect.move(3, 3))
        screen.blit(title_surf, title_rect)

        # Vẽ Phụ đề thông tin
        sub_text = "LÊ VĂN CƯỜNG"
        sub_surf = self.font_subtitle.render(sub_text, True, COLOR_TEXT_LIGHT)
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 170))
        screen.blit(sub_surf, sub_rect)

        # Đường gạch ngang phân cách
        pygame.draw.line(screen, COLOR_ACCENT_YELLOW, (SCREEN_WIDTH // 2 - 250, 200), (SCREEN_WIDTH // 2 + 250, 200), 2)

        # Vẽ tiêu đề phân mục 1: Chế độ chơi
        mode_label = self.font_section.render("CHỌN CHẾ ĐỘ CHƠI (GAME MODE):", True, COLOR_TEXT_LIGHT)
        screen.blit(mode_label, (SCREEN_WIDTH // 2 - 140, 255))
        
        # Vẽ tiêu đề phân mục 2: Thời gian thi đấu
        time_label = self.font_section.render("THỜI GIAN THI ĐẤU (DURATION):", True, COLOR_TEXT_LIGHT)
        screen.blit(time_label, (SCREEN_WIDTH // 2 - 140, 375))

        # Vẽ các nút lựa chọn
        for btn in self.buttons:
            if btn.group_name == "mode":
                btn.draw(screen, self.font_btn, COLOR_ACCENT_BLUE, (52, 73, 94))
            elif btn.group_name == "time":
                btn.draw(screen, self.font_btn, COLOR_ACCENT, (52, 73, 94))
            elif btn.group_name == "action":
                # Nút start có nhịp thở (pulse) hoạt họa dựa trên hàm sin
                pulse = int(math.sin(pygame.time.get_ticks() * 0.007) * 15)
                # Thay đổi kích thước nút start tạm thời theo hiệu ứng pulse
                orig_rect = btn.rect.copy()
                btn.rect.inflate_ip(pulse, pulse // 2)
                btn.draw(screen, self.font_btn, COLOR_ACCENT_YELLOW, (192, 57, 43))
                btn.rect = orig_rect

        # Vẽ hình ảnh xem trước của cầu thủ hai bên góc để làm màn hình phong phú hơn
        if self.p1_preview:
            # Player 1 (Blue)
            p1_rect = self.p1_preview.get_rect(center=(180, 500))
            # Vẽ bóng đổ cầu thủ
            pygame.draw.ellipse(screen, (20, 25, 30, 150), (p1_rect.x, p1_rect.bottom - 15, 70, 20))
            screen.blit(self.p1_preview, p1_rect)
            p1_lbl = self.font_section.render("ĐỘI XANH (WASD)", True, COLOR_ACCENT_BLUE)
            screen.blit(p1_lbl, p1_lbl.get_rect(center=(180, 560)))

        if self.p2_preview:
            # Player 2 (Red)
            p2_rect = self.p2_preview.get_rect(center=(SCREEN_WIDTH - 180, 500))
            # Vẽ bóng đổ cầu thủ
            pygame.draw.ellipse(screen, (20, 25, 30, 150), (p2_rect.x, p2_rect.bottom - 15, 70, 20))
            screen.blit(self.p2_preview, p2_rect)
            p2_lbl = self.font_section.render(
                "ĐỘI ĐỎ (AI)" if self.game_mode == "1p" else "ĐỘI ĐỎ (MŨI TÊN)", 
                True, COLOR_ACCENT
            )
            screen.blit(p2_lbl, p2_lbl.get_rect(center=(SCREEN_WIDTH - 180, 560)))


        credit_y = SCREEN_HEIGHT - 35
        credits = [
            "Project: Football 2D Top-down (Sports Pack Soccer)",
            "Sinh viên thực hiện: LÊ VĂN CƯỜNG - MSSV: 2124110288"
        ]
        for i, line in enumerate(credits):
            txt_surf = self.font_credits.render(line, True, (140, 150, 160))
            txt_rect = txt_surf.get_rect(center=(SCREEN_WIDTH // 2, credit_y + i * 16))
            screen.blit(txt_surf, txt_rect)
