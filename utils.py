"""
Moneywise Utilities Module
Phát triển tối ưu cho Python 3.13.7
Chức năng: Cung cấp các hàm tiện ích hệ thống, định dạng tiền tệ, xử lý thời gian và validate dữ liệu.
An toàn - Tiết kiệm tài nguyên - Không phụ thuộc thư viện ngoài.
"""

import os
import sys
import re
from datetime import datetime, timedelta

class MoneywiseUtils:
    """
    Lớp tập hợp tất cả các công cụ tĩnh (Static Methods) hỗ trợ xử lý logic nền,
    giúp mã nguồn ở các file chính trở nên ngắn gọn và dễ bảo trì hơn.
    """

    @staticmethod
    def resource_path(relative_path):
        """
        Thuật toán định tuyến đường dẫn tuyệt đối cho tài nguyên (Assets, Backgrounds).
        Hỗ trợ tối ưu khi chạy script thô HOẶC sau khi đóng gói thành file đơn (.EXE) bằng PyInstaller.
        Giúp vượt qua cơ chế chặn đường dẫn ảo của Windows SmartScreen.
        """
        try:
            # PyInstaller tạo một thư mục tạm thời và lưu đường dẫn trong _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        return os.path.join(base_path, relative_path)

    @staticmethod
    def format_currency(amount, suffix="VND"):
        """
        Chuyển đổi một số thực/số nguyên thành chuỗi định dạng tiền tệ chuẩn UX.
        Ví dụ: 1500000 -> "1,500,000 VND"
        """
        try:
            val = float(amount)
            return f"{val:,.0f} {suffix}"
        except (ValueError, TypeError):
            return f"0 {suffix}"

    @staticmethod
    def clean_and_parse_amount(amount_str):
        """
        Bộ lọc thông minh xử lý chuỗi tiền tệ do người dùng nhập vào.
        Chấp nhận các định dạng lỗi như: "1.000.000", "500,000", " 250000đ ", "100k"
        Trả về giá trị float hợp lệ hoặc None nếu không thể dịch được.
        """
        if not amount_str:
            return None
            
        try:
            # Chuyển sang chữ thường và loại bỏ khoảng trắng thừa
            clean_str = amount_str.strip().lower()
            
            # Xử lý tiếng lóng tài chính phổ biến (Ví dụ: 100k -> 100000)
            if clean_str.endswith('k'):
                clean_str = clean_str[:-1]
                multiplier = 1000
            else:
                multiplier = 1
                
            # Loại bỏ tất cả các ký tự không phải số, dấu chấm, hoặc dấu phẩy
            clean_str = re.sub(r'[^\d.,]', '', clean_str)
            
            if not clean_str:
                return None
                
            # Thuật toán đoán định dấu phân cách thập phân/hàng nghìn
            if ',' in clean_str and '.' in clean_str:
                # Định dạng chuẩn quốc tế (1,000.50) hoặc chuẩn Việt Nam (1.000,50)
                if clean_str.rfind(',') > clean_str.rfind('.'):
                    # Kiểu VN: đổi chấm thành rỗng, phẩy thành chấm
                    clean_str = clean_str.replace('.', '').replace(',', '.')
                else:
                    # Kiểu Quốc tế: xóa phẩy
                    clean_str = clean_str.replace(',', '')
            elif ',' in clean_str:
                # Chỉ có dấu phẩy: Thường là phân cách hàng nghìn ở VN (500,000)
                # Trừ khi nó đóng vai trò là dấu thập phân duy nhất (Ví dụ: 50,5 VND)
                if len(clean_str).split(',')[-1] == 3:
                    clean_str = clean_str.replace(',', '')
                else:
                    clean_str = clean_str.replace(',', '.')
            elif '.' in clean_str:
                # Chỉ có dấu chấm: Thường là phân cách hàng nghìn (100.000)
                if len(clean_str.split('.')[-1]) == 3:
                    clean_str = clean_str.replace('.', '')

            result = float(clean_str) * multiplier
            return result if result >= 0 else None
            
        except (ValueError, IndexError):
            return None

    @staticmethod
    def sanitize_text(text, max_length=150):
        """
        Hàm dọn dẹp chuỗi văn bản (Mục tiêu/Chi tiết mặt hàng).
        Cắt bỏ ký tự lạ để chống lỗi vỡ giao diện Log và hạn chế các cuộc tấn công SQL Injection thô sơ.
        """
        if not text:
            return ""
        # Loại bỏ các ký tự điều khiển nguy hiểm (Newline, tab...)
        clean_text = re.sub(r'[\n\r\t]', ' ', text)
        # Bóp gọn khoảng trắng thừa ở giữa chuỗi
        clean_text = " ".join(clean_text.split())
        # Giới hạn độ dài chuỗi ký tự để bảo vệ bộ nhớ đệm UI
        return clean_text[:max_length]

    @staticmethod
    def get_period_bounds_display(period_type):
        """
        Tính toán chính xác ngày bắt đầu và ngày kết thúc của chu kỳ hiện tại dưới dạng chuỗi văn bản.
        Dùng để hiển thị lên thanh tiêu đề hoặc sub-header của UI.
        Ví dụ: "Từ 22/06/2026 đến 28/06/2026"
        """
        now = datetime.now()
        
        if period_type == "Tuần":
            start = now - timedelta(days=now.weekday())
            end = start + timedelta(days=6)
        elif period_type == "Tháng":
            start = now.replace(day=1)
            # Tìm ngày cuối tháng bằng cách cộng 32 ngày rồi quay lại ngày mùng 1 đầu tháng sau trừ đi 1 ngày
            next_month = (start + timedelta(days=32)).replace(day=1)
            end = next_month - timedelta(days=1)
        elif period_type == "Năm":
            start = now.replace(month=1, day=1)
            end = now.replace(month=12, day=31)
        else:
            return now.strftime("%d/%m/%Y")
            
        return f"Từ {start.strftime('%d/%m/%Y')} đến {end.strftime('%d/%m/%Y')}"

    @staticmethod
    def calculate_financial_health_status(total_spent, budget_limit):
        """
        Thuật toán phân tích chỉ số sức khỏe tài chính thông minh dựa trên tỷ lệ chi tiêu.
        Trả về một bộ gồm: (Lời đánh giá ngắn, Mã màu sắc đại diện)
        """
        if budget_limit <= 0:
            return ("Chưa thiết lập hạn mức trần!", "#94A3B8")
            
        pct = (total_spent / budget_limit) * 100
        
        if pct == 0:
            return ("Ví tiền nguyên vẹn. Bạn chưa tiêu gì trong chu kỳ này!", "#10B981")
        elif pct < 50:
            return ("An toàn tuyệt vời! Bạn đang kiểm soát chi tiêu rất tốt.", "#10B981")
        elif pct < 80:
            return ("Hợp lý. Ngân sách đang vơi dần, hãy chi tiêu thông thái hơn.", "#EAB308")
        elif pct < 100:
            return ("Báo động vàng! Bạn đã chạm sát ngưỡng giới hạn chi tiêu.", "#F97316")
        else:
            over = total_spent - budget_limit
            return (f"Khủng hoảng nhẹ! Bạn đã tiêu lạm phát quá {over:,.0f} VND.", "#EF4444")