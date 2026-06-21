# sprites/ball.py
"""
Đối tượng Quả bóng (Ball Class)
Quản lý vị trí, vận tốc, ma sát, va chạm biên sân, va chạm cột dọc khung thành và phát hiện ghi bàn.
"""

import pygame
import math
import random
from config import (
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM,
    CENTER_X, CENTER_Y, GOAL_TOP, GOAL_BOTTOM, GOAL_DEPTH,
    BALL_RADIUS, BALL_FRICTION, BOUNCE_COEFF
)
from utils.asset_loader import load_ball

class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.radius = BALL_RADIUS
        self.base_image = load_ball(self.radius)
        self.image = self.base_image
        self.rect = self.image.get_rect()
        
        # Tọa độ thực dạng số thực để di chuyển mượt mà
        self.x = float(CENTER_X)
        self.y = float(CENTER_Y)
        
        # Vận tốc theo 2 trục
        self.vx = 0.0
        self.vy = 0.0
        
        # Góc xoay hiển thị quả bóng (tạo hiệu ứng lăn)
        self.angle = 0.0
        self.owner = None
        self.last_touched_team = "blue"
        
        # Cập nhật vị trí ban đầu
        self.update_rect()

    def reset(self, x=CENTER_X, y=CENTER_Y):
        """Đặt bóng lại vị trí chỉ định và triệt tiêu vận tốc."""
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.owner = None
        self.last_touched_team = "blue"
        self.update_rect()

    def update_rect(self):
        """Cập nhật rect từ tọa độ số thực float."""
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def kick(self, angle, force):
        """Áp dụng lực sút bóng theo góc xác định."""
        self.vx += math.cos(angle) * force
        self.vy += math.sin(angle) * force
        
        # Giới hạn vận tốc tối đa tránh xuyên tường
        speed = math.hypot(self.vx, self.vy)
        if speed > 22.0:
            self.vx = (self.vx / speed) * 22.0
            self.vy = (self.vy / speed) * 22.0

    def update(self):
        """Cập nhật chuyển động và xử lý va chạm biên."""
        if self.owner is not None:
            # Khóa bóng dính chặt vào chân của chủ sở hữu
            self.x = self.owner.x + math.cos(self.owner.angle) * (self.owner.radius + self.radius - 1)
            self.y = self.owner.y + math.sin(self.owner.angle) * (self.owner.radius + self.radius - 1)
            self.vx = self.owner.vx
            self.vy = self.owner.vy
            
            # Tạo hiệu ứng xoay nhẹ tương ứng khi rê bóng
            speed = math.hypot(self.vx, self.vy)
            if speed > 0.2:
                rotation_speed = speed * 1.5
                if self.vx < 0:
                    self.angle += rotation_speed
                else:
                    self.angle -= rotation_speed
                self.image = pygame.transform.rotate(self.base_image, self.angle)
                old_center = self.rect.center
                self.rect = self.image.get_rect()
                self.rect.center = old_center
                
            self.update_rect()
            return

        # Di chuyển theo vận tốc
        self.x += self.vx
        self.y += self.vy
        
        # Áp dụng lực ma sát mặt cỏ
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION
        
        # Dừng hẳn nếu vận tốc quá nhỏ
        if math.hypot(self.vx, self.vy) < 0.1:
            self.vx = 0.0
            self.vy = 0.0
            
        # Tạo hiệu ứng xoay bóng tương ứng với vận tốc
        speed = math.hypot(self.vx, self.vy)
        if speed > 0.2:
            # Xoay theo chiều di chuyển
            rotation_speed = speed * 1.5
            # Xác định chiều xoay (tùy thuộc hướng chuyển động)
            if self.vx < 0:
                self.angle += rotation_speed
            else:
                self.angle -= rotation_speed
            
            # Xoay ảnh
            self.image = pygame.transform.rotate(self.base_image, self.angle)
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center

        # Xử lý va chạm biên sân bóng
        self.handle_boundary_collisions()
        self.update_rect()

    def handle_boundary_collisions(self):
        """Xử lý va chạm với biên sân và khung thành (cho phép bóng ra ngoài biên một chút)."""
        # 1. Va chạm biên trên/dưới ngoài sân (block ở cự ly 35px ngoài đường biên)
        if self.y - self.radius < FIELD_TOP - 35:
            self.y = FIELD_TOP - 35 + self.radius
            self.vy = -self.vy * BOUNCE_COEFF
            self.vx *= 0.95
            
        elif self.y + self.radius > FIELD_BOTTOM + 35:
            self.y = FIELD_BOTTOM + 35 - self.radius
            self.vy = -self.vy * BOUNCE_COEFF
            self.vx *= 0.95

        # 2. Va chạm biên trái/phải và khung thành
        in_goal_height = (GOAL_TOP <= self.y <= GOAL_BOTTOM)

        # Biên Trái (x = FIELD_LEFT) ngoài sân
        if self.x - self.radius < FIELD_LEFT - 40:
            if in_goal_height:
                # Bóng đang đi vào lưới gôn trái
                if self.x - self.radius < FIELD_LEFT - GOAL_DEPTH:
                    self.x = FIELD_LEFT - GOAL_DEPTH + self.radius
                    self.vx = -self.vx * 0.3
                
                # Giới hạn trên/dưới của lưới
                if self.y - self.radius < GOAL_TOP:
                    self.y = GOAL_TOP + self.radius
                    self.vy = -self.vy * BOUNCE_COEFF
                elif self.y + self.radius > GOAL_BOTTOM:
                    self.y = GOAL_BOTTOM - self.radius
                    self.vy = -self.vy * BOUNCE_COEFF
            else:
                # Chặn bóng ở cự ly 40px ngoài vạch gôn để trọng tài thổi phạt biên ngang
                self.x = FIELD_LEFT - 40 + self.radius
                self.vx = -self.vx * BOUNCE_COEFF
                self.vy *= 0.95

        # Biên Phải (x = FIELD_RIGHT) ngoài sân
        elif self.x + self.radius > FIELD_RIGHT + 40:
            if in_goal_height:
                # Bóng đang đi vào lưới gôn phải
                if self.x + self.radius > FIELD_RIGHT + GOAL_DEPTH:
                    self.x = FIELD_RIGHT + GOAL_DEPTH - self.radius
                    self.vx = -self.vx * 0.3
                
                if self.y - self.radius < GOAL_TOP:
                    self.y = GOAL_TOP + self.radius
                    self.vy = -self.vy * BOUNCE_COEFF
                elif self.y + self.radius > GOAL_BOTTOM:
                    self.y = GOAL_BOTTOM - self.radius
                    self.vy = -self.vy * BOUNCE_COEFF
            else:
                self.x = FIELD_RIGHT + 40 - self.radius
                self.vx = -self.vx * BOUNCE_COEFF
                self.vy *= 0.95

        # 3. Va chạm cột dọc khung thành (4 điểm cột dọc gôn)
        # Các cột dọc nằm tại:
        # Cột trái trên: (FIELD_LEFT, GOAL_TOP)
        # Cột trái dưới: (FIELD_LEFT, GOAL_BOTTOM)
        # Cột phải trên: (FIELD_RIGHT, GOAL_TOP)
        # Cột phải dưới: (FIELD_RIGHT, GOAL_BOTTOM)
        posts = [
            (FIELD_LEFT, GOAL_TOP),
            (FIELD_LEFT, GOAL_BOTTOM),
            (FIELD_RIGHT, GOAL_TOP),
            (FIELD_RIGHT, GOAL_BOTTOM)
        ]
        
        post_radius = 6.0  # Độ dày cột gôn giả lập hình tròn nhỏ
        for px, py in posts:
            dist = math.hypot(self.x - px, self.y - py)
            min_dist = self.radius + post_radius
            if dist < min_dist:
                # Tính toán hướng đẩy ra và góc phản xạ vật lý
                if dist == 0:  # Tránh lỗi chia cho 0
                    dx, dy = 1, 0
                    dist = 1
                else:
                    dx = (self.x - px) / dist
                    dy = (self.y - py) / dist
                
                # Đẩy bóng ra khỏi cột dọc
                self.x = px + dx * min_dist
                self.y = py + dy * min_dist
                
                # Tính phản xạ vận tốc
                dot_product = self.vx * dx + self.vy * dy
                if dot_product < 0: # Chỉ nảy nếu bóng đang chuyển động hướng vào cột
                    self.vx = (self.vx - 2 * dot_product * dx) * BOUNCE_COEFF
                    self.vy = (self.vy - 2 * dot_product * dy) * BOUNCE_COEFF

    def check_goal(self):
        """
        Kiểm tra xem bóng đã đi hẳn qua vạch vôi vào lưới chưa.
        Trả về:
            1: Ghi bàn vào lưới Trái (đội Phải ghi bàn)
            2: Ghi bàn vào lưới Phải (đội Trái ghi bàn)
            0: Chưa ghi bàn
        """
        # Quả bóng phải chui vào hoàn toàn (tâm bóng + bán kính qua vạch gôn)
        if GOAL_TOP <= self.y <= GOAL_BOTTOM:
            if self.x + self.radius < FIELD_LEFT:
                return 1  # Lưới trái bị ghi bàn -> Đội 2 ghi bàn
            elif self.x - self.radius > FIELD_RIGHT:
                return 2  # Lưới phải bị ghi bàn -> Đội 1 ghi bàn
        return 0
