"""
Moneywise UI Components Module
Phát triển tối ưu cho Python 3.13.7 và CustomTkinter
Hỗ trợ tùy biến giao diện giữa hệ màu đơn sắc và hệ thống 10 ảnh nền
Đã vá hoàn toàn các lỗi hệ thống liên quan đến kích thước hình học và tương phản màu chữ dropdown
"""

import os
import sys
import random
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk

# Cấu hình Matplotlib tương thích sâu với luồng đồ họa của Tkinter
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==============================================================================
# HỆ THỐNG HẰNG SỐ VÀ ĐỊNH DẠNG ĐỒ HỌA (UI CONSTANTS)
# ==============================================================================
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 14, "bold")
FONT_LABEL = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 12, "normal")
FONT_LOG = ("Consolas", 11, "normal")

COLOR_PRIMARY = "#3B82F6"
COLOR_SUCCESS = "#2CC985"
COLOR_WARNING_LOW = "#EAB308"
COLOR_WARNING_HIGH = "#F97316"
COLOR_DANGER = "#EF4444"

CATEGORIES = ["Học tập", "Giải trí", "Công việc", "Nhu cầu cá nhân", "Ăn uống", "Đi lại", "Khác"]

ADVICE_RULES = {
    "Học tập": "Đầu tư vào bản thân luôn mang lại lợi nhuận cao nhất. Hãy tiếp tục phát huy!",
    "Giải trí": "Bạn đang đầu tư nhiều vào giải trí. Mẹo: Hãy duy trì một thói quen chi tiêu 50/30/20 và có thể giải trí miễn phí bằng cách đi bộ, hoặc là chơi thể thao.",
    "Công việc": "Chi phí cho công việc là cần thiết để tạo ra thu nhập, nhưng hãy tối ưu hiệu suất hóa đơn.",
    "Nhu cầu cá nhân": "Cân nhắc kỹ lưỡng giữa nhu cầu thiết yếu (Need) và mong muốn nhất thời (Want).",
    "Ăn uống": "Nấu ăn tại nhà không chỉ giúp bạn làm chủ sức khỏe mà còn tiết kiệm đến 40% chi phí ăn ngoài.",
    "Đi lại": "Tối ưu lộ trình di chuyển hoặc cân nhắc phương tiện công cộng nếu tần suất đi lại quá lớn.",
    "Khác": "Khoản chi không tên thường gom thành lỗ hổng lớn. Hãy cố gắng phân loại chi tiết hơn ở lần sau."
}

# ==============================================================================
# 1. ĐỘNG CƠ HÌNH NỀN THÔNG MINH (RESPONSIVE BACKGROUND)
# ==============================================================================
class ResponsiveBackground(tk.Label):
    """
    Hợp phần xử lý hình nền co giãn hoặc đổ màu trơn dựa trên lựa chọn của người dùng.
    Hỗ trợ hiển thị mượt mà khi người dùng kéo giãn độ rộng cửa sổ app.
    """
    def __init__(self, master, bg_folder_path, **kwargs):
        super().__init__(master, **kwargs)
        self.bg_folder = bg_folder_path
        self.current_mode = "color"       # Trạng thái: "color" hoặc "image"
        self.current_value = "#1E1E24"     # Lưu mã màu hex hoặc tên file ảnh hiện hành
        self.raw_image = None
        self.tk_image = None
        
        # Tự động khởi tạo cấu trúc thư mục nếu chưa tồn tại trên ổ đĩa
        if not os.path.exists(self.bg_folder):
            try:
                os.makedirs(self.bg_folder)
            except Exception:
                pass
            
        # Thiết lập khởi động mặc định bằng gam màu tối tiêu chuẩn
        self.configure(bg=self.current_value)

    def set_theme(self, selection, width, height):
        """Hàm tiếp nhận lệnh thay đổi giao diện diện mạo từ Form điều khiển đổ xuống"""
        if selection.startswith("Ảnh nền"):
            try:
                # Phân rã chuỗi "Ảnh nền X" để lấy chỉ số file ảnh "bg_X.jpg"
                num = selection.split(" ")[-1]
                filename = f"bg_{num}.jpg"
                full_path = os.path.join(self.bg_folder, filename)
                
                if os.path.exists(full_path):
                    self.raw_image = Image.open(full_path)
                    self.current_mode = "image"
                    self.current_value = filename
                    self.configure(text="") 
                    self.resize_and_adapt(width, height)
                else:
                    messagebox.showwarning(
                        "Thiếu Tài Nguyên", 
                        f"Không tìm thấy file {filename} tại:\n{self.bg_folder}\n\nHệ thống tạm thời giữ nguyên cấu hình nền cũ."
                    )
            except Exception as e:
                print(f"[!] Lỗi nạp ảnh nền nghệ thuật: {e}")
        else:
            # Bản đồ ánh xạ hệ màu đơn sắc (Solid Color Matte)
            color_map = {
                "Nền tối chuẩn": "#1E1E24",
                "Nền Xám không gian": "#2D3748",
                "Nền Xanh Navy": "#1A202C",
                "Nền Tím Huyền Ảo": "#2E1A47"
            }
            color_hex = color_map.get(selection, "#1E1E24")
            self.current_mode = "color"
            self.current_value = color_hex
            self.raw_image = None
            self.configure(image="", bg=color_hex)

    def resize_and_adapt(self, width, height):
        """Thuật toán nội suy co giãn kích thước ảnh chất lượng cao thích ứng độ phân giải cửa sổ"""
        if self.current_mode == "image" and self.raw_image and width > 10 and height > 10:
            try:
                resized_img = self.raw_image.resize((width, height), Image.Resampling.LANCZOS)
                self.tk_image = ImageTk.PhotoImage(resized_img)
                self.configure(image=self.tk_image)
            except Exception as e:
                print(f"Lỗi xử lý co giãn mật độ pixel ảnh nền: {e}")


# ==============================================================================
# 2. KHUNG NHẬP LIỆU GIAO DỊCH (TRANSACTION INPUT FORM)
# ==============================================================================
class TransactionForm(ctk.CTkFrame):
    """Khung chứa form nhập liệu: Lựa chọn danh mục, tự nhập mô tả và số tiền chi tiêu."""
    def __init__(self, master, on_save_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_save = on_save_callback
        self.configure(fg_color="transparent")
        self.build_widgets()

    def build_widgets(self):
        lbl_section = ctk.CTkLabel(self, text="➕ GHI CHÉP CHI TIÊU", font=FONT_SUBTITLE, text_color=COLOR_PRIMARY)
        lbl_section.pack(pady=(10, 15), anchor="w")

        lbl_cat = ctk.CTkLabel(self, text="1. Chọn danh mục chính:", font=FONT_LABEL)
        lbl_cat.pack(anchor="w", pady=2)
        
        # SỬA LỖI TƯƠNG PHẢN MÀU CHỮ DROPDOWN
        self.combo_category = ctk.CTkOptionMenu(
            self, 
            values=CATEGORIES,
            fg_color="#2E3038", 
            button_color="#43454E",
            text_color="#FFFFFF",
            dropdown_fg_color="#2E3038",
            dropdown_text_color="#FFFFFF",
            dropdown_hover_color="#43454E"
        )
        self.combo_category.pack(fill="x", pady=(0, 12))

        lbl_detail = ctk.CTkLabel(self, text="2. Chi tiết mặt hàng / Mục tiêu (Tự nhập):", font=FONT_LABEL)
        lbl_detail.pack(anchor="w", pady=2)
        
        self.entry_detail = ctk.CTkEntry(self, placeholder_text="Ví dụ: Bút bi, Phở bò, Vé xe buýt...")
        self.entry_detail.pack(fill="x", pady=(0, 12))

        lbl_amount = ctk.CTkLabel(self, text="3. Số tiền chi tiêu (VND):", font=FONT_LABEL)
        lbl_amount.pack(anchor="w", pady=2)
        
        self.entry_amount = ctk.CTkEntry(self, placeholder_text="Nhập số tiền đã thanh toán")
        self.entry_amount.pack(fill="x", pady=(0, 20))

        self.btn_submit = ctk.CTkButton(
            self, 
            text="Lưu Vào Nhật Ký", 
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_SUCCESS, 
            hover_color="#23A16A",
            command=self.validate_and_submit
        )
        self.btn_submit.pack(fill="x", ipady=4)

    def validate_and_submit(self):
        category = self.combo_category.get()
        detail = self.entry_detail.get().strip()
        amount_str = self.entry_amount.get().strip()

        if not detail:
            messagebox.showwarning("Lỗi Nhập Liệu", "Vui lòng tự điền chi tiết mặt hàng chi tiêu!")
            return

        if not amount_str:
            messagebox.showwarning("Lỗi Nhập Liệu", "Vui lòng cung cấp số tiền đã thanh toán!")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Lỗi Số Liệu", "Số tiền chi tiêu phải là một con số lớn hơn 0!")
                return
        except ValueError:
            messagebox.showerror("Lỗi Định Dạng", "Số tiền không hợp lệ! Vui lòng chỉ nhập các ký tự số nguyên hoặc số thập phân.")
            return

        self.on_save(category, detail, amount)
        self.clear_form()

    def clear_form(self):
        self.entry_detail.delete(0, tk.END)
        self.entry_amount.delete(0, tk.END)


# ==============================================================================
# 3. KHUNG CẤU HÌNH HẠN MỨC TRẦN (BUDGET CONFIGURATION FORM)
# ==============================================================================
class BudgetConfigForm(ctk.CTkFrame):
    """Khung điều khiển hạn mức cảnh báo dòng tiền tối đa theo chu kỳ thời gian."""
    def __init__(self, master, on_update_callback, on_get_budget_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_update = on_update_callback
        self.get_budget = on_get_budget_callback
        self.configure(fg_color="transparent")
        self.build_widgets()

    def build_widgets(self):
        lbl_section = ctk.CTkLabel(self, text="⚙️ QUẢN LÝ HẠN MỨC TRẦN", font=FONT_SUBTITLE, text_color=COLOR_PRIMARY)
        lbl_section.pack(pady=(15, 10), anchor="w")

        self.seg_period = ctk.CTkSegmentedButton(self, values=["Tuần", "Tháng", "Năm"], command=self.handle_period_switch)
        self.seg_period.set("Tháng")
        self.seg_period.pack(fill="x", pady=(0, 12))

        lbl_limit = ctk.CTkLabel(self, text="Thiết lập hạn mức tối đa mới (VND):", font=FONT_LABEL)
        lbl_limit.pack(anchor="w", pady=2)

        self.entry_limit = ctk.CTkEntry(self, placeholder_text="Nhập hạn mức trần bảo vệ")
        self.entry_limit.pack(fill="x", pady=(0, 15))

        self.btn_update = ctk.CTkButton(
            self,
            text="Cập Nhật Hạn Mức",
            font=("Segoe UI", 12, "bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self.process_update
        )
        self.btn_update.pack(fill="x", ipady=2)
        self.handle_period_switch("Tháng")

    def handle_period_switch(self, selected_period):
        current_val = self.get_budget(selected_period)
        self.entry_limit.delete(0, tk.END)
        self.entry_limit.insert(0, str(int(current_val)))

    def process_update(self):
        period = self.seg_period.get()
        limit_str = self.entry_limit.get().strip()

        try:
            limit_val = float(limit_str)
            if limit_val < 0:
                messagebox.showerror("Lỗi Số Liệu", "Hạn mức tối đa bảo vệ không được phép dưới 0 VND!")
                return
        except ValueError:
            messagebox.showerror("Lỗi Định Dạng", "Vui lòng cung cấp giá trị hạn mức hợp lệ!")
            return

        self.on_update(period, limit_val)
        messagebox.showinfo("Thành Công", f"Đã thiết lập hạn mức chi tiêu {period} thành {limit_val:,.0f} VND.")


# ==============================================================================
# 4. KHUNG ĐIỀU CHỈNH GIAO DIỆN & HÌNH NỀN (THEME CONFIGURATION FORM)
# ==============================================================================
class ThemeConfigForm(ctk.CTkFrame):
    """Khung điều khiển cho phép người dùng đổi màu nền tĩnh hoặc nạp các file ảnh nền."""
    def __init__(self, master, on_theme_change_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_theme_change = on_theme_change_callback
        self.configure(fg_color="transparent")
        self.build_widgets()
        
    def build_widgets(self):
        lbl_section = ctk.CTkLabel(self, text="🎨 GIAO DIỆN & HÌNH NỀN", font=FONT_SUBTITLE, text_color=COLOR_PRIMARY)
        lbl_section.pack(pady=(15, 10), anchor="w")
        
        themes_list = [
            "Nền tối chuẩn", "Nền Xám không gian", "Nền Xanh Navy", "Nền Tím Huyền Ảo",
            "Ảnh nền 1", "Ảnh nền 2", "Ảnh nền 3", "Ảnh nền 4", "Ảnh nền 5",
            "Ảnh nền 6", "Ảnh nền 7", "Ảnh nền 8", "Ảnh nền 9", "Ảnh nền 10"
        ]
        
        # SỬA LỖI TƯƠNG PHẢN MÀU CHỮ DROPDOWN (ÉP CHỮ TRẮNG)
        self.combo_theme = ctk.CTkOptionMenu(
            self,
            values=themes_list,
            command=self.on_theme_change,
            fg_color="#2E3038",
            button_color="#43454E",
            text_color="#FFFFFF",
            dropdown_fg_color="#2E3038",
            dropdown_text_color="#FFFFFF",
            dropdown_hover_color="#43454E"
        )
        self.combo_theme.set("Nền tối chuẩn")
        self.combo_theme.pack(fill="x")


# ==============================================================================
# 5. TRUNG TÂM PHÂN TÍCH & ĐỒ THỊ THỐNG KÊ (ANALYTICS PANEL)
# ==============================================================================
class AnalyticsPanel(ctk.CTkFrame):
    """Hợp phần trung tâm kết xuất biểu đồ quạt Matplotlib và phân tích lời khuyên."""
    def __init__(self, master, on_period_change_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_period_change = on_period_change_callback
        self.configure(fg_color=("#F2F4F7", "#1A1C20"), corner_radius=15, border_width=1)
        self.build_widgets()

    def build_widgets(self):
        self.seg_view = ctk.CTkSegmentedButton(self, values=["Tuần", "Tháng", "Năm"], command=self.on_period_change)
        self.seg_view.set("Tháng")
        self.seg_view.pack(pady=15, padx=15, fill="x")

        self.chart_frame = ctk.CTkFrame(self, fg_color=("#E5E7EB", "#25272C"), corner_radius=10)
        self.chart_frame.pack(pady=5, padx=15, fill="both", expand=True)

        self.fig, self.ax = plt.subplots(figsize=(4, 4), facecolor="none")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        self.progress_container = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_container.pack(pady=10, padx=15, fill="x")

        self.lbl_status = ctk.CTkLabel(self.progress_container, text="Tiến độ: 0% (0 / 0 VND)", font=FONT_LABEL, anchor="w")
        self.lbl_status.pack(fill="x", pady=2)

        self.bar = ctk.CTkProgressBar(self.progress_container, height=14, corner_radius=7)
        self.bar.set(0.0)
        self.bar.pack(fill="x", pady=4)

        self.lbl_alert = ctk.CTkLabel(self.progress_container, text="", font=FONT_LABEL, text_color=COLOR_DANGER, anchor="w")
        self.lbl_alert.pack(fill="x", pady=2)

        lbl_adv_title = ctk.CTkLabel(self, text="💡 TƯ VẤN LỜI KHUYÊN MONEYWISE", font=("Segoe UI", 11, "bold"), text_color=COLOR_PRIMARY)
        lbl_adv_title.pack(anchor="w", padx=15, pady=(5, 0))

        self.txt_advice = ctk.CTkTextbox(self, height=75, wrap="word", font=FONT_BODY)
        self.txt_advice.pack(pady=(2, 15), padx=15, fill="x")
        self.txt_advice.insert("1.0", "Hệ thống đang phân tích hành vi dòng tiền của bạn...")
        self.txt_advice.configure(state="disabled")

    def update_progress_engine(self, total_spent, budget_limit):
        if budget_limit <= 0:
            pct = 0.0
        else:
            pct = (total_spent / budget_limit) * 100

        self.lbl_status.configure(text=f"Tiến độ chi tiêu: {pct:.1f}% ({total_spent:,.0f} / {budget_limit:,.0f} VND)")
        
        if pct < 60:
            target_color = COLOR_SUCCESS
        elif pct < 80:
            target_color = COLOR_WARNING_LOW
        elif pct < 100:
            target_color = COLOR_WARNING_HIGH
        else:
            target_color = COLOR_DANGER

        self.bar.set(min(pct / 100.0, 1.0))
        self.bar.configure(progress_color=target_color)

        if total_spent > budget_limit:
            over_amount = total_spent - budget_limit
            self.lbl_alert.configure(text=f"⚠️ BẠN ĐÃ TIÊU VƯỢT HẠN MỨC: {over_amount:,.0f} VND!")
        else:
            self.lbl_alert.configure(text="")

    def render_pie_visual(self, grouped_data):
        self.ax.clear()
        
        if not grouped_data:
            self.ax.text(0.5, 0.5, "Không có dữ liệu\nđể vẽ đồ thị quạt", horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, color="gray", fontsize=12)
            self.ax.axis('off')
            self.canvas.draw()
            return

        labels = list(grouped_data.keys())
        values = list(grouped_data.values())
        
        palette = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#4B5563']
        mode_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"

        wedges, texts, autotexts = self.ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=140,
            colors=palette[:len(labels)],
            textprops=dict(color=mode_color, fontsize=9)
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')

        self.ax.axis('equal')
        self.fig.tight_layout()
        self.canvas.draw()

    def update_advice_board(self, highest_category):
        self.txt_advice.configure(state="normal")
        self.txt_advice.delete("1.0", tk.END)

        if not highest_category:
            self.txt_advice.insert(tk.END, "Chúc mừng! Bạn đang kiểm soát ngân sách rất xuất sắc, chưa ghi nhận hạng mục chi tiêu rủi ro cao.")
        else:
            advice_msg = ADVICE_RULES.get(highest_category, "Hãy duy trì thói quen ghi chép tài chính chặt chẽ để tối ưu hóa tương lai.")
            self.txt_advice.insert(tk.END, f"Nhóm chi nhiều nhất: {highest_category}.\n💡 {advice_msg}")
            
        self.txt_advice.configure(state="disabled")


# ==============================================================================
# 6. KHUNG NHẬT KÝ CHI TIÊU BÊN PHẢI (HISTORY LOG PANEL)
# ==============================================================================
class HistoryLogPanel(ctk.CTkFrame):
    """Khung hiển thị dòng thời gian (Timeline) chi tiết lịch sử thu chi."""
    def __init__(self, master, on_filter_change_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_filter_change = on_filter_change_callback
        self.configure(fg_color=("#F2F4F7", "#1A1C20"), corner_radius=15, border_width=1)
        self.build_widgets()

    def build_widgets(self):
        lbl_section = ctk.CTkLabel(self, text="📜 NHẬT KÝ HOẠT ĐỘNG", font=FONT_SUBTITLE)
        lbl_section.pack(pady=15, padx=10)

        search_box = ctk.CTkFrame(self, fg_color="transparent")
        search_box.pack(fill="x", padx=15, pady=(0, 5))

        lbl_filter = ctk.CTkLabel(search_box, text="Lọc tìm kiếm theo danh mục:", font=("Segoe UI", 11, "bold"))
        lbl_filter.pack(anchor="w")

        filter_list = ["Tất cả"] + CATEGORIES
        
        # SỬA LỖI TƯƠNG PHẢN MÀU CHỮ DROPDOWN
        self.combo_search = ctk.CTkOptionMenu(
            search_box,
            values=filter_list,
            command=self.on_filter_change,
            fg_color="#2E3038",
            button_color="#43454E",
            text_color="#FFFFFF",
            dropdown_fg_color="#2E3038",
            dropdown_text_color="#FFFFFF",
            dropdown_hover_color="#43454E"
        )
        self.combo_search.pack(fill="x", pady=5)

        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color=("#E5E7EB", "#1F2125"), label_text="Dòng thời gian chi tiêu thực tế")
        self.scroll_area.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def render_log_rows(self, dataset):
        for widget in self.scroll_area.winfo_children():
            widget.destroy()

        if not dataset:
            lbl_empty = ctk.CTkLabel(self.scroll_area, text="Không tìm thấy bản ghi nào khớp với bộ lọc.", font=("Segoe UI", 11, "italic"), text_color="gray")
            lbl_empty.pack(pady=20)
            return

        for data_row in dataset:
            timestamp_raw, date_str, detail, amount, category = data_row
            
            try:
                time_obj = datetime.strptime(timestamp_raw, "%Y-%m-%d %H:%M:%S")
                time_formatted = time_obj.strftime("%H:%M:%S")
            except ValueError:
                time_formatted = "00:00:00"

            display_text = (
                f"⏱️ {time_formatted} [{date_str}]\n"
                f"🛒 Đã tiêu: {detail}\n"
                f"💰 Số tiền: {amount:,.0f} VND\n"
                f"🗂️ Danh mục: {category}"
            )

            row_card = ctk.CTkFrame(self.scroll_area, fg_color=("#FFFFFF", "#2A2D34"), corner_radius=6, border_width=1, border_color="#43454E")
            row_card.pack(fill="x", pady=4, padx=5)

            lbl_log = ctk.CTkLabel(row_card, text=display_text, font=FONT_LOG, justify="left", anchor="w")
            lbl_log.pack(fill="x", padx=10, pady=6)


# ==============================================================================
# 7. KHUNG CHỨA TOÀN DIỆN DIỆN MẠO CHÍNH (APPLICATION INTERFACE CONTAINER)
# ==============================================================================
class MoneywiseUIContainer(ctk.CTk):
    """Kiến trúc phân khu Grid 3 cột kết nối trực tiếp với Controller điều hành chính."""
    def __init__(self, bg_folder, controller_hooks):
        super().__init__()
        self.hooks = controller_hooks
        
        self.title("Moneywise - Giải Pháp Quản Lý Chi Tiêu Toàn Diện")
        self.geometry("1200x750")
        self.minsize(1100, 680)

        self.bg_system = ResponsiveBackground(self, bg_folder_path=bg_folder)
        self.bg_system.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_system.lower()

        self.grid_columnconfigure(0, weight=3, minsize=320)  
        self.grid_columnconfigure(1, weight=4, minsize=420)  
        self.grid_columnconfigure(2, weight=3, minsize=340)  
        self.grid_rowconfigure(0, weight=1)

        self.assemble_modular_frames()
        self.bind("<Configure>", self.handle_window_resize_event)

    def assemble_modular_frames(self):
        """Lắp ráp chi tiết các Module nghiệp vụ lên khung giao diện (Đã sửa lỗi tràn khung bằng Khung cuộn)"""
        
        self.left_column = ctk.CTkScrollableFrame(
            self, 
            fg_color=("#F2F4F7", "#1A1C20"), 
            corner_radius=15, 
            border_width=1
        )
        self.left_column.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # Khởi tạo form nhập giao dịch
        self.tx_form = TransactionForm(self.left_column, on_save_callback=self.hooks['add_transaction'])
        self.tx_form.pack(pady=(5, 10), padx=5, fill="x")

        # Đường phân cách đồ họa trực quan
        line_break = ctk.CTkFrame(self.left_column, height=2, fg_color="#43454E")
        line_break.pack(fill="x", padx=5, pady=10)

        # Khởi tạo form hạn mức
        self.budget_form = BudgetConfigForm(
            self.left_column, 
            on_update_callback=self.hooks['update_budget'],
            on_get_budget_callback=self.hooks['get_budget_val']
        )
        self.budget_form.pack(pady=5, padx=5, fill="x")

        # Khởi tạo form cấu hình giao diện & hình nền tùy biến
        self.theme_form = ThemeConfigForm(
            self.left_column,
            on_theme_change_callback=self.cb_internal_theme_change
        )
        self.theme_form.pack(pady=5, padx=5, fill="x")

        # Đường phân cách đồ họa trước khi vào khu vực nút hệ thống
        line_break2 = ctk.CTkFrame(self.left_column, height=2, fg_color="#43454E")
        line_break2.pack(fill="x", padx=5, pady=15)

        # Nút xuất tài liệu báo cáo HTML
        self.btn_html_export = ctk.CTkButton(
            self.left_column,
            text="Xuất Báo Cáo HTML",
            font=("Segoe UI", 13, "bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=self.hooks['export_report_html']
        )
        self.btn_html_export.pack(pady=5, padx=5, fill="x")

        # Nút dọn sạch dữ liệu hệ thống
        self.btn_factory_reset = ctk.CTkButton(
            self.left_column,
            text="Xóa Toàn Bộ Dữ Liệu",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_DANGER,
            hover_color="#DC2626",
            command=self.hooks['clear_all_system_data']
        )
        self.btn_factory_reset.pack(pady=(5, 15), padx=5, fill="x")

        # Khung đồ thị thống kê ở giữa
        self.visual_panel = AnalyticsPanel(self, on_period_change_callback=self.hooks['change_view_period'])
        self.visual_panel.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # Khung nhật ký tiến trình bên phải
        self.history_panel = HistoryLogPanel(self, on_filter_change_callback=self.hooks['change_log_filter'])
        self.history_panel.grid(row=0, column=2, padx=15, pady=15, sticky="nsew")

    def cb_internal_theme_change(self, selected_theme):
        self.bg_system.set_theme(selected_theme, self.winfo_width(), self.winfo_height())
        if 'change_theme' in self.hooks:
            self.hooks['change_theme'](selected_theme)

    def handle_window_resize_event(self, event):
        if event.widget == self:
            self.bg_system.resize_and_adapt(self.winfo_width(), self.winfo_height())

    def request_save_path(self, period_name):
        file_dest = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Document", "*.html")],
            title=f"Chọn vị trí lưu trữ Báo cáo {period_name}",
            initialfile=f"Moneywise_Report_{period_name}_{datetime.now().strftime('%Y%m%d')}.html"
        )
        return file_dest

    def fetch_current_chart_figure(self):
        return self.fig, self.ax