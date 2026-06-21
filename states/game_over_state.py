# states/game_over_state.py
"""
Màn hình Kết thúc trận đấu (Game Over State)
Hiển thị tỷ số chung cuộc, công bố đội chiến thắng và thống kê chi tiết các thông số kỹ thuật trận đấu
(Tỷ lệ kiểm soát bóng, số lần sút gôn), cùng các nút chức năng Chơi lại hoặc Quay về Menu chính.
"""

import pygame
from states.state_manager import State
from states.menu_state import Button
from utils.asset_loader import get_font
from config import (
    COLOR_BG_UI, COLOR_TEXT_LIGHT, COLOR_TEXT_DARK,
    COLOR_ACCENT, COLOR_ACCENT_BLUE, COLOR_ACCENT_YELLOW,
    SCREEN_WIDTH, SCREEN_HEIGHT
)

class GameOverState(State):
    def __init__(self):
        super().__init__()
        self.font_title = None
        self.font_result = None
        self.font_stats_header = None
        self.font_stats = None
        self.font_btn = None
        
        # Nhận dữ liệu truyền qua
        self.score_blue = 0
        self.score_red = 0
        self.winner = "DRAW"
        self.game_mode = "1p"
        self.total_match_time = 60
        self.stats = {}
        
        self.buttons = []

    def startup(self, **kwargs):
        """Được gọi khi trận đấu kết thúc để nạp số liệu thống kê trận đấu."""
        self.score_blue = kwargs.get("score_blue", 0)
        self.score_red = kwargs.get("score_red", 0)
        self.winner = kwargs.get("winner", "DRAW")
        self.game_mode = kwargs.get("game_mode", "1p")
        self.stats = kwargs.get("stats", {
            "shots_blue": 0, "shots_red": 0,
            "possession_frames_blue": 0, "possession_frames_red": 0
        })

        # Cấu hình phông chữ
        pygame.font.init()
        self.font_title = get_font(46, bold=True)
        self.font_result = get_font(38, bold=True)
        self.font_stats_header = get_font(20, bold=True)
        self.font_stats = get_font(18)
        self.font_btn = get_font(16, bold=True)

        # Khởi tạo các nút bấm
        self.buttons = []
        
        btn_replay = Button(SCREEN_WIDTH // 2 - 130, 620, 220, 48, "CHƠI LẠI (PLAY AGAIN)", "replay", "action")
        btn_menu = Button(SCREEN_WIDTH // 2 + 130, 620, 220, 48, "MENU CHÍNH (MAIN MENU)", "menu", "action")
        
        self.buttons.extend([btn_replay, btn_menu])

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.check_hover(mouse_pos)
            
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.buttons:
                    if btn.is_hovered:
                        if btn.value == "replay":
                            # Chơi lại với cấu hình cũ
                            # Lấy cấu hình trận đấu cũ từ PlayingState cũ hoặc mặc định
                            match_time = 60 if not hasattr(self.manager.states["PLAYING"], "total_match_time") else self.manager.states["PLAYING"].total_match_time
                            self.manager.change_state("PLAYING", game_mode=self.game_mode, match_time=match_time)
                        elif btn.value == "menu":
                            # Quay lại Menu chính
                            self.manager.change_state("MENU")

    def update(self):
        pass

    def draw(self, screen):
        # Vẽ nền xám đen đậm
        screen.fill(COLOR_BG_UI)
        
        # Vẽ khung viền báo cáo mờ màu trắng
        report_rect = pygame.Rect(180, 80, SCREEN_WIDTH - 360, SCREEN_HEIGHT - 320)
        pygame.draw.rect(screen, (30, 40, 50), report_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), report_rect, 2, border_radius=12)

        # 1. Tiêu đề Bảng Thống kê
        title_surf = self.font_title.render("THỐNG KÊ TRẬN ĐẤU", True, COLOR_ACCENT_YELLOW)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 130))
        screen.blit(title_surf, title_rect)
        
        # Gạch chân
        pygame.draw.line(screen, COLOR_ACCENT_YELLOW, (SCREEN_WIDTH // 2 - 150, 165), (SCREEN_WIDTH // 2 + 150, 165), 2)

        # 2. Công bố đội chiến thắng
        if self.winner == "BLUE":
            result_text = "ĐỘI XANH GIÀNH CHIẾN THẮNG!"
            result_color = COLOR_ACCENT_BLUE
        elif self.winner == "RED":
            result_text = "ĐỘI ĐỎ GIÀNH CHIẾN THẮNG!"
            result_color = COLOR_ACCENT
        else:
            result_text = "TRẬN ĐẤU KẾT THÚC VỚI TỶ SỐ HÒA!"
            result_color = (200, 200, 200)
            
        result_surf = self.font_result.render(result_text, True, result_color)
        result_rect = result_surf.get_rect(center=(SCREEN_WIDTH // 2, 210))
        screen.blit(result_surf, result_rect)

        # 3. Tỷ số chung cuộc lớn
        score_text = f"{self.score_blue}   -   {self.score_red}"
        score_font = get_font(50, bold=True)
        score_surf = score_font.render(score_text, True, COLOR_TEXT_LIGHT)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, 270))
        screen.blit(score_surf, score_rect)

        # Vẽ nhãn tên đội dưới điểm
        lbl_font = get_font(16, bold=True)
        lbl_blue = lbl_font.render("ĐỘI XANH", True, COLOR_ACCENT_BLUE)
        lbl_red = lbl_font.render("ĐỘI ĐỎ", True, COLOR_ACCENT)
        screen.blit(lbl_blue, (score_rect.left - 90, score_rect.centery - 10))
        screen.blit(lbl_red, (score_rect.right + 20, score_rect.centery - 10))

        # Đường kẻ phân cách bảng số liệu
        pygame.draw.line(screen, (70, 80, 90), (220, 325), (SCREEN_WIDTH - 220, 325), 1)

        # 4. Tính toán số liệu thống kê trận đấu
        # Tỷ lệ kiểm soát bóng (Possession)
        tot_frames = self.stats["possession_frames_blue"] + self.stats["possession_frames_red"]
        if tot_frames > 0:
            pos_blue = int(self.stats["possession_frames_blue"] / tot_frames * 100)
            pos_red = 100 - pos_blue
        else:
            pos_blue = 50
            pos_red = 50
            
        # Số cú sút
        shots_blue = self.stats["shots_blue"]
        shots_red = self.stats["shots_red"]

        # Vẽ bảng Thống kê chi tiết
        stat_rows = [
            ("KIỂM SOÁT BÓNG (%)", f"{pos_blue}%", f"{pos_red}%"),
            ("SỐ CÚ SÚT GÔN", str(shots_blue), str(shots_red)),
            ("SỐ BÀN THẮNG", str(self.score_blue), str(self.score_red))
        ]
        
        # Vẽ Header của bảng thống kê
        header_y = 350
        lbl_h_stat = self.font_stats_header.render("CHỈ SỐ THỐNG KÊ", True, COLOR_ACCENT_YELLOW)
        lbl_h_blue = self.font_stats_header.render("ĐỘI XANH", True, COLOR_ACCENT_BLUE)
        lbl_h_red = self.font_stats_header.render("ĐỘI ĐỎ", True, COLOR_ACCENT)
        
        screen.blit(lbl_h_stat, (250, header_y))
        screen.blit(lbl_h_blue, (SCREEN_WIDTH - 420, header_y))
        screen.blit(lbl_h_red, (SCREEN_WIDTH - 300, header_y))
        
        pygame.draw.line(screen, (80, 90, 100), (220, 380), (SCREEN_WIDTH - 220, 380), 2)
        
        # Vẽ các hàng số liệu
        row_y = 400
        for label, val_blue, val_red in stat_rows:
            lbl_surf = self.font_stats.render(label, True, COLOR_TEXT_LIGHT)
            v_blue_surf = self.font_stats.render(val_blue, True, COLOR_TEXT_LIGHT)
            v_red_surf = self.font_stats.render(val_red, True, COLOR_TEXT_LIGHT)
            
            screen.blit(lbl_surf, (250, row_y))
            screen.blit(v_blue_surf, (SCREEN_WIDTH - 400, row_y))
            screen.blit(v_red_surf, (SCREEN_WIDTH - 280, row_y))
            
            # Kẻ gạch ngang mờ cho mỗi hàng
            pygame.draw.line(screen, (50, 60, 70), (220, row_y + 30), (SCREEN_WIDTH - 220, row_y + 30), 1)
            row_y += 45

        # Vẽ các nút chức năng điều hướng
        for btn in self.buttons:
            btn.draw(screen, self.font_btn, COLOR_ACCENT_BLUE, (52, 73, 94))
            
      
        credit_font = get_font(12)
        credit_surf = credit_font.render("Project: Football 2D Top-down (Sports Pack Soccer)", True, (100, 110, 120))
        screen.blit(credit_surf, credit_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35)))
