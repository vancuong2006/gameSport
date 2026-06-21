# utils/asset_loader.py
"""
Hệ thống tải tài nguyên hình ảnh (Asset Loader)
Tự động tải các tệp từ thư mục kenney_sports-pack, tự động thu nhỏ/phóng to
và cung cấp cơ chế dự phòng (fallback) vẽ bằng Vector vẽ đồ họa nếu thiếu tệp.
"""

import os
import pygame
import math
from config import PNG_DIR, COLOR_ACCENT_BLUE, COLOR_ACCENT, COLOR_LINE

# Cache lưu trữ ảnh để tránh nạp đi nạp lại làm giảm hiệu năng
_image_cache = {}

def get_fallback_player(color_tuple, size=(44, 44)):
    """Tạo sprite cầu thủ dự phòng nếu không tải được ảnh."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(surface, color_tuple, (size[0] // 2, size[1] // 2), size[0] // 2 - 2)
    pygame.draw.circle(surface, (255, 255, 255), (size[0] // 2, size[1] // 2), size[0] // 2 - 2, 2)
    # Vẽ mũi tên hướng (mặc định quay sang phải)
    center_x, center_y = size[0] // 2, size[1] // 2
    arrow_len = size[0] // 2 - 4
    pygame.draw.line(surface, (255, 255, 255), (center_x, center_y), (center_x + arrow_len, center_y), 3)
    pygame.draw.polygon(surface, (255, 255, 255), [
        (center_x + arrow_len, center_y - 4),
        (center_x + arrow_len + 4, center_y),
        (center_x + arrow_len, center_y + 4)
    ])
    return surface

def get_fallback_ball(radius=12):
    """Tạo sprite bóng dự phòng."""
    size = radius * 2
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surface, (255, 255, 255), (radius, radius), radius)
    pygame.draw.circle(surface, (0, 0, 0), (radius, radius), radius, 2)
    # Vẽ vài nét đứt giả quả bóng đá
    pygame.draw.circle(surface, (0, 0, 0), (radius, radius), radius // 2, 1)
    return surface

def load_image(relative_path, scale=None):
    """Nạp một hình ảnh đơn lẻ từ đường dẫn và lưu vào cache, giữ tỷ lệ aspect ratio."""
    # Chuyển đổi thành khóa cache
    cache_key = (relative_path, scale)
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    full_path = os.path.join(PNG_DIR, relative_path)
    
    try:
        if os.path.exists(full_path):
            image = pygame.image.load(full_path).convert_alpha()
            if scale:
                # scale là (max_w, max_h)
                orig_rect = image.get_rect()
                orig_w, orig_h = orig_rect.width, orig_rect.height
                target_w, target_h = scale
                
                # Tính toán tỷ lệ co giãn để giữ nguyên tỷ lệ khung hình (Aspect Ratio)
                ratio_w = target_w / orig_w
                ratio_h = target_h / orig_h
                ratio = min(ratio_w, ratio_h)
                
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                image = pygame.transform.smoothscale(image, (new_w, new_h))
                
            _image_cache[cache_key] = image
            return image
        else:
            # print(f"Không tìm thấy ảnh tại: {full_path}. Đang sử dụng hình ảnh mặc định.")
            return None
    except Exception as e:
        print(f"Lỗi khi nạp ảnh {full_path}: {e}")
        return None

def get_font(size, bold=False, italic=False):
    """
    Tải font chữ hệ thống hỗ trợ tốt tiếng Việt Unicode (Segoe UI, Calibri, Tahoma, Arial).
    """
    # Trả về đối tượng font hệ thống hỗ trợ tốt tiếng Việt
    return pygame.font.SysFont(["Segoe UI", "Calibri", "Tahoma", "Arial"], size, bold, italic)

def load_player(team_color, index=1, size=(44, 44), raw=False):
    """
    Nạp sprite cầu thủ dựa trên màu đội (Blue, Red, Green, White) và index (1-14).
    Nếu raw=False và index <= 10, tự động ghép Torso, Tay và Chân thành một ảnh hoàn chỉnh.
    Tự động fallback vẽ hình tròn nếu lỗi nạp ảnh.
    """
    team_folder = team_color.capitalize()
    
    if raw or index > 10:
        filename = f"character{team_folder} ({index}).png"
        relative_path = os.path.join(team_folder, filename)
        
        img = load_image(relative_path, size)
        if img:
            return img
        
        # Tạo dự phòng nếu lỗi
        fallback_color = COLOR_ACCENT_BLUE if team_color.lower() == "blue" else COLOR_ACCENT
        if team_color.lower() == "green":
            fallback_color = (46, 204, 113)
        elif team_color.lower() == "white":
            fallback_color = (236, 240, 241)
            
        return get_fallback_player(fallback_color, size)

    # Lắp ghép composite (Thân + Tay + Chân)
    w, h = size
    f = w / 44.0  # Tỷ lệ co giãn dựa trên kích thước chuẩn 44
    
    # Nạp các thành phần đơn lẻ (dùng raw=True để tránh đệ quy vô hạn)
    body_img = load_player(team_color, index, (int(28 * f), int(40 * f)), raw=True)
    hand_img = load_player(team_color, 11, (int(16 * f), int(16 * f)), raw=True)
    # Lật ngang ảnh bàn tay để quay về phía trước (mặc định hướng trái)
    if hand_img:
        hand_img = pygame.transform.flip(hand_img, True, False)
    foot_img = load_player(team_color, 13, (int(16 * f), int(16 * f)), raw=True)
    
    # Tạo Surface ghép trong suốt
    composite = pygame.Surface(size, pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    
    # 1. Vẽ hai chân phía dưới thân người (về phía sau lưng)
    if foot_img:
        # Chân trái (Left foot)
        fl_rect = foot_img.get_rect(center=(int(cx - 10 * f), int(cy - 8 * f)))
        composite.blit(foot_img, fl_rect.topleft)
        # Chân phải (Right foot)
        fr_rect = foot_img.get_rect(center=(int(cx - 10 * f), int(cy + 8 * f)))
        composite.blit(foot_img, fr_rect.topleft)
        
    # 2. Vẽ thân mình
    if body_img:
        body_rect = body_img.get_rect(center=(cx, cy))
        composite.blit(body_img, body_rect.topleft)
        
    # 3. Vẽ hai tay hai bên vai (vươn về phía trước mặt)
    if hand_img:
        # Tay trái (Left hand)
        hl_rect = hand_img.get_rect(center=(int(cx + 8 * f), int(cy - 13 * f)))
        composite.blit(hand_img, hl_rect.topleft)
        # Tay phải (Right hand)
        hr_rect = hand_img.get_rect(center=(int(cx + 8 * f), int(cy + 13 * f)))
        composite.blit(hand_img, hr_rect.topleft)
        
    return composite

def load_ball(radius=12):
    """Nạp ảnh quả bóng đá."""
    # ball_soccer1.png là quả bóng tiêu chuẩn đen trắng
    img = load_image(os.path.join("Equipment", "ball_soccer1.png"), (radius * 2, radius * 2))
    if img:
        return img
    return get_fallback_ball(radius)

def load_ui_element(element_index, size=None):
    """Nạp các phần tử đồ họa khác như khung thành hoặc thẻ phạt trong thư mục Elements."""
    filename = f"element ({element_index}).png"
    return load_image(os.path.join("Elements", filename), size)

def load_equipment(filename, size=None):
    """Nạp các thiết bị thể thao khác như thẻ phạt, còi..."""
    return load_image(os.path.join("Equipment", filename), size)
