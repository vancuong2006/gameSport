# states/state_manager.py
"""
Trình quản lý trạng thái trò chơi (State Manager)
Điều phối chuyển cảnh giữa Menu chính, Trận đấu đang diễn ra và Màn hình kết thúc.
"""

class StateManager:
    def __init__(self, screen):
        self.screen = screen
        self.states = {}
        self.current_state = None

    def register_state(self, name, state_object):
        """Đăng ký một trạng thái mới vào bộ quản lý."""
        self.states[name] = state_object
        state_object.manager = self

    def change_state(self, name, **kwargs):
        """Chuyển đổi sang trạng thái được chỉ định và truyền tham số nếu cần."""
        if name in self.states:
            self.current_state = self.states[name]
            # Gọi hàm khởi động của trạng thái đó với các tham số truyền thêm
            self.current_state.startup(**kwargs)
        else:
            print(f"Trạng thái {name} chưa được đăng ký.")

    def handle_events(self, events):
        """Truyền sự kiện bàn phím/chuột tới trạng thái hiện tại."""
        if self.current_state:
            self.current_state.handle_events(events)

    def update(self):
        """Cập nhật logic cho trạng thái hiện tại."""
        if self.current_state:
            self.current_state.update()

    def draw(self):
        """Vẽ giao diện cho trạng thái hiện tại lên màn hình."""
        if self.current_state:
            self.current_state.draw(self.screen)
            
# Lớp cơ sở cho các Trạng thái
class State:
    def __init__(self):
        self.manager = None

    def startup(self, **kwargs):
        """Chạy mỗi khi trạng thái này được kích hoạt."""
        pass

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pass
Class = State
