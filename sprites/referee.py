# sprites/referee.py
"""
Lớp Trọng tài chính và Trọng tài biên (Referee and Linesman Classes)
"""

import pygame
import math
from config import (
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM,
    CENTER_X, CENTER_Y, PLAYER_RADIUS
)
from utils.asset_loader import load_player
from sprites.player import Player

class Referee(Player):
    def __init__(self):
        # Trọng tài chính dùng trang phục Special 1 (Áo sọc đen trắng)
        super().__init__("special", 1, "referee", CENTER_X, CENTER_Y - 120)
        self.target_x = CENTER_X
        self.target_y = CENTER_Y
        self.speed = 3.0

    def update(self, ball, players=None):
        """Trọng tài chính di chuyển bám sát bóng nhưng giữ cự ly an toàn với bóng và các cầu thủ."""
        dx = ball.x - self.x
        dy = ball.y - self.y
        dist = math.hypot(dx, dy)
        
        # 1. Tránh bóng (không đứng quá gần bóng)
        if dist < 100:
            # Di chuyển tránh ra xa bóng
            angle = math.atan2(dy, dx) + math.pi
            self.vx += (math.cos(angle) * self.speed - self.vx) * 0.12
            self.vy += (math.sin(angle) * self.speed - self.vy) * 0.12
        elif dist > 180:
            # Di chuyển đuổi theo bóng
            angle = math.atan2(dy, dx)
            self.vx += (math.cos(angle) * self.speed - self.vx) * 0.08
            self.vy += (math.sin(angle) * self.speed - self.vy) * 0.08
        else:
            # Đi chậm giữ khoảng cách
            angle = math.atan2(dy, dx)
            self.vx += (math.cos(angle) * (self.speed * 0.4) - self.vx) * 0.05
            self.vy += (math.sin(angle) * (self.speed * 0.4) - self.vy) * 0.05

        # 2. Tránh các cầu thủ trên sân (giữ khoảng cách tối thiểu 70px)
        if players:
            for player in players:
                p_dx = player.x - self.x
                p_dy = player.y - self.y
                p_dist = math.hypot(p_dx, p_dy)
                if p_dist < 75.0 and p_dist > 0:
                    # Hướng đẩy ra xa cầu thủ
                    repel_angle = math.atan2(p_dy, p_dx) + math.pi
                    # Lực đẩy tỷ lệ nghịch với khoảng cách
                    force = ((75.0 - p_dist) / 75.0) * self.speed
                    self.vx += (math.cos(repel_angle) * force - self.vx) * 0.15
                    self.vy += (math.sin(repel_angle) * force - self.vy) * 0.15
            
        self.x += self.vx
        self.y += self.vy
        
        # Giới hạn di chuyển trong biên sân
        margin = 35
        if self.x < FIELD_LEFT + margin: self.x = FIELD_LEFT + margin
        if self.x > FIELD_RIGHT - margin: self.x = FIELD_RIGHT - margin
        if self.y < FIELD_TOP + margin: self.y = FIELD_TOP + margin
        if self.y > FIELD_BOTTOM - margin: self.y = FIELD_BOTTOM - margin
        
        # Hướng mặt về phía bóng
        self.angle = math.atan2(ball.y - self.y, ball.x - self.x)
        self.update_rotation()
        self.update_rect()


class Linesman(Player):
    def __init__(self, is_top=True):
        # Trọng tài biên dùng trang phục Special 2
        y_pos = FIELD_TOP - 24 if is_top else FIELD_BOTTOM + 24
        super().__init__("special", 2, "linesman", CENTER_X, y_pos)
        self.is_top = is_top
        self.speed = 3.5

    def update(self, ball):
        """Trọng tài biên chạy dọc theo đường biên tương ứng với trục X của bóng."""
        self.target_x = ball.x
        if self.target_x < FIELD_LEFT: 
            self.target_x = FIELD_LEFT
        if self.target_x > FIELD_RIGHT: 
            self.target_x = FIELD_RIGHT
        
        dx = self.target_x - self.x
        self.vx += (dx * 0.12 - self.vx) * 0.15
        self.x += self.vx
        
        # Trọng tài biên luôn hướng mặt về phía quả bóng để quan sát
        self.angle = math.atan2(ball.y - self.y, ball.x - self.x)
        self.update_rotation()
        self.update_rect()
