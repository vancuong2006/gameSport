# sprites/player_ai.py
"""
Cầu thủ trí tuệ nhân tạo (AI Player Class)
Mô phỏng hành vi tự động cho Đồng đội và Đối thủ dựa trên vị trí bóng và Vai trò (Tiền đạo, Hậu vệ, Thủ môn).
"""

import pygame
import math
import random
from config import (
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM, FIELD_WIDTH, FIELD_HEIGHT,
    CENTER_X, CENTER_Y, GOAL_TOP, GOAL_BOTTOM,
    AI_SPEED, AI_GK_SPEED, DRIBBLE_DISTANCE, MAX_KICK_POWER
)
from sprites.player import Player

class AIPlayer(Player):
    def __init__(self, team_color, number, role, start_x, start_y, team_side):
        """
        Khởi tạo cầu thủ AI.
        team_side: "left" (phía trái sân, thường là Blue) hoặc "right" (phía phải sân, thường là Red)
        """
        super().__init__(team_color, number, role, start_x, start_y)
        self.team_side = team_side
        
        # Xác định gôn nhà và gôn đối phương
        if self.team_side == "left":
            self.own_goal_x = FIELD_LEFT
            self.opp_goal_x = FIELD_RIGHT
        else:
            self.own_goal_x = FIELD_RIGHT
            self.opp_goal_x = FIELD_LEFT
            
        self.opp_goal_y = (GOAL_TOP + GOAL_BOTTOM) // 2
        self.own_goal_y = (GOAL_TOP + GOAL_BOTTOM) // 2

        # Trạng thái AI
        self.state = "idle"  # idle, chase, return, defend, attack
        self.target_x = self.spawn_x
        self.target_y = self.spawn_y

    def steer_towards_target(self, speed_limit):
        """Tính toán vận tốc di chuyển hướng tới mục tiêu (Steering Behavior)."""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 8:
            # Hướng di chuyển
            self.vx += (dx / dist * speed_limit - self.vx) * 0.1
            self.vy += (dy / dist * speed_limit - self.vy) * 0.1
            self.angle = math.atan2(self.vy, self.vx)
        else:
            # Giảm tốc dần khi đã cận kề mục tiêu
            self.vx *= 0.8
            self.vy *= 0.8
            if math.hypot(self.vx, self.vy) < 0.1:
                self.vx = 0.0
                self.vy = 0.0

    def update(self, ball):
        """Cập nhật tư duy AI và chuyển động theo từng khung hình."""
        # 1. Định hình mục tiêu dựa trên vai trò cầu thủ và vị trí quả bóng
        if self.role == "goalkeeper":
            self.update_goalkeeper_logic(ball)
        elif self.role == "defender":
            self.update_defender_logic(ball)
        elif self.role == "striker":
            self.update_striker_logic(ball)

        # Cập nhật tọa độ di chuyển dựa trên vận tốc
        self.x += self.vx
        self.y += self.vy

        # 2. Rê dắt bóng và sút bóng nếu chạm bóng
        has_control = self.try_dribble(ball)
        if has_control:
            self.kick_decision(ball)

        # 3. Giới hạn di chuyển biên sân bóng
        self.handle_collisions_with_walls()
        
        # 4. Cập nhật góc xoay cầu thủ
        self.update_rotation()
        
        self.update_rect()

    def update_goalkeeper_logic(self, ball):
        """
        Logic thủ môn:
        - Bám sát trục dọc gôn nhà.
        - Di chuyển dọc theo trục Y để cản phá đường bóng.
        - Rút ra xa nếu bóng ở quá xa, lao lên phá bóng nếu bóng quá sát vòng cấm gôn.
        """
        # Vị trí trục X đứng cản phá (cách vạch gôn nhà 45px)
        if self.team_side == "left":
            self.target_x = FIELD_LEFT + 45
        else:
            self.target_x = FIELD_RIGHT - 45
            
        # Theo dõi bóng theo trục Y nhưng giới hạn trong khung thành
        self.target_y = ball.y
        if self.target_y < GOAL_TOP - 15:
            self.target_y = GOAL_TOP - 15
        elif self.target_y > GOAL_BOTTOM + 15:
            self.target_y = GOAL_BOTTOM + 15
            
        # Nếu bóng ở quá gần khung thành (trong bán kính 140px), thủ môn lao lên phá bóng giải nguy
        dist_to_ball = self.get_distance_to(ball.x, ball.y)
        if dist_to_ball < 140:
            self.target_x = ball.x
            self.target_y = ball.y
            self.steer_towards_target(AI_SPEED)  # Lao lên nhanh hơn bình thường
        else:
            self.steer_towards_target(AI_GK_SPEED) # Giữ vị trí cản phá bằng tốc độ gôn

    def update_defender_logic(self, ball):
        """
        Logic hậu vệ năng động:
        - Luôn dâng cao hỗ trợ tấn công hoặc áp sát cướp bóng nếu bóng ở gần (dưới 300px).
        - Nếu bóng ở sâu phần sân nhà, lao ra tranh bóng quyết liệt.
        - Nếu bóng ở xa bên phần sân đối phương, dâng lên giữa sân giữ khoảng cách hỗ trợ.
        """
        dist_to_ball = self.get_distance_to(ball.x, ball.y)
        
        # Kiểm tra xem bóng có ở bên phần sân nhà không
        ball_in_own_half = False
        if self.team_side == "left":
            ball_in_own_half = (ball.x < CENTER_X)
        else:
            ball_in_own_half = (ball.x > CENTER_X)
            
        # Hậu vệ sẽ lao lên cướp bóng nếu bóng ở phần sân nhà HOẶC bóng ở cự ly gần dưới 300px
        if ball_in_own_half or dist_to_ball < 300:
            self.target_x = ball.x
            self.target_y = ball.y
            self.steer_towards_target(AI_SPEED)
        else:
            # Nếu bóng ở quá xa phần sân khách, dâng lên đứng ở vị trí bọc lót giữa sân
            own_goal_center_x = FIELD_LEFT if self.team_side == "left" else FIELD_RIGHT
            
            # Vị trí đứng hỗ trợ (giữa bóng và gôn nhà, dâng cao bám theo bóng)
            self.target_x = (ball.x * 0.4 + own_goal_center_x * 0.6)
            self.target_y = (ball.y * 0.4 + CENTER_Y * 0.6)
            
            # Giới hạn hậu vệ không dâng quá sâu vào vòng cấm đối phương
            if self.team_side == "left" and self.target_x > CENTER_X + 100:
                self.target_x = CENTER_X + 100
            elif self.team_side == "right" and self.target_x < CENTER_X - 100:
                self.target_x = CENTER_X - 100
                
            self.steer_towards_target(AI_SPEED * 0.85)

    def update_striker_logic(self, ball):
        """
        Logic tiền đạo:
        - Luôn bám sát, săn đuổi bóng để tranh chấp.
        - Nếu giữ bóng, di chuyển thẳng về khung thành đối thủ để sút gôn.
        """
        if self.has_ball_control:
            # Rê bóng thẳng về gôn đối diện
            self.target_x = self.opp_goal_x
            self.target_y = self.opp_goal_y
            
            # Cầu thủ hướng thẳng về phía gôn
            self.angle = math.atan2(self.opp_goal_y - self.y, self.opp_goal_x - self.x)
            
            # Tiến lên
            self.vx = math.cos(self.angle) * AI_SPEED
            self.vy = math.sin(self.angle) * AI_SPEED
        else:
            # Không giữ bóng -> Chạy theo cướp bóng
            self.target_x = ball.x
            self.target_y = ball.y
            self.steer_towards_target(AI_SPEED)

    def kick_decision(self, ball):
        """
        Đưa ra quyết định sút bóng cho AI:
        - Tiền đạo: Sút thẳng về phía gôn đối thủ nếu trong cự ly thuận lợi.
        - Hậu vệ / Thủ môn: Sút thật mạnh phá bóng lên phía phần sân đối phương.
        """
        if self.role == "striker":
            # Kiểm tra khoảng cách tới khung thành đối phương
            dist_to_goal = math.hypot(self.opp_goal_x - self.x, self.opp_goal_y - self.y)
            
            # Hướng sút nhắm vào gôn đối diện
            # Thêm một chút ngẫu nhiên để thủ môn đối thủ khó phán đoán hơn (nhắm góc cao, góc thấp)
            target_y_offset = random.randint(-40, 40)
            self.angle = math.atan2((self.opp_goal_y + target_y_offset) - self.y, self.opp_goal_x - self.x)
            
            if dist_to_goal < FIELD_WIDTH * 0.5:
                # Sút căng
                self.kick_ball(ball, force=MAX_KICK_POWER - random.uniform(0.5, 2.0))
            else:
                # Rê dắt tiếp hoặc sút nhẹ hơn
                self.kick_ball(ball, force=MAX_KICK_POWER * 0.7)
        else:
            # Hậu vệ / Thủ môn: Sút giải nguy phá bóng lên trên
            # Sút xiên chéo lên phần sân đối phương để đồng đội tranh chấp
            target_y = random.randint(FIELD_TOP + 50, FIELD_BOTTOM - 50)
            self.angle = math.atan2(target_y - self.y, self.opp_goal_x - self.x)
            self.kick_ball(ball, force=MAX_KICK_POWER)
