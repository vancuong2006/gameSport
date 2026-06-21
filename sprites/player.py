# sprites/player.py
"""
Lớp Cầu thủ Cơ sở (Base Player Class)
Quản lý trạng thái di chuyển, góc xoay, va chạm sân bóng và các thao tác cơ bản với bóng như khống chế và sút.
"""

import pygame
import math
from config import (
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM,
    PLAYER_RADIUS, PLAYER_FRICTION, PLAYER_SPEED, DRIBBLE_DISTANCE, MAX_KICK_POWER
)
from utils.asset_loader import load_player

class Player(pygame.sprite.Sprite):
    def __init__(self, team_color, number, role, start_x, start_y):
        super().__init__()
        self.team_color = team_color.lower()
        self.number = number  # Dùng để chọn file ảnh (1 - 14)
        self.role = role      # "striker", "defender", "goalkeeper"
        
        self.radius = PLAYER_RADIUS
        
        # Nạp các phần thể cầu thủ để vẽ chi tiết (Torso, Hand, Foot)
        self.body_img = load_player(self.team_color, self.number, (int(self.radius * 2.0 * (28/44)), int(self.radius * 2.0 * (40/44))), raw=True)
        self.hand_img = load_player(self.team_color, 11, (int(self.radius * 2.0 * (16/44)), int(self.radius * 2.0 * (16/44))), raw=True)
        # Lật ngang ảnh bàn tay để quay về phía trước
        if self.hand_img:
            self.hand_img = pygame.transform.flip(self.hand_img, True, False)
        self.foot_img = load_player(self.team_color, 13, (int(self.radius * 2.0 * (16/44)), int(self.radius * 2.0 * (16/44))), raw=True)
        
        # Để duy trì tính tương thích với sprite group
        self.base_image = load_player(self.team_color, self.number, (self.radius * 2, self.radius * 2))
        self.image = self.base_image
        self.rect = self.image.get_rect()
        
        # Trạng thái hoạt ảnh chạy
        self.walk_phase = 0.0
        
        # Tọa độ thực dạng số thực
        self.x = float(start_x)
        self.y = float(start_y)
        
        # Vận tốc di chuyển
        self.vx = 0.0
        self.vy = 0.0
        
        # Hướng cầu thủ đang đối mặt (dạng radian, mặc định quay sang phải nếu ở đội trái và ngược lại)
        self.angle = 0.0 if self.team_color == "blue" else math.pi
        
        # Trạng thái giữ bóng và sút
        self.has_ball_control = False
        self.kick_cooldown = 0
        
        # Lưu trữ điểm hồi sinh ban đầu
        self.spawn_x = start_x
        self.spawn_y = start_y

        self.update_rect()

    def reset(self):
        """Đặt cầu thủ về vị trí xuất phát ban đầu."""
        self.x = float(self.spawn_x)
        self.y = float(self.spawn_y)
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0 if self.team_color == "blue" else math.pi
        self.has_ball_control = False
        self.kick_cooldown = 0
        self.update_rect()

    def update_rect(self):
        """Cập nhật rect hiển thị từ tọa độ số thực."""
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def handle_collisions_with_walls(self):
        """Giới hạn cầu thủ trong biên sân bóng."""
        # Giới hạn x biên trái/phải
        if self.x - self.radius < FIELD_LEFT:
            self.x = FIELD_LEFT + self.radius
            self.vx = 0
        elif self.x + self.radius > FIELD_RIGHT:
            self.x = FIELD_RIGHT - self.radius
            self.vx = 0

        # Giới hạn y biên trên/dưới
        if self.y - self.radius < FIELD_TOP:
            self.y = FIELD_TOP + self.radius
            self.vy = 0
        elif self.y + self.radius > FIELD_BOTTOM:
            self.y = FIELD_BOTTOM - self.radius
            self.vy = 0

    def get_distance_to(self, target_x, target_y):
        """Tính khoảng cách đến một tọa độ mục tiêu."""
        return math.hypot(target_x - self.x, target_y - self.y)

    def update_rotation(self):
        """Xoay ảnh cầu thủ theo hướng di chuyển hiện tại hoặc hướng bóng và cập nhật hoạt ảnh chạy."""
        # Nếu đang có chuyển động, hướng cầu thủ theo hướng di chuyển
        speed = math.hypot(self.vx, self.vy)
        if speed > 0.2:
            self.angle = math.atan2(self.vy, self.vx)
            self.walk_phase += speed * 0.15  # Cập nhật pha bước chạy
            
        # Xoay hình ảnh (Kenney sprites mặc định hướng sang phải)
        # Pygame xoay ngược chiều kim đồng hồ nên cần đổi dấu góc
        deg = -math.degrees(self.angle)
        self.image = pygame.transform.rotate(self.base_image, deg)
        
        # Cập nhật lại center rect để tránh nhảy hình
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center

    def try_dribble(self, ball):
        """
        Kiểm tra và xử lý khống chế/rê bóng dính chân.
        Chỉ rời chân khi sút bóng, chuyền hoặc đối phương cướp bóng ở cự ly gần.
        """
        if self.kick_cooldown > 0:
            self.kick_cooldown -= 1
            return False

        # Nếu mình đang giữ bóng -> Giữ chặt bóng không cho rơi ra
        if ball.owner == self:
            self.has_ball_control = True
            ball.last_touched_team = self.team_color
            return True

        # Nếu bóng đang có chủ khác -> Cho phép áp sát để cướp bóng
        if ball.owner is not None and ball.owner != self:
            dist_to_owner = self.get_distance_to(ball.owner.x, ball.owner.y)
            # Cướp bóng nếu ở cự ly tiếp cận 36px và không trong thời gian choáng
            if dist_to_owner < 36.0:
                old_owner = ball.owner
                old_owner.has_ball_control = False
                old_owner.kick_cooldown = 20  # Cho đối phương thời gian hồi cướp bóng
                
                ball.owner = self
                self.has_ball_control = True
                self.kick_cooldown = 10
                ball.last_touched_team = self.team_color
                return True

        # Nếu bóng chưa có ai giữ (bóng tự do)
        if ball.owner is None:
            dist = self.get_distance_to(ball.x, ball.y)
            if dist < DRIBBLE_DISTANCE:
                ball.owner = self
                self.has_ball_control = True
                ball.last_touched_team = self.team_color
                return True

        self.has_ball_control = False
        return False

    def kick_ball(self, ball, force=MAX_KICK_POWER):
        """Sút bóng theo hướng đối mặt của cầu thủ."""
        dist = self.get_distance_to(ball.x, ball.y)
        
        # Có thể sút nếu bóng ở trong phạm vi rê bóng hoặc mình đang cầm bóng
        if dist < DRIBBLE_DISTANCE + 5 or ball.owner == self:
            # Giải phóng chủ sở hữu bóng trước khi sút bay đi
            ball.owner = None
            ball.last_touched_team = self.team_color
            ball.kick(self.angle, force)
            self.kick_cooldown = 15  # Đặt thời gian hồi sút bóng để tránh dính bóng lại ngay lập tức
            self.has_ball_control = False
            return True
        return False

    def draw_indicator(self, surface, color):
        """Vẽ một chỉ thị hình tam giác nhỏ trên đầu cầu thủ được chọn điều khiển."""
        # Chỉ thị hình tam giác nhỏ trên đầu cầu thủ
        indicator_y = self.rect.top - 12
        points = [
            (self.rect.centerx - 6, indicator_y),
            (self.rect.centerx + 6, indicator_y),
            (self.rect.centerx, indicator_y + 8)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 1)

    def draw(self, screen):
        """Vẽ cầu thủ đầy đủ tay chân và hoạt ảnh chạy sống động."""
        speed = math.hypot(self.vx, self.vy)
        # Biên độ dao động chân khi chạy, nếu đứng yên thì chân mở cố định
        swing = math.sin(self.walk_phase) * 6 if speed > 0.2 else 0.0
        
        # Tính toán góc xoay
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        
        f = (self.radius * 2) / 44.0
        
        # 1. Tính toán vị trí chân (Feet)
        lf_local_x = -10 * f + swing
        lf_local_y = -8 * f
        lf_x = self.x + (lf_local_x * cos_a - lf_local_y * sin_a)
        lf_y = self.y + (lf_local_x * sin_a + lf_local_y * cos_a)
        
        rf_local_x = -10 * f - swing
        rf_local_y = 8 * f
        rf_x = self.x + (rf_local_x * cos_a - rf_local_y * sin_a)
        rf_y = self.y + (rf_local_x * sin_a + rf_local_y * cos_a)
        
        # Vẽ chân
        if self.foot_img:
            self.draw_rotated_component(screen, self.foot_img, lf_x, lf_y)
            self.draw_rotated_component(screen, self.foot_img, rf_x, rf_y)
            
        # 2. Vẽ thân mình (Body)
        if self.body_img:
            self.draw_rotated_component(screen, self.body_img, self.x, self.y)
            
        # 3. Tính toán vị trí tay (Hands - đưa về phía trước vai)
        lh_local_x = 8 * f - swing * 0.3
        lh_local_y = -13 * f
        lh_x = self.x + (lh_local_x * cos_a - lh_local_y * sin_a)
        lh_y = self.y + (lh_local_x * sin_a + lh_local_y * cos_a)
        
        rh_local_x = 8 * f + swing * 0.3
        rh_local_y = 13 * f
        rh_x = self.x + (rh_local_x * cos_a - rh_local_y * sin_a)
        rh_y = self.y + (rh_local_x * sin_a + rh_local_y * cos_a)
        
        # Vẽ tay
        if self.hand_img:
            self.draw_rotated_component(screen, self.hand_img, lh_x, lh_y)
            self.draw_rotated_component(screen, self.hand_img, rh_x, rh_y)
            
    def draw_rotated_component(self, screen, base_img, center_x, center_y):
        """Xoay và vẽ một phần thể của cầu thủ."""
        deg = -math.degrees(self.angle)
        rot_img = pygame.transform.rotate(base_img, deg)
        rect = rot_img.get_rect(center=(int(center_x), int(center_y)))
        screen.blit(rot_img, rect.topleft)
