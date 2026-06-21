# sprites/player_user.py
"""
Cầu thủ do người chơi điều khiển (User Player Class)
Xử lý các sự kiện nhấn phím từ bàn phím để di chuyển và sút bóng.
"""

import pygame
import math
from config import PLAYER_SPEED, PLAYER_FRICTION
from sprites.player import Player

class UserPlayer(Player):
    def __init__(self, team_color, number, role, start_x, start_y, controls):
        """
        Khởi tạo cầu thủ do người điều khiển.
        controls là dictionary chứa cấu hình phím:
        { 'up': key_code, 'down': key_code, 'left': key_code, 'right': key_code, 'kick': key_code }
        """
        super().__init__(team_color, number, role, start_x, start_y)
        self.controls = controls

    def handle_input(self, keys):
        """Đọc phím bấm từ bàn phím và gán vận tốc cho cầu thủ với quán tính mượt mà."""
        dx = 0
        dy = 0

        # Kiểm tra phím hướng
        if keys[self.controls['up']]:
            dy -= 1
        if keys[self.controls['down']]:
            dy += 1
        if keys[self.controls['left']]:
            dx -= 1
        if keys[self.controls['right']]:
            dx += 1

        # Chuẩn hóa vector di chuyển chéo để tốc độ luôn đồng đều
        if dx != 0 or dy != 0:
            target_angle = math.atan2(dy, dx)
            # Di chuyển mượt mà tăng dần vận tốc với quán tính cao hơn
            target_vx = math.cos(target_angle) * PLAYER_SPEED
            target_vy = math.sin(target_angle) * PLAYER_SPEED
            
            # Quán tính di chuyển (giảm hệ số để tăng độ mượt mà)
            self.vx += (target_vx - self.vx) * 0.18
            self.vy += (target_vy - self.vy) * 0.18
            
            # Nội suy góc xoay để nhân vật quay mặt mượt mà, không bị giật snaps
            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += angle_diff * 0.22
        else:
            # Tự động phanh khi nhả nút di chuyển
            self.vx *= PLAYER_FRICTION
            self.vy *= PLAYER_FRICTION
            if math.hypot(self.vx, self.vy) < 0.1:
                self.vx = 0.0
                self.vy = 0.0

    def update(self, keys, ball, teammates=None, opponents=None):
        """Cập nhật vị trí cầu thủ mỗi khung hình, xử lý chuyền, sút và tắc bóng."""
        self.handle_input(keys)
        
        # Cập nhật tọa độ
        self.x += self.vx
        self.y += self.vy
        
        # Xử lý va chạm biên sân bóng
        self.handle_collisions_with_walls()
        
        # Cập nhật xoay hình ảnh cầu thủ
        self.update_rotation()
        
        # Thử khống chế / rê bóng
        self.try_dribble(ball)
        
        # Tìm đồng đội gần nhất để chuẩn bị hướng chuyền bóng
        self.closest_teammate = None
        if teammates:
            min_dist = float('inf')
            for tm in teammates:
                if tm != self:
                    d = self.get_distance_to(tm.x, tm.y)
                    if d < min_dist:
                        min_dist = d
                        self.closest_teammate = tm
                        
        # Kiểm tra sút bóng (phím D) hoặc tắc bóng (phím D)
        if keys[self.controls['kick']]:
            if self.has_ball_control:
                self.kick_ball(ball)
            elif self.kick_cooldown == 0:
                # Logic tắc bóng (Tackle) khi đối thủ đang cầm bóng
                opponent_has_ball = False
                if opponents:
                    for opp in opponents:
                        if opp.has_ball_control:
                            opponent_has_ball = True
                            break
                            
                dist_to_ball = self.get_distance_to(ball.x, ball.y)
                # Chỉ cho phép tắc bóng khi ở cự ly tiếp cận
                if dist_to_ball < 120:
                    # Lao người lên phía trước (Lunge tackle)
                    self.vx += math.cos(self.angle) * 3.5
                    self.vy += math.sin(self.angle) * 3.5
                    
                    if dist_to_ball < 45:
                        # Tắc bóng thành công: Đá bóng văng ra xa
                        ball.owner = None
                        ball.last_touched_team = self.team_color
                        ball.kick(self.angle, force=10.0)
                        
                        # Cho đối thủ choáng ngắn và mất kiểm soát bóng
                        if opponents:
                            for opp in opponents:
                                opp.has_ball_control = False
                                opp.kick_cooldown = 30
                        self.kick_cooldown = 20

        # Kiểm tra chuyền bóng (phím S)
        if self.controls.get('pass') and keys[self.controls['pass']]:
            if self.has_ball_control and self.closest_teammate and self.kick_cooldown == 0:
                # Tính góc chuyền đến vị trí đồng đội gần nhất
                pass_angle = math.atan2(self.closest_teammate.y - ball.y, self.closest_teammate.x - ball.x)
                self.angle = pass_angle
                ball.owner = None
                ball.last_touched_team = self.team_color
                ball.kick(pass_angle, force=11.0)  # Lực chuyền trung bình mượt mà
                self.kick_cooldown = 25
                self.has_ball_control = False
            
        self.update_rect()

    def draw(self, screen):
        """Vẽ vòng tròn chỉ định và mũi tên hướng chuyền dưới chân khi giữ bóng."""
        if self.has_ball_control and getattr(self, 'closest_teammate', None):
            tm = self.closest_teammate
            # 1. Vẽ vòng tròn dưới chân màu vàng nổi bật
            pygame.draw.circle(screen, (241, 196, 15), (int(self.x), int(self.y)), 25, 2)
            
            # 2. Vẽ mũi tên hướng đến đồng đội
            dx = tm.x - self.x
            dy = tm.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                ux = dx / dist
                uy = dy / dist
                start_x = self.x + ux * 26
                start_y = self.y + uy * 26
                end_x = self.x + ux * 48
                end_y = self.y + uy * 48
                
                # Thân mũi tên
                pygame.draw.line(screen, (241, 196, 15), (int(start_x), int(start_y)), (int(end_x), int(end_y)), 3)
                
                # Đầu mũi tên tam giác
                arrow_angle = math.atan2(uy, ux)
                arrow_size = 8
                p1 = (end_x, end_y)
                p2 = (end_x - arrow_size * math.cos(arrow_angle - math.pi / 6), end_y - arrow_size * math.sin(arrow_angle - math.pi / 6))
                p3 = (end_x - arrow_size * math.cos(arrow_angle + math.pi / 6), end_y - arrow_size * math.sin(arrow_angle + math.pi / 6))
                pygame.draw.polygon(screen, (241, 196, 15), [p1, p2, p3])
                
        # Vẽ các thành phần của cầu thủ (Torso, tay, chân)
        super().draw(screen)
