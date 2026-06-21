# states/playing_state.py
"""
Màn hình Trận đấu chính (Playing State)
Quản lý toàn bộ vòng lặp trận đấu bao gồm vẽ sân cỏ sọc chuyên nghiệp, cập nhật vị trí cầu thủ và bóng,
xử lý va chạm vật lý giữa người-người, người-bóng, đếm ngược thời gian thi đấu, ghi điểm và hiệu ứng ăn mừng GOAL!
"""

import pygame
import math
import random
from states.state_manager import State
from config import (
    COLOR_GRASS_LIGHT, COLOR_GRASS_DARK, COLOR_LINE, COLOR_GOAL_NET,
    COLOR_BG_UI, COLOR_TEXT_LIGHT, COLOR_ACCENT, COLOR_ACCENT_BLUE, COLOR_ACCENT_YELLOW,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM, FIELD_WIDTH, FIELD_HEIGHT,
    CENTER_X, CENTER_Y, GOAL_TOP, GOAL_BOTTOM, GOAL_HEIGHT, GOAL_DEPTH, FPS,
    P1_UP, P1_DOWN, P1_LEFT, P1_RIGHT, P1_KICK, P1_PASS,
    P2_UP, P2_DOWN, P2_LEFT, P2_RIGHT, P2_KICK, P2_PASS
)
from sprites.ball import Ball
from sprites.player_user import UserPlayer
from sprites.player_ai import AIPlayer
from utils.asset_loader import get_font
from sprites.referee import Referee, Linesman

class PlayingState(State):
    def __init__(self):
        super().__init__()
        self.font_score = None
        self.font_timer = None
        self.font_notice = None
        self.font_tip = None
        
        # Các thực thể trong game
        self.ball = None
        self.players = pygame.sprite.Group()
        self.blue_team = []
        self.red_team = []
        
        # Điểm và Thời gian
        self.score_blue = 0
        self.score_red = 0
        self.total_match_time = 60
        self.time_remaining = 0.0
        
        # Trạng thái trận đấu
        self.game_mode = "1p"
        self.is_celebrating = False
        self.celebration_timer = 0
        self.scoring_team = 0  # 1: Blue, 2: Red
        
        # Thống kê trận đấu (để đưa vào màn hình kết quả)
        self.stats = {
            "shots_blue": 0,
            "shots_red": 0,
            "possession_frames_blue": 0,
            "possession_frames_red": 0
        }

    def startup(self, **kwargs):
        """Khởi tạo trận đấu mới dựa trên lựa chọn ở Menu."""
        self.game_mode = kwargs.get("game_mode", "1p")
        self.total_match_time = kwargs.get("match_time", 60)
        self.time_remaining = float(self.total_match_time)
        
        self.score_blue = 0
        self.score_red = 0
        self.is_celebrating = False
        self.celebration_timer = 0
        
        self.stats = {
            "shots_blue": 0,
            "shots_red": 0,
            "possession_frames_blue": 0,
            "possession_frames_red": 0
        }

        # Khởi tạo phông chữ
        pygame.font.init()
        self.font_score = get_font(36, bold=True)
        self.font_timer = get_font(40, bold=True)
        self.font_notice = get_font(70, bold=True)
        self.font_tip = get_font(14)

        # Khởi tạo bóng
        self.ball = Ball()
        
        # Khởi tạo trọng tài
        self.referee = Referee()
        self.linesman_top = Linesman(is_top=True)
        self.linesman_bottom = Linesman(is_top=False)
        
        # Biến trạng thái ném biên/đá phạt biên
        self.out_of_bounds_timer = 0
        self.out_of_bounds_type = ""
        self.out_of_bounds_team = ""
        self.banner_text = ""
        
        # Khởi tạo các đội bóng (3v3)
        self.players.empty()
        self.blue_team = []
        self.red_team = []
        
        # Định nghĩa phím điều khiển cho Player 1 (Blue)
        p1_controls = {
            'up': P1_UP,
            'down': P1_DOWN,
            'left': P1_LEFT,
            'right': P1_RIGHT,
            'kick': P1_KICK,
            'pass': P1_PASS
        }
        
        # Định nghĩa phím điều khiển cho Player 2 (Red) nếu chơi 2 người
        p2_controls = {
            'up': P2_UP,
            'down': P2_DOWN,
            'left': P2_LEFT,
            'right': P2_RIGHT,
            'kick': P2_KICK,
            'pass': P2_PASS
        }

        # --- ĐỘI XANH (BLUE TEAM - LEFT SIDE) ---
        # Thủ môn AI
        gk_blue = AIPlayer("blue", 11, "goalkeeper", FIELD_LEFT + 45, CENTER_Y, "left")
        # Hậu vệ AI
        def_blue = AIPlayer("blue", 4, "defender", CENTER_X - 220, CENTER_Y - 100, "left")
        # Tiền đạo Người chơi điều khiển
        striker_blue = UserPlayer("blue", 10, "striker", CENTER_X - 100, CENTER_Y + 80, p1_controls)
        
        self.blue_team.extend([gk_blue, def_blue, striker_blue])
        self.players.add(gk_blue, def_blue, striker_blue)

        # --- ĐỘI ĐỎ (RED TEAM - RIGHT SIDE) ---
        # Thủ môn AI
        gk_red = AIPlayer("red", 1, "goalkeeper", FIELD_RIGHT - 45, CENTER_Y, "right")
        # Hậu vệ AI
        def_red = AIPlayer("red", 3, "defender", CENTER_X + 220, CENTER_Y + 100, "right")
        
        # Tiền đạo: có thể là Người điều khiển hoặc AI tuỳ theo game_mode
        if self.game_mode == "2p":
            striker_red = UserPlayer("red", 9, "striker", CENTER_X + 100, CENTER_Y - 80, p2_controls)
        else:
            striker_red = AIPlayer("red", 9, "striker", CENTER_X + 100, CENTER_Y - 80, "right")
            
        self.red_team.extend([gk_red, def_red, striker_red])
        self.players.add(gk_red, def_red, striker_red)
        
        self.reset_positions_for_kickoff()

    def reset_positions_for_kickoff(self):
        """Đặt bóng ở tâm sân và các cầu thủ về vị trí mặc định khi bắt đầu/ghi bàn."""
        self.ball.reset(CENTER_X, CENTER_Y)
        for player in self.players:
            player.reset()
        if hasattr(self, 'referee'):
            self.referee.reset()
            self.referee.x = CENTER_X
            self.referee.y = CENTER_Y - 120
            self.referee.vx = 0.0
            self.referee.vy = 0.0
            self.referee.update_rect()
        if hasattr(self, 'linesman_top'):
            self.linesman_top.reset()
            self.linesman_top.x = CENTER_X
            self.linesman_top.y = FIELD_TOP - 24
            self.linesman_top.vx = 0.0
            self.linesman_top.vy = 0.0
            self.linesman_top.update_rect()
        if hasattr(self, 'linesman_bottom'):
            self.linesman_bottom.reset()
            self.linesman_bottom.x = CENTER_X
            self.linesman_bottom.y = FIELD_BOTTOM + 24
            self.linesman_bottom.vx = 0.0
            self.linesman_bottom.vy = 0.0
            self.linesman_bottom.update_rect()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Nhấn ESC để quay lại menu chính lập tức
                    self.manager.change_state("MENU")
                
                # Ghi nhận số lần sút để tính thống kê
                if not self.is_celebrating:
                    if event.key == P1_KICK:
                        # Kiểm tra xem striker xanh có ở gần bóng để sút không
                        striker = self.blue_team[2]
                        if striker.get_distance_to(self.ball.x, self.ball.y) < 40:
                            self.stats["shots_blue"] += 1
                    if self.game_mode == "2p" and event.key == P2_KICK:
                        # Kiểm tra xem striker đỏ có ở gần bóng để sút không
                        striker = self.red_team[2]
                        if striker.get_distance_to(self.ball.x, self.ball.y) < 40:
                            self.stats["shots_red"] += 1

    def update_collisions_player_player(self):
        """Xử lý va chạm đàn hồi đơn giản giữa các cầu thủ để tránh đè lấn chồng chéo lên nhau."""
        player_list = list(self.players)
        for i in range(len(player_list)):
            for j in range(i + 1, len(player_list)):
                p1 = player_list[i]
                p2 = player_list[j]
                
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                dist = math.hypot(dx, dy)
                min_dist = p1.radius + p2.radius
                
                if dist < min_dist:
                    # Hai cầu thủ chạm nhau -> Đẩy họ ra hai phía ngược nhau
                    overlap = min_dist - dist
                    if dist == 0:
                        # Nếu trùng toạ độ tuyệt đối, đẩy ngẫu nhiên
                        p2.x += min_dist / 2
                        p1.x -= min_dist / 2
                    else:
                        push_x = (dx / dist) * overlap * 0.5
                        push_y = (dy / dist) * overlap * 0.5
                        
                        p2.x += push_x
                        p2.y += push_y
                        p1.x -= push_x
                        p1.y -= push_y
                        
                        # Giảm nhẹ tốc độ của cả hai khi va chạm nhau
                        p1.vx *= 0.8
                        p1.vy *= 0.8
                        p2.vx *= 0.8
                        p2.vy *= 0.8

    def update(self):
        # 1. Nếu đang ăn mừng ghi bàn, ngưng cập nhật trận đấu, chạy đếm ngược ăn mừng
        if self.is_celebrating:
            self.celebration_timer -= 1
            if self.celebration_timer <= 0:
                self.is_celebrating = False
                self.reset_positions_for_kickoff()
            # Vẫn cập nhật chuyển động chậm dần của bóng trong lưới
            self.ball.update()
            return

        # 1.5. Nếu đang tạm dừng do bóng ra biên (Out of bounds)
        if hasattr(self, 'out_of_bounds_timer') and self.out_of_bounds_timer > 0:
            self.out_of_bounds_timer -= 1
            if self.out_of_bounds_timer <= 0:
                self.resolve_out_of_bounds_restart()
            # Vẫn cập nhật chuyển động chậm dần của bóng
            self.ball.update()
            # Trọng tài vẫn di chuyển
            self.referee.update(self.ball, self.players)
            self.linesman_top.update(self.ball)
            self.linesman_bottom.update(self.ball)
            return

        # 2. Cập nhật thời gian thi đấu còn lại
        self.time_remaining -= 1.0 / FPS
        if self.time_remaining <= 0:
            self.time_remaining = 0
            # Chuyển sang màn hình GAME OVER và truyền dữ liệu thống kê
            winner = "BLUE" if self.score_blue > self.score_red else ("RED" if self.score_red > self.score_blue else "DRAW")
            self.manager.change_state("GAMEOVER", 
                                      score_blue=self.score_blue, 
                                      score_red=self.score_red, 
                                      winner=winner,
                                      stats=self.stats,
                                      game_mode=self.game_mode)
            return

        # 3. Cập nhật đầu vào của người chơi điều khiển
        keys = pygame.key.get_pressed()
        
        # Cập nhật đội xanh (Blue team)
        for player in self.blue_team:
            if isinstance(player, UserPlayer):
                player.update(keys, self.ball, self.blue_team, self.red_team)
            else:
                player.update(self.ball)
                
        # Cập nhật đội đỏ (Red team)
        for player in self.red_team:
            if isinstance(player, UserPlayer):
                player.update(keys, self.ball, self.red_team, self.blue_team)
            else:
                player.update(self.ball)
                # Đếm số lần sút bóng tự động của AI
                if player.role == "striker" and player.get_distance_to(self.ball.x, self.ball.y) < 35:
                    if random.random() < 0.05:  # Giới hạn ghi nhận sút thực tế
                        self.stats["shots_red"] += 1

        # Xử lý va chạm giữa các cầu thủ
        self.update_collisions_player_player()

        # 4. Cập nhật chuyển động bóng
        self.ball.update()
        
        # Cập nhật chuyển động trọng tài
        self.referee.update(self.ball, self.players)
        self.linesman_top.update(self.ball)
        self.linesman_bottom.update(self.ball)
        
        # 5. Theo dõi kiểm soát bóng để tính thời gian kiểm soát (Possession %)
        blue_has_control = any(p.has_ball_control for p in self.blue_team)
        red_has_control = any(p.has_ball_control for p in self.red_team)
        if blue_has_control:
            self.stats["possession_frames_blue"] += 1
        elif red_has_control:
            self.stats["possession_frames_red"] += 1

        # 6. Kiểm tra bàn thắng
        goal_status = self.ball.check_goal()
        if goal_status == 1:
            # Lưới bên trái bị ghi bàn -> Đội Đỏ (Red) ghi bàn
            self.score_red += 1
            self.is_celebrating = True
            self.celebration_timer = 110  # ~ 1.8 giây ăn mừng
            self.scoring_team = 2
        elif goal_status == 2:
            # Lưới bên phải bị ghi bàn -> Đội Xanh (Blue) ghi bàn
            self.score_blue += 1
            self.is_celebrating = True
            self.celebration_timer = 110
            self.scoring_team = 1
            
        # 7. Kiểm tra bóng ra ngoài biên
        if goal_status == 0:
            self.check_out_of_bounds()

    def draw_field(self, screen):
        """Vẽ toàn bộ sân cỏ, sọc sân bóng, vòng tròn trung tâm và khung thành bằng đồ họa vector."""
        # Nền cỏ xanh lá sọc dọc
        screen.fill(COLOR_GRASS_LIGHT)
        stripe_width = FIELD_WIDTH // 15
        for i in range(15):
            if i % 2 == 0:
                stripe_rect = pygame.Rect(FIELD_LEFT + i * stripe_width, FIELD_TOP, stripe_width, FIELD_HEIGHT)
                pygame.draw.rect(screen, COLOR_GRASS_DARK, stripe_rect)

        # Vẽ lưới khung thành hai bên gôn (Hiệu ứng đan lưới mắt cáo mờ rất đẹp)
        self.draw_goal_net(screen, FIELD_LEFT - GOAL_DEPTH, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT, is_left=True)
        self.draw_goal_net(screen, FIELD_RIGHT, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT, is_left=False)

        # Đường biên bao quanh sân bóng
        pygame.draw.rect(screen, COLOR_LINE, (FIELD_LEFT, FIELD_TOP, FIELD_WIDTH, FIELD_HEIGHT), 3)

        # Vòng tròn trung tâm và chấm giao bóng giữa sân
        pygame.draw.circle(screen, COLOR_LINE, (CENTER_X, CENTER_Y), 90, 3)
        pygame.draw.circle(screen, COLOR_LINE, (CENTER_X, CENTER_Y), 6)
        
        # Đường kẻ giữa sân chia đôi hai phần sân bóng
        pygame.draw.line(screen, COLOR_LINE, (CENTER_X, FIELD_TOP), (CENTER_X, FIELD_BOTTOM), 3)

        # Khu vực 16m50 (Penalty Area)
        pen_area_width = 140
        pen_area_height = 280
        # Bên Trái
        pygame.draw.rect(screen, COLOR_LINE, (FIELD_LEFT, CENTER_Y - pen_area_height // 2, pen_area_width, pen_area_height), 3)
        pygame.draw.circle(screen, COLOR_LINE, (FIELD_LEFT + 100, CENTER_Y), 4) # Chấm phạt đền
        # Vẽ vòng bán nguyệt trước vòng cấm gôn trái
        pygame.draw.arc(screen, COLOR_LINE, (FIELD_LEFT + 40, CENTER_Y - 70, 120, 140), -math.pi/2, math.pi/2, 3)
        
        # Bên Phải
        pygame.draw.rect(screen, COLOR_LINE, (FIELD_RIGHT - pen_area_width, CENTER_Y - pen_area_height // 2, pen_area_width, pen_area_height), 3)
        pygame.draw.circle(screen, COLOR_LINE, (FIELD_RIGHT - 100, CENTER_Y), 4) # Chấm phạt đền
        pygame.draw.arc(screen, COLOR_LINE, (FIELD_RIGHT - 160, CENTER_Y - 70, 120, 140), math.pi/2, 3*math.pi/2, 3)

        # Khu vực 5m50 (Goal Area)
        goal_area_width = 50
        goal_area_height = 160
        # Bên Trái
        pygame.draw.rect(screen, COLOR_LINE, (FIELD_LEFT, CENTER_Y - goal_area_height // 2, goal_area_width, goal_area_height), 3)
        # Bên Phải
        pygame.draw.rect(screen, COLOR_LINE, (FIELD_RIGHT - goal_area_width, CENTER_Y - goal_area_height // 2, goal_area_width, goal_area_height), 3)

        # Các cung phạt góc (Corner arcs)
        corner_r = 15
        # Góc trên bên trái
        pygame.draw.arc(screen, COLOR_LINE, (FIELD_LEFT - corner_r, FIELD_TOP - corner_r, corner_r*2, corner_r*2), 3*math.pi/2, 2*math.pi, 2)
        # Góc dưới bên trái
        pygame.draw.arc(screen, COLOR_LINE, (FIELD_LEFT - corner_r, FIELD_BOTTOM - corner_r, corner_r*2, corner_r*2), 0, math.pi/2, 2)
        # Góc trên bên phải
        pygame.draw.arc(screen, COLOR_LINE, (FIELD_RIGHT - corner_r, FIELD_TOP - corner_r, corner_r*2, corner_r*2), math.pi, 3*math.pi/2, 2)
        # Góc dưới bên phải
        pygame.draw.arc(screen, COLOR_LINE, (FIELD_RIGHT - corner_r, FIELD_BOTTOM - corner_r, corner_r*2, corner_r*2), math.pi/2, math.pi, 2)

        # Vẽ 4 cột dọc khung thành màu trắng nổi bật
        pygame.draw.circle(screen, (255, 255, 255), (FIELD_LEFT, GOAL_TOP), 6)
        pygame.draw.circle(screen, (255, 255, 255), (FIELD_LEFT, GOAL_BOTTOM), 6)
        pygame.draw.circle(screen, (255, 255, 255), (FIELD_RIGHT, GOAL_TOP), 6)
        pygame.draw.circle(screen, (255, 255, 255), (FIELD_RIGHT, GOAL_BOTTOM), 6)

    def draw_goal_net(self, screen, x, y, width, height, is_left):
        """Vẽ lưới mắt cáo khung thành bằng các đường kẻ đan chéo."""
        # Vẽ nền xám lưới gôn
        pygame.draw.rect(screen, (25, 45, 25), (x, y, width, height))
        
        # Vẽ các vạch lưới đan chéo
        spacing = 10
        net_color = (130, 160, 130)
        
        # Đường xiên sắc
        for start_x in range(x - height, x + width, spacing):
            # Tính điểm bắt đầu và điểm kết thúc của đường chéo giới hạn trong khung thành
            x1 = max(x, start_x)
            y1 = y + (x1 - start_x)
            x2 = min(x + width, start_x + height)
            y2 = y + (x2 - start_x)
            if y1 <= y + height and y2 <= y + height:
                pygame.draw.line(screen, net_color, (x1, y1), (x2, y2), 1)
                
        # Đường xiên huyền
        for start_x in range(x, x + width + height, spacing):
            x1 = max(x, start_x - height)
            y1 = y + (start_x - x1)
            x2 = min(x + width, start_x)
            y2 = y + (start_x - x2)
            if y1 <= y + height and y2 <= y + height:
                pygame.draw.line(screen, net_color, (x1, y1), (x2, y2), 1)

        # Kẻ viền khung lưới bao bên ngoài
        if is_left:
            pygame.draw.line(screen, COLOR_LINE, (x, y), (x + width, y), 3)
            pygame.draw.line(screen, COLOR_LINE, (x, y + height), (x + width, y + height), 3)
            pygame.draw.line(screen, COLOR_LINE, (x, y), (x, y + height), 3)
        else:
            pygame.draw.line(screen, COLOR_LINE, (x, y), (x + width, y), 3)
            pygame.draw.line(screen, COLOR_LINE, (x, y + height), (x + width, y + height), 3)
            pygame.draw.line(screen, COLOR_LINE, (x + width, y), (x + width, y + height), 3)

    def draw_hud(self, screen):
        """Vẽ bảng hiển thị tỉ số và thời gian ở đầu màn hình."""
        # Nền đen xám sang trọng cho bảng HUD
        hud_height = 80
        pygame.draw.rect(screen, COLOR_BG_UI, (0, 0, SCREEN_WIDTH, hud_height))
        # Viền dưới của HUD
        pygame.draw.line(screen, COLOR_ACCENT_YELLOW, (0, hud_height), (SCREEN_WIDTH, hud_height), 3)

        # 1. Hiển thị Tỉ số (Scoreboard) ở trung tâm
        score_text = f"{self.score_blue}   -   {self.score_red}"
        score_surf = self.font_score.render(score_text, True, COLOR_TEXT_LIGHT)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, hud_height // 2))
        
        # Vẽ thẻ màu xanh/đỏ phía dưới tỉ số để nhận diện đội bóng
        p_card_w, p_card_h = 75, 42
        pygame.draw.rect(screen, COLOR_ACCENT_BLUE, (score_rect.left - p_card_w - 20, hud_height // 2 - p_card_h // 2, p_card_w, p_card_h), border_radius=6)
        pygame.draw.rect(screen, COLOR_ACCENT, (score_rect.right + 20, hud_height // 2 - p_card_h // 2, p_card_w, p_card_h), border_radius=6)
        
        # Nhãn Tên Đội bóng viết đè lên thẻ màu
        name_blue = self.font_score.render("BLU", True, COLOR_TEXT_LIGHT)
        name_red = self.font_score.render("RED", True, COLOR_TEXT_LIGHT)
        screen.blit(name_blue, name_blue.get_rect(center=(score_rect.left - p_card_w // 2 - 20, hud_height // 2)))
        screen.blit(name_red, name_red.get_rect(center=(score_rect.right + p_card_w // 2 + 20, hud_height // 2)))
        
        # Vẽ điểm tỉ số
        screen.blit(score_surf, score_rect)

        # 2. Hiển thị Đồng hồ (Timer) bên phải
        minutes = int(self.time_remaining) // 60
        seconds = int(self.time_remaining) % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"
        timer_surf = self.font_timer.render(timer_text, True, COLOR_ACCENT_YELLOW)
        screen.blit(timer_surf, (SCREEN_WIDTH - 150, hud_height // 2 - timer_surf.get_height() // 2))

        # 3. Hiển thị Phím điều khiển trợ giúp bên trái (HUD tips)
        tip_y = 15
        if self.game_mode == "1p":
            tips = [
                "P1 (XANH): Di chuyển = MŨI TÊN | Sút/Tắc bóng = D | Chuyền = S",
                "ĐỘI ĐỎ (AI): Tự động phòng thủ và tấn công",
                "Nhấn ESC để thoát về Menu chính"
            ]
        else:
            tips = [
                "P1 (XANH): Di chuyển = MŨI TÊN | Sút/Tắc = D | Chuyền = S",
                "P2 (ĐỎ): Di chuyển = WASD | Sút/Tắc = J | Chuyền = K",
                "Nhấn ESC để thoát về Menu chính"
            ]
            
        for i, tip in enumerate(tips):
            tip_surf = self.font_tip.render(tip, True, (190, 200, 210))
            screen.blit(tip_surf, (20, tip_y + i * 18))

    def draw_goal_celebration(self, screen):
        """Vẽ bảng hiệu ứng thông báo GOAL! cực lớn nhấp nháy khi ghi bàn."""
        # Làm tối mờ màn hình thi đấu phía sau để nổi bật thông báo ăn mừng
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Xác định đội ghi bàn để đổi màu chữ phù hợp
        team_name = "ĐỘI XANH (BLUE)" if self.scoring_team == 1 else "ĐỘI ĐỎ (RED)"
        text_color = COLOR_ACCENT_BLUE if self.scoring_team == 1 else COLOR_ACCENT
        
        # Nhấp nháy chữ GOAL! bằng hiệu ứng sin theo thời gian hệ thống
        blink = (pygame.time.get_ticks() // 150) % 2 == 0
        glow_color = COLOR_ACCENT_YELLOW if blink else COLOR_TEXT_LIGHT
        
        # 1. Vẽ dòng chữ "GOAL!" lớn phát sáng
        goal_text = "G O A L ! ! !"
        goal_surf = self.font_notice.render(goal_text, True, glow_color)
        goal_rect = goal_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        
        # Tạo bóng chữ phát sáng phía sau
        glow_surf = self.font_notice.render(goal_text, True, (20, 20, 20))
        screen.blit(glow_surf, goal_rect.move(5, 5))
        screen.blit(goal_surf, goal_rect)
        
        # 2. Vẽ thông tin đội bóng ghi bàn
        lbl_text = f"{team_name} GHI BÀN!"
        lbl_font = get_font(28, bold=True)
        lbl_surf = lbl_font.render(lbl_text, True, text_color)
        lbl_rect = lbl_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        
        # Vẽ thẻ nền mờ phía dưới dòng chữ đội ghi bàn
        bg_card_w = lbl_surf.get_width() + 40
        bg_card_rect = pygame.Rect(SCREEN_WIDTH // 2 - bg_card_w // 2, SCREEN_HEIGHT // 2 + 32, bg_card_w, 40)
        pygame.draw.rect(screen, COLOR_BG_UI, bg_card_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), bg_card_rect, 1, border_radius=6)
        screen.blit(lbl_surf, lbl_rect)

        # 3. Pháo hoa ăn mừng đơn giản bằng các hạt tròn nhỏ bắn tung tóe quanh màn hình
        random.seed(self.celebration_timer) # Giữ cho các hạt pháo hoa nhất quán trong suốt frames ăn mừng
        for _ in range(35):
            particle_x = SCREEN_WIDTH // 2 + random.randint(-200, 200)
            particle_y = SCREEN_HEIGHT // 2 + random.randint(-150, 150)
            color = random.choice([COLOR_ACCENT_YELLOW, COLOR_ACCENT_BLUE, COLOR_ACCENT, (255, 255, 255)])
            r = random.randint(4, 9)
            pygame.draw.circle(screen, color, (particle_x, particle_y), r)

    def draw(self, screen):
        # 1. Vẽ sân bóng
        self.draw_field(screen)
        
        # 2. Vẽ quả bóng (Vẽ bóng đổ của quả bóng trước để tạo cảm giác 3D nổi trên cỏ)
        ball_shadow_pos = (self.ball.rect.centerx + 4, self.ball.rect.centery + 4)
        pygame.draw.circle(screen, (20, 30, 20, 130), ball_shadow_pos, self.ball.radius)
        screen.blit(self.ball.image, self.ball.rect.topleft)
        
        # 2.5. Vẽ bóng đổ và các Trọng tài lên sân cỏ
        for ref in [self.referee, self.linesman_top, self.linesman_bottom]:
            if hasattr(ref, 'rect'):
                shadow_rect = pygame.Rect(ref.rect.x, ref.rect.bottom - 8, ref.rect.width, 10)
                pygame.draw.ellipse(screen, (20, 30, 20, 150), shadow_rect)
                ref.draw(screen)
        
        # 3. Vẽ các cầu thủ lên sân cỏ
        for player in self.players:
            # Vẽ bóng đổ hình elip màu đen mờ dưới chân cầu thủ trước
            shadow_rect = pygame.Rect(player.rect.x, player.rect.bottom - 8, player.rect.width, 10)
            pygame.draw.ellipse(screen, (20, 30, 20, 150), shadow_rect)
            
            # Vẽ cầu thủ chính đầy đủ tay chân hoạt họa chạy
            player.draw(screen)
            
            # Vẽ vòng tròn chỉ thị (Indicator) trên đầu cầu thủ do người điều khiển trực tiếp
            if isinstance(player, UserPlayer):
                color = COLOR_ACCENT_YELLOW if player.team_color == "blue" else COLOR_ACCENT_YELLOW
                player.draw_indicator(screen, color)

        # 4. Vẽ bảng tỉ số, thời gian (HUD)
        self.draw_hud(screen)

        # 5. Vẽ màn hình ăn mừng nếu có bàn thắng vừa được ghi
        if self.is_celebrating:
            self.draw_goal_celebration(screen)
            
        # 6. Vẽ thông báo biên / phạt góc nếu có
        if hasattr(self, 'out_of_bounds_timer') and self.out_of_bounds_timer > 0:
            self.draw_out_of_bounds_banner(screen)

    def check_out_of_bounds(self):
        """Kiểm tra xem bóng có vượt qua các đường biên sân không."""
        # Tránh kiểm tra khi bóng đang được giữ
        if self.ball.owner is not None:
            return

        # Xác định đội hưởng quyền đá phạt (là đội đối lập với đội chạm bóng cuối cùng)
        last_team = getattr(self.ball, 'last_touched_team', 'blue')
        benefiting_team = "red" if last_team == "blue" else "blue"
        
        # 1. Biên dọc (Touchline - top/bottom)
        if self.ball.y < FIELD_TOP or self.ball.y > FIELD_BOTTOM:
            self.out_of_bounds_timer = 70  # ~ 1.1 giây dừng trận đấu
            self.out_of_bounds_type = "touchline"
            self.out_of_bounds_team = benefiting_team
            self.banner_text = "NÉM BIÊN!"
            # Ghi nhận tọa độ bóng đi ra ngoài
            self.out_of_bounds_x = max(FIELD_LEFT + 25, min(FIELD_RIGHT - 25, self.ball.x))
            self.out_of_bounds_y = FIELD_TOP if self.ball.y < FIELD_TOP else FIELD_BOTTOM
            return

        # 2. Biên ngang (Goal line - left/right) và không ghi bàn
        in_goal_height = (GOAL_TOP <= self.ball.y <= GOAL_BOTTOM)
        if not in_goal_height and (self.ball.x < FIELD_LEFT or self.ball.x > FIELD_RIGHT):
            # Xác định xem bóng ra biên ngang phía bên nào
            is_left_side = self.ball.x < FIELD_LEFT
            
            # Đội phòng ngự và đội tấn công phía bên này
            if is_left_side:
                defending_team = "blue"
                attacking_team = "red"
            else:
                defending_team = "red"
                attacking_team = "blue"

            if last_team == attacking_team:
                # Tấn công chạm bóng cuối -> Phát bóng lên (Goal Kick) cho đội phòng ngự
                self.out_of_bounds_timer = 70
                self.out_of_bounds_type = "goal_kick"
                self.out_of_bounds_team = defending_team
                self.banner_text = "PHÁT BÓNG LÊN!"
            else:
                # Phòng ngự chạm bóng cuối -> Phạt góc (Corner Kick) cho đội tấn công
                self.out_of_bounds_timer = 70
                self.out_of_bounds_type = "corner_kick"
                self.out_of_bounds_team = attacking_team
                self.banner_text = "PHẠT GÓC!"
                
            self.out_of_bounds_x = FIELD_LEFT if is_left_side else FIELD_RIGHT
            self.out_of_bounds_y = FIELD_TOP if self.ball.y < CENTER_Y else FIELD_BOTTOM

    def resolve_out_of_bounds_restart(self):
        """Đặt bóng và định vị cầu thủ để thực hiện quả đá phạt biên / phạt góc / phát bóng lên."""
        team_list = self.blue_team if self.out_of_bounds_team == "blue" else self.red_team
        
        # Ngăn chặn quả bóng trôi
        self.ball.vx = 0.0
        self.ball.vy = 0.0
        
        if self.out_of_bounds_type == "touchline":
            # Đưa bóng về điểm biên dọc
            self.ball.x = self.out_of_bounds_x
            self.ball.y = self.out_of_bounds_y
            
            # Tìm cầu thủ gần nhất để ném biên (không tính thủ môn)
            kickers = [p for p in team_list if p.role != "goalkeeper"]
            if kickers:
                kicker = min(kickers, key=lambda p: p.get_distance_to(self.ball.x, self.ball.y))
                
                # Đặt cầu thủ ngay sau quả bóng
                kicker.x = self.ball.x
                kicker.y = self.ball.y + (18 if self.ball.y == FIELD_TOP else -18)
                kicker.vx = 0.0
                kicker.vy = 0.0
                
                # Định hướng cầu thủ quay về phía sân
                kicker.angle = math.pi/2 if self.ball.y == FIELD_TOP else -math.pi/2
                kicker.update_rotation()
                kicker.update_rect()
                
                # Trao bóng
                self.ball.owner = kicker
                kicker.has_ball_control = True
                kicker.kick_cooldown = 10

        elif self.out_of_bounds_type == "goal_kick":
            # Đặt bóng trong vòng cấm địa gôn nhà
            self.ball.x = FIELD_LEFT + 75 if self.out_of_bounds_team == "blue" else FIELD_RIGHT - 75
            self.ball.y = CENTER_Y
            
            # Thủ môn là người phát bóng
            if team_list:
                gk = team_list[0] # Thủ môn luôn ở vị trí đầu tiên
                gk.x = self.ball.x
                gk.y = self.ball.y
                gk.vx = 0.0
                gk.vy = 0.0
                gk.angle = 0.0 if self.out_of_bounds_team == "blue" else math.pi
                gk.update_rotation()
                gk.update_rect()
                
                self.ball.owner = gk
                gk.has_ball_control = True
                gk.kick_cooldown = 10

        elif self.out_of_bounds_type == "corner_kick":
            # Đặt bóng tại điểm phạt góc
            self.ball.x = self.out_of_bounds_x
            self.ball.y = self.out_of_bounds_y
            
            # Tìm cầu thủ gần nhất để phạt góc (thường là striker hoặc defender)
            kickers = [p for p in team_list if p.role != "goalkeeper"]
            if kickers:
                kicker = min(kickers, key=lambda p: p.get_distance_to(self.ball.x, self.ball.y))
                
                kicker.x = self.ball.x + (15 if self.ball.x == FIELD_LEFT else -15)
                kicker.y = self.ball.y + (15 if self.ball.y == FIELD_TOP else -15)
                kicker.vx = 0.0
                kicker.vy = 0.0
                
                # Quay hướng vào gôn đối diện
                target_goal_y = (GOAL_TOP + GOAL_BOTTOM) // 2
                target_goal_x = FIELD_RIGHT if self.out_of_bounds_team == "blue" else FIELD_LEFT
                kicker.angle = math.atan2(target_goal_y - kicker.y, target_goal_x - kicker.x)
                kicker.update_rotation()
                kicker.update_rect()
                
                self.ball.owner = kicker
                kicker.has_ball_control = True
                kicker.kick_cooldown = 10
            
        # Cập nhật vị trí bóng
        self.ball.update_rect()

    def draw_out_of_bounds_banner(self, screen):
        """Vẽ biểu ngữ thông báo bóng ra ngoài đường biên cực đẹp."""
        # 1. Vẽ dải nền tối mờ chạy ngang màn hình
        banner_h = 100
        banner_rect = pygame.Rect(0, SCREEN_HEIGHT // 2 - banner_h // 2 - 10, SCREEN_WIDTH, banner_h)
        
        # Vẽ hình chữ nhật trong suốt
        overlay = pygame.Surface((SCREEN_WIDTH, banner_h), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 220))
        screen.blit(overlay, (0, banner_rect.y))
        
        # Vẽ hai đường viền màu vàng gold
        pygame.draw.line(screen, COLOR_ACCENT_YELLOW, (0, banner_rect.top), (SCREEN_WIDTH, banner_rect.top), 2)
        pygame.draw.line(screen, COLOR_ACCENT_YELLOW, (0, banner_rect.bottom), (SCREEN_WIDTH, banner_rect.bottom), 2)
        
        # 2. Vẽ chữ thông báo phát sáng
        text_surf = self.font_notice.render(self.banner_text, True, COLOR_ACCENT_YELLOW)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
        
        # Hiệu ứng đổ bóng chữ phát sáng
        shadow_surf = self.font_notice.render(self.banner_text, True, (0, 0, 0))
        screen.blit(shadow_surf, text_rect.move(3, 3))
        screen.blit(text_surf, text_rect)
