"""
Moneywise Report Generator Module
Phát triển tối ưu cho Python 3.13.7
Chức năng: Khởi tạo báo cáo tài chính HTML độc lập không dùng Template Engine
An toàn với Windows SmartScreen - Không yêu cầu quyền Quản trị (Admin)
"""

import os
import io
import base64
from datetime import datetime

# Bảng màu đồng bộ từ UI để hiển thị trạng thái tài chính trên file báo cáo HTML
COLOR_HTML_SUCCESS = "#10B981"       # Xanh lá (An toàn)
COLOR_HTML_WARNING_LOW = "#F59E0B"   # Vàng (Cảnh báo nhẹ)
COLOR_HTML_WARNING_HIGH = "#F97316"  # Cam (Rủi ro cao)
COLOR_HTML_DANGER = "#EF4444"        # Đỏ (Vượt ngưỡng)

class ReportGenerator:
    """
    Lớp điều phối kỹ thuật kết xuất báo cáo tài chính hằng tuần/tháng/năm.
    Sử dụng kỹ thuật nhúng Base64 mã hóa ảnh đồ thị độc lập.
    """
    
    @staticmethod
    def _convert_chart_to_base64(fig):
        """
        Thuật toán nội bộ: Chuyển đổi Figure của Matplotlib thành chuỗi Base64.
        Giúp file HTML tự ngậm ảnh bên trong, tránh lỗi gãy đường dẫn (broken paths).
        """
        if fig is None:
            return ""
        try:
            img_buffer = io.BytesIO()
            # Đổi tạm nền đồ thị sang màu trắng tinh khiết để tiệp màu với trang giấy in HTML
            original_facecolor = fig.get_facecolor()
            fig.patch.set_facecolor('white')
            
            # Lưu đồ thị vào bộ nhớ đệm RAM dưới định dạng PNG chất lượng cao
            fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150, facecolor='white')
            img_buffer.seek(0)
            
            # Mã hóa nhị phân sang chuỗi ký tự Base64 ASCII
            base64_data = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # Khôi phục trạng thái nền cũ của biểu đồ trên giao diện ứng dụng để không làm mất mỹ quan
            fig.patch.set_facecolor(original_facecolor)
            
            return base64_data
        except Exception as e:
            print(f"[!] Lỗi nghiêm trọng khi mã hóa đồ thị sang Base64: {e}")
            return ""

    @staticmethod
    def _calculate_progress_color(total_spent, budget_limit):
        """Tính toán mã màu CSS động cho file báo cáo dựa trên tỷ lệ tiêu dùng"""
        if budget_limit <= 0:
            return COLOR_HTML_DANGER
        pct = (total_spent / budget_limit) * 100
        if pct < 60:
            return COLOR_HTML_SUCCESS
        elif pct < 80:
            return COLOR_HTML_WARNING_LOW
        elif pct < 100:
            return COLOR_HTML_WARNING_HIGH
        return COLOR_HTML_DANGER

    @classmethod
    def generate_html_report(cls, target_path, period_type, transactions, budget_limit, matplotlib_fig):
        """
        Hàm cốt lõi: Biên dịch chuỗi HTML thô từ mảng dữ liệu và ghi xuống ổ đĩa cứng.
        Không phụ thuộc file template bên ngoài, không lo lỗi phân quyền Windows.
        """
        if not target_path:
            return False, "Đường dẫn lưu file không hợp lệ hoặc người dùng đã hủy lệnh."

        try:
            # 1. Tính toán các chỉ số tài chính cơ bản
            total_spent = sum(row[3] for row in transactions) # row[3] là trường amount trong cấu trúc DB
            total_records = len(transactions)
            overspent_amount = total_spent - budget_limit
            is_overspent = overspent_amount > 0
            
            # Tính toán phân rã ngân sách theo danh mục để lập bảng thống kê phụ
            category_summary = {}
            for row in transactions:
                _, _, _, amount, category = row
                category_summary[category] = category_summary.get(category, 0.0) + amount

            # 2. Xử lý chuyển đổi biểu đồ quạt sang chuỗi nhúng mã hóa Base64
            chart_base64_string = cls._convert_chart_to_base64(matplotlib_fig)
            
            # 3. Khởi tạo thuật toán dựng cấu trúc HTML Table bằng vòng lặp chuỗi
            table_rows_html = ""
            for idx, row in enumerate(transactions, 1):
                timestamp_raw, date_str, detail, amount, category = row
                
                # Trích xuất định dạng hiển thị thời gian tinh gọn
                try:
                    time_formatted = datetime.strptime(timestamp_raw, "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
                except ValueError:
                    time_formatted = "00:00:00"

                table_rows_html += f"""
                <tr>
                    <td class="text-center">{idx}</td>
                    <td><span class="badge-time">{time_formatted}</span> {date_str}</td>
                    <td><span class="badge-cat">{category}</span></td>
                    <td class="text-semibold">{detail}</td>
                    <td class="text-right text-danger">{amount:,.0f} VND</td>
                </tr>
                """

            # 4. Dựng cấu trúc bảng tóm tắt danh mục chi tiết
            cat_rows_html = ""
            for cat_name, cat_amount in sorted(category_summary.items(), key=lambda item: item[1], reverse=True):
                cat_pct = (cat_amount / total_spent * 100) if total_spent > 0 else 0.0
                cat_rows_html += f"""
                <div class="cat-summary-row">
                    <span class="cat-summary-name">🔹 {cat_name}</span>
                    <span class="cat-summary-val">{cat_amount:,.0f} VND ({cat_pct:.1f}%)</span>
                </div>
                """

            # 5. Thiết lập khối giao diện cảnh báo nếu người dùng tiêu lạm phát (Vượt hạn mức trần)
            alert_block_html = ""
            if is_overspent:
                alert_block_html = f"""
                <div class="alert-card animate-shake">
                    <div class="alert-title">⚠️ CẢNH BÁO: VƯỢT HẠN MỨC CHI TIÊU!</div>
                    <div class="alert-body">
                        Hệ thống ghi nhận bạn đã tiêu quá hạn mức thiết lập cho chu kỳ {period_type} này 
                        một khoản tiền là: <strong>{overspent_amount:,.0f} VND</strong>. Hãy cân đối lại dòng tiền ngay!
                    </div>
                </div>
                """

            # Xác định màu sắc động cho biến số hiển thị tiến trình tổng quát
            status_color = cls._calculate_progress_color(total_spent, budget_limit)
            progress_percentage = (total_spent / budget_limit * 100) if budget_limit > 0 else 0.0

            # 6. Biên dịch khối đại văn bản HTML cấu trúc lồng CSS nội bộ cao cấp (Embedded CSS Grid/Flexbox)
            html_payload = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moneywise - Báo Cáo Tài Chính Theo {period_type}</title>
    <style>
        :root {{
            --primary: #3B82F6;
            --dark: #0F172A;
            --slate: #475569;
            --light-bg: #F8FAFC;
            --border: #E2E8F0;
        }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--light-bg);
            color: var(--dark);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.5;
        }}
        .report-wrapper {{
            max-width: 1000px;
            margin: 0 auto;
            background: #FFFFFF;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        }}
        .header-section {{
            text-align: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 30px;
            margin-bottom: 35px;
        }}
        .header-section h1 {{
            font-size: 28px;
            color: #1E3A8A;
            margin: 0 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .header-section .timestamp {{
            font-size: 14px;
            color: var(--slate);
            font-style: italic;
        }}
        .grid-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #F1F5F9;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid var(--border);
        }}
        .stat-card .title {{
            font-size: 13px;
            font-weight: 600;
            color: var(--slate);
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 22px;
            font-weight: 700;
            color: var(--dark);
        }}
        .alert-card {{
            background-color: #FEF2F2;
            border-left: 6px solid #EF4444;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 35px;
        }}
        .alert-title {{
            color: #991B1B;
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 6px;
        }}
        .alert-body {{
            color: #7F1D1D;
            font-size: 14px;
        }}
        .visuals-container {{
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 30px;
            align-items: center;
            background: #FAFAFA;
            padding: 25px;
            border-radius: 12px;
            border: 1px dashed #CBD5E1;
            margin-bottom: 35px;
        }}
        .chart-box {{
            text-align: center;
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .chart-box img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}
        .cat-box {{
            padding: 10px 0;
        }}
        .cat-box h3 {{
            margin-top: 0;
            font-size: 16px;
            border-bottom: 2px solid var(--border);
            padding-bottom: 8px;
            color: #1E3A8A;
        }}
        .cat-summary-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #F1F5F9;
            font-size: 14px;
        }}
        .cat-summary-name {{
            font-weight: 500;
        }}
        .cat-summary-val {{
            font-weight: 600;
            color: var(--slate);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th {{
            background-color: #1E3A8A;
            color: #FFFFFF;
            font-weight: 600;
            font-size: 14px;
            padding: 14px 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
            color: #334155;
        }}
        tr:nth-child(even) {{
            background-color: #F8FAFC;
        }}
        tr:hover {{
            background-color: #F1F5F9;
        }}
        .text-center {{ text-align: center; }}
        .text-right {{ text-align: right; }}
        .text-semibold {{ font-weight: 600; }}
        .text-danger {{ color: #DC2626; }}
        .badge-time {{
            background: #E2E8F0;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
            font-weight: 600;
        }}
        .badge-cat {{
            background: #DBEAFE;
            color: #1E40AF;
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .footer-banner {{
            text-align: center;
            margin-top: 50px;
            font-size: 12px;
            color: #94A3B8;
            border-top: 1px solid var(--border);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="report-wrapper">
        <div class="header-section">
            <h1>Báo Cáo Nhật Ký Chi Tiêu - Moneywise</h1>
            <div class="timestamp">Báo cáo khởi tạo tự động vào ngày: {datetime.now().strftime('%d/%m/%Y lúc %H:%M:%S')}</div>
        </div>

        {alert_block_html}

        <div class="grid-stats">
            <div class="stat-card">
                <div class="title">Chu Kỳ Thống Kê</div>
                <div class="value" style="color: var(--primary);">Theo {period_type}</div>
            </div>
            <div class="stat-card">
                <div class="title">Hạn Mức Ngưỡng Trần</div>
                <div class="value">{budget_limit:,.0f}đ</div>
            </div>
            <div class="stat-card">
                <div class="title">Tổng Chi Tiêu Thực Tế</div>
                <div class="value" style="color: {status_color};">{total_spent:,.0f}đ</div>
            </div>
        </div>

        <div class="visuals-container">
            <div class="chart-box">
                {"<img src='data:image/png;base64," + chart_base64_string + "' alt='Biểu đồ cơ cấu Moneywise'>" if chart_base64_string else "<p style='color:gray;padding:40px;'>Đồ thị trống hoặc không có dữ liệu kết xuất.</p>"}
            </div>
            <div class="cat-box">
                <h3>📊 CƠ CẤU THEO DANH MỤC</h3>
                {cat_rows_html if cat_rows_html else "<p style='color:gray;font-size:14px;'>Không ghi nhận hạng mục phát sinh tiền.</p>"}
                <div class="cat-summary-row" style="border-top: 2px solid var(--border); margin-top: 10px; font-weight: bold;">
                    <span>Tỷ lệ lấp đầy hạn mức:</span>
                    <span style="color: {status_color};">{progress_percentage:.1f}%</span>
                </div>
            </div>
        </div>

        <h3>📋 CHI TIẾT DÒNG THỜI GIAN GIAO DỊCH ({total_records} Bản Ghi)</h3>
        <table>
            <thead>
                <tr>
                    <th style="width: 6%;" class="text-center">STT</th>
                    <th style="width: 24%;">Thời Gian Ghi Nhận</th>
                    <th style="width: 20%;">Danh Mục Gốc</th>
                    <th style="width: 32%;">Chi Tiết Mục Tiêu Đã Chi</th>
                    <th style="width: 18%;" class="text-right">Số Tiền (VND)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html if table_rows_html else "<tr><td colspan='5' class='text-center' style='color:gray;padding:30px;'>Không tồn tại dữ liệu nhật ký giao dịch trong chu kỳ này.</td></tr>"}
            </tbody>
        </table>

        <div class="footer-banner">
            Báo cáo tài chính độc lập được sinh ra từ lõi phần mềm Moneywise Core Engine (Python 3.13.7).<br>
            Tệp tin an toàn - Không chứa mã độc thực thi hệ thống - Bảo mật dữ liệu cá nhân cục bộ.
        </div>
    </div>
</body>
</html>
"""

            # 7. Lưu trữ tệp tin xuống đường dẫn vật lý người dùng chọn bằng cơ chế Encoding UTF-8 chuẩn chỉ
            with open(target_path, "w", encoding="utf-8") as file_stream:
                file_stream.write(html_payload)
                
            return True, "Kết xuất tệp HTML hoàn tất."
        except Exception as e:
            return False, f"Lỗi hệ thống trong quá trình xử lý chuỗi hoặc ghi file: {str(e)}"