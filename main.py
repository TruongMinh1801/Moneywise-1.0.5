"""
MONEYWISE 1.0.5 - PHIÊN BẢN NGUYÊN KHỐI (MONOLITHIC EDITION)
--------------------------------------------------------------------------------
Phát triển bởi: Đội ngũ BFF (Build for the Future) - Khóa VII
Đóng gói & Phân phối: TMB Software
Mục đích: Dự án tham gia cuộc thi Samsung Solve for Tomorrow 2026

Bản cập nhật 1.0.5:
- Chuyển đổi kiến trúc lưu trữ sang JSON tại C:\\Users\\<User>\\Moneywise 1.0.5
- Tích hợp Engine tự động kiểm tra và làm sạch dữ liệu theo chu kỳ (Tuần/Tháng/Năm)
- Cho phép người dùng nạp ảnh nền cá nhân hóa (Custom Background)
- Gộp toàn bộ UI Components và Main Controller thành kiến trúc nguyên khối
--------------------------------------------------------------------------------
"""

import os
import sys
import json
import shutil
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
# PHẦN 1: HỆ THỐNG HẰNG SỐ VÀ CẤU HÌNH GIAO DIỆN (CONSTANTS & CONFIG)
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
    "Giải trí": "Bạn đang đầu tư nhiều vào giải trí. Mẹo: Hãy duy trì quy tắc 50/30/20 và thử các hoạt động miễn phí.",
    "Công việc": "Chi phí cho công việc là cần thiết để tạo ra thu nhập, nhưng hãy tối ưu hiệu suất hóa đơn.",
    "Nhu cầu cá nhân": "Cân nhắc kỹ lưỡng giữa nhu cầu thiết yếu (Need) và mong muốn nhất thời (Want).",
    "Ăn uống": "Nấu ăn tại nhà không chỉ giúp bạn làm chủ sức khỏe mà còn tiết kiệm đến 40% chi phí ăn ngoài.",
    "Đi lại": "Tối ưu lộ trình di chuyển hoặc cân nhắc phương tiện công cộng nếu tần suất đi lại quá lớn.",
    "Khác": "Khoản chi không tên thường gom thành lỗ hổng lớn. Hãy phân loại chi tiết hơn ở lần sau."
}


# ==============================================================================
# PHẦN 2: LÕI XỬ LÝ DỮ LIỆU & LƯU TRỮ (DATA CORE ENGINE)
# ==============================================================================
class MoneywiseDataEngine:
    """Động cơ xử lý dữ liệu JSON an toàn tại thư mục User, độc lập với file thực thi"""
    
    def __init__(self):
        self.data_dir = self._get_secure_data_dir()
        self.data_file = os.path.join(self.data_dir, "moneywise_data.json")
        self.custom_bg_dir = os.path.join(self.data_dir, "custom_backgrounds")
        
        if not os.path.exists(self.custom_bg_dir):
            os.makedirs(self.custom_bg_dir)
            
        self.app_data = self._load_and_check_budget_reset()

    def _get_secure_data_dir(self):
        """Khởi tạo và trả về đường dẫn C:\\Users\\<Username>\\Moneywise 1.0.5"""
        user_home = os.path.expanduser("~")
        directory = os.path.join(user_home, "Moneywise 1.0.5")
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    def _get_default_schema(self):
        return {
            "budget_type": "Tháng",
            "budget_limits": {
                "Tuần": 1000000.0,
                "Tháng": 5000000.0,
                "Năm": 60000000.0
            },
            "cycle_start_date": datetime.now().strftime("%Y-%m-%d"),
            "custom_bg_path": "",
            "theme_color": "Nền tối chuẩn",
            "transactions": []
        }

    def _load_and_check_budget_reset(self):
        """Cơ chế tự động làm sạch nhật ký chi tiêu khi bước sang chu kỳ mới"""
        default_data = self._get_default_schema()
        
        if not os.path.exists(self.data_file):
            self._save_raw_data(default_data)
            return default_data

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return default_data

        # Khôi phục các key bị thiếu nếu update từ bản cũ
        for key, value in default_data.items():
            if key not in data:
                data[key] = value

        # THUẬT TOÁN KIỂM TRA CHU KỲ (TIME-CYCLE VALIDATION)
        current_time = datetime.now()
        try:
            saved_time = datetime.strptime(data["cycle_start_date"], "%Y-%m-%d")
        except ValueError:
            saved_time = current_time

        is_reset = False
        b_type = data["budget_type"]
        
        if b_type == "Tuần":
            if current_time.isocalendar()[1] != saved_time.isocalendar()[1] or current_time.year != saved_time.year:
                is_reset = True
        elif b_type == "Tháng":
            if current_time.month != saved_time.month or current_time.year != saved_time.year:
                is_reset = True
        elif b_type == "Năm":
            if current_time.year != saved_time.year:
                is_reset = True

        if is_reset:
            data["transactions"] = [] 
            data["cycle_start_date"] = current_time.strftime("%Y-%m-%d")
            self._save_raw_data(data)
            print(f"[*] Đã tự động bước sang chu kỳ {b_type} mới. Làm sạch nhật ký chi tiêu!")

        return data

    def _save_raw_data(self, data):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def save_current_state(self):
        """Ghi đè trạng thái app_data hiện hành xuống ổ đĩa"""
        self._save_raw_data(self.app_data)

    def add_transaction(self, category, detail, amount):
        now = datetime.now()
        tx = {
            "id": len(self.app_data["transactions"]) + 1,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date_str": now.strftime("%Y-%m-%d"),
            "category": category,
            "detail": detail,
            "amount": amount
        }
        self.app_data["transactions"].append(tx)
        self.save_current_state()

    def get_budget_limit(self, period):
        return self.app_data["budget_limits"].get(period, 0.0)

    def update_budget_limit(self, period, amount):
        self.app_data["budget_limits"][period] = amount
        self.save_current_state()
        
    def set_budget_type(self, period):
        self.app_data["budget_type"] = period
        self.save_current_state()

    def clear_all_transactions(self):
        self.app_data["transactions"] = []
        self.save_current_state()


# ==============================================================================
# PHẦN 3: CÁC COMPONENT GIAO DIỆN (UI MODULES)
# ==============================================================================
class ResponsiveBackground(tk.Label):
    """Hệ thống nền động tương thích PyInstaller tĩnh và ảnh Custom của người dùng"""
    def __init__(self, master, data_engine, **kwargs):
        super().__init__(master, **kwargs)
        self.db = data_engine
        self.current_mode = "color"
        self.raw_image = None
        self.tk_image = None
        
        # Load theme hoặc ảnh nền từ phiên làm việc trước
        saved_bg = self.db.app_data.get("custom_bg_path", "")
        saved_theme = self.db.app_data.get("theme_color", "Nền tối chuẩn")
        
        if saved_bg and os.path.exists(saved_bg):
            self.set_custom_image(saved_bg, 1200, 750)
        else:
            self.set_theme(saved_theme, 1200, 750)

    def set_custom_image(self, file_path, width, height):
        try:
            self.raw_image = Image.open(file_path)
            self.current_mode = "image"
            self.configure(text="", bg="#1E1E24")
            self.resize_and_adapt(width, height)
            
            # Cập nhật db
            self.db.app_data["custom_bg_path"] = file_path
            self.db.save_current_state()
        except Exception as e:
            print(f"Lỗi nạp ảnh custom: {e}")

    def set_theme(self, selection, width, height):
        """Xử lý nạp màu đơn sắc hoặc nạp ảnh nền nội bộ (assets)"""
        if selection.startswith("Ảnh nền"):
            num = selection.split(" ")[-1]
            filename = f"bg_{num}.jpg"
            
            # Tìm đường dẫn tuyệt đối khi chạy qua PyInstaller _MEIPASS
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            full_path = os.path.join(base_path, "assets", "background", filename)
            
            if os.path.exists(full_path):
                self.raw_image = Image.open(full_path)
                self.current_mode = "image"
                self.configure(text="")
                self.resize_and_adapt(width, height)
                
                # Xóa custom bg nếu chọn lại ảnh hệ thống
                self.db.app_data["custom_bg_path"] = ""
                self.db.app_data["theme_color"] = selection
                self.db.save_current_state()
            else:
                messagebox.showwarning("Thiếu Tài Nguyên", f"Không tìm thấy {filename} trong gói cài đặt.")
        else:
            color_map = {
                "Nền tối chuẩn": "#1E1E24",
                "Nền Xám không gian": "#2D3748",
                "Nền Xanh Navy": "#1A202C",
                "Nền Tím Huyền Ảo": "#2E1A47"
            }
            color_hex = color_map.get(selection, "#1E1E24")
            self.current_mode = "color"
            self.raw_image = None
            self.configure(image="", bg=color_hex)
            
            self.db.app_data["custom_bg_path"] = ""
            self.db.app_data["theme_color"] = selection
            self.db.save_current_state()

    def resize_and_adapt(self, width, height):
        if self.current_mode == "image" and self.raw_image and width > 10 and height > 10:
            try:
                resized_img = self.raw_image.resize((width, height), Image.Resampling.LANCZOS)
                self.tk_image = ImageTk.PhotoImage(resized_img)
                self.configure(image=self.tk_image)
            except Exception as e:
                pass


class TransactionForm(ctk.CTkFrame):
    def __init__(self, master, on_save_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_save = on_save_callback
        self.configure(fg_color="transparent")
        self.build_widgets()

    def build_widgets(self):
        ctk.CTkLabel(self, text="➕ GHI CHÉP CHI TIÊU", font=FONT_SUBTITLE, text_color=COLOR_PRIMARY).pack(pady=(10, 15), anchor="w")
        ctk.CTkLabel(self, text="1. Chọn danh mục chính:", font=FONT_LABEL).pack(anchor="w", pady=2)
        
        self.combo_category = ctk.CTkOptionMenu(
            self, values=CATEGORIES,
            fg_color="#2E3038", button_color="#43454E", text_color="#FFFFFF",
            dropdown_fg_color="#2E3038", dropdown_text_color="#FFFFFF", dropdown_hover_color="#43454E"
        )
        self.combo_category.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="2. Chi tiết mặt hàng (Tự nhập):", font=FONT_LABEL).pack(anchor="w", pady=2)
        self.entry_detail = ctk.CTkEntry(self, placeholder_text="Ví dụ: Bút bi, Phở bò...")
        self.entry_detail.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="3. Số tiền chi tiêu (VND):", font=FONT_LABEL).pack(anchor="w", pady=2)
        self.entry_amount = ctk.CTkEntry(self, placeholder_text="Nhập số tiền đã thanh toán")
        self.entry_amount.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(self, text="Lưu Vào Nhật Ký", font=("Segoe UI", 13, "bold"), fg_color=COLOR_SUCCESS, hover_color="#23A16A", command=self.submit).pack(fill="x", ipady=4)

    def submit(self):
        cat, det, amt = self.combo_category.get(), self.entry_detail.get().strip(), self.entry_amount.get().strip()
        if not det or not amt:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ chi tiết và số tiền!")
            return
        try:
            amt_val = float(amt)
            if amt_val <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi dữ liệu", "Số tiền phải là số lớn hơn 0!")
            return
        self.on_save(cat, det, amt_val)
        self.entry_detail.delete(0, tk.END)
        self.entry_amount.delete(0, tk.END)


class BudgetConfigForm(ctk.CTkFrame):
    def __init__(self, master, db_engine, on_update_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_engine
        self.on_update = on_update_callback
        self.configure(fg_color="transparent")
        self.build_widgets()

    def build_widgets(self):
        ctk.CTkLabel(self, text="⚙️ QUẢN LÝ HẠN MỨC", font=FONT_SUBTITLE, text_color=COLOR_PRIMARY).pack(pady=(15, 10), anchor="w")
        
        self.seg_period = ctk.CTkSegmentedButton(self, values=["Tuần", "Tháng", "Năm"], command=self.load_limit)
        self.seg_period.set(self.db.app_data["budget_type"])
        self.seg_period.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="Hạn mức tối đa (VND):", font=FONT_LABEL).pack(anchor="w", pady=2)
        self.entry_limit = ctk.CTkEntry(self, placeholder_text="Nhập số tiền")
        self.entry_limit.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(self, text="Cập Nhật Hạn Mức", font=("Segoe UI", 12, "bold"), fg_color="#4F46E5", hover_color="#4338CA", command=self.save_limit).pack(fill="x", ipady=2)
        self.load_limit(self.seg_period.get())

    def load_limit(self, period):
        val = self.db.get_budget_limit(period)
        self.entry_limit.delete(0, tk.END)
        self.entry_limit.insert(0, str(int(val)))
        
    def save_limit(self):
        period, val_str = self.seg_period.get(), self.entry_limit.get().strip()
        try:
            val = float(val_str)
            if val < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Hạn mức không hợp lệ!")
            return
        
        self.db.set_budget_type(period)
        self.db.update_budget_limit(period, val)
        messagebox.showinfo("Thành Công", f"Đã lưu hạn mức {period} là {val:,.0f} VND.")
        self.on_update()


class ThemeConfigForm(ctk.CTkFrame):
    def __init__(self, master, on_theme_change, on_custom_bg, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        ctk.CTkLabel(self, text="🎨 GIAO DIỆN & HÌNH NỀN", font=FONT_SUBTITLE, text_color=COLOR_PRIMARY).pack(pady=(15, 10), anchor="w")
        
        themes = ["Nền tối chuẩn", "Nền Xám không gian", "Nền Xanh Navy", "Nền Tím Huyền Ảo"] + [f"Ảnh nền {i}" for i in range(1, 11)]
        self.combo = ctk.CTkOptionMenu(
            self, values=themes, command=on_theme_change,
            fg_color="#2E3038", button_color="#43454E", text_color="#FFFFFF",
            dropdown_fg_color="#2E3038", dropdown_text_color="#FFFFFF", dropdown_hover_color="#43454E"
        )
        self.combo.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(self, text="Tải Ảnh Từ Máy Tính...", font=("Segoe UI", 11, "bold"), fg_color="#64748B", hover_color="#475569", command=on_custom_bg).pack(fill="x")


class AnalyticsPanel(ctk.CTkFrame):
    def __init__(self, master, db_engine, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_engine
        self.configure(fg_color=("#F2F4F7", "#1A1C20"), corner_radius=15, border_width=1)
        self.build_widgets()

    def build_widgets(self):
        self.chart_frame = ctk.CTkFrame(self, fg_color=("#E5E7EB", "#25272C"), corner_radius=10)
        self.chart_frame.pack(pady=15, padx=15, fill="both", expand=True)

        self.fig, self.ax = plt.subplots(figsize=(4, 4), facecolor="none")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        self.prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.prog_frame.pack(pady=10, padx=15, fill="x")

        self.lbl_status = ctk.CTkLabel(self.prog_frame, text="Tiến độ: 0%", font=FONT_LABEL, anchor="w")
        self.lbl_status.pack(fill="x", pady=2)
        
        self.bar = ctk.CTkProgressBar(self.prog_frame, height=14, corner_radius=7)
        self.bar.set(0)
        self.bar.pack(fill="x", pady=4)
        
        self.lbl_alert = ctk.CTkLabel(self.prog_frame, text="", font=FONT_LABEL, text_color=COLOR_DANGER, anchor="w")
        self.lbl_alert.pack(fill="x", pady=2)

        ctk.CTkLabel(self, text="💡 TƯ VẤN LỜI KHUYÊN MONEYWISE", font=("Segoe UI", 11, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w", padx=15)
        self.txt_advice = ctk.CTkTextbox(self, height=75, wrap="word", font=FONT_BODY)
        self.txt_advice.pack(pady=(5, 15), padx=15, fill="x")

    def refresh_data(self):
        txs = self.db.app_data["transactions"]
        b_type = self.db.app_data["budget_type"]
        limit = self.db.get_budget_limit(b_type)
        
        # 1. Tính toán Chart
        cat_sums = {}
        for tx in txs:
            cat_sums[tx["category"]] = cat_sums.get(tx["category"], 0) + tx["amount"]
            
        self.ax.clear()
        if not cat_sums:
            self.ax.text(0.5, 0.5, "Chưa có giao dịch\ntrong chu kỳ này", ha='center', va='center', color="gray", fontsize=11)
            self.ax.axis('off')
        else:
            labels, values = list(cat_sums.keys()), list(cat_sums.values())
            colors = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#4B5563']
            text_col = "white" if ctk.get_appearance_mode() == "Dark" else "black"
            _, _, autotexts = self.ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops=dict(color=text_col, fontsize=9))
            for at in autotexts: at.set_color('white'); at.set_weight('bold')
            self.ax.axis('equal')
        
        self.fig.tight_layout()
        self.canvas.draw()

        # 2. Cập nhật Progress Bar
        total = sum(cat_sums.values())
        pct = (total / limit * 100) if limit > 0 else 0
        
        self.lbl_status.configure(text=f"Chi tiêu chu kỳ {b_type}: {pct:.1f}% ({total:,.0f} / {limit:,.0f} VND)")
        self.bar.set(min(pct / 100.0, 1.0))
        
        if pct < 60: col = COLOR_SUCCESS
        elif pct < 80: col = COLOR_WARNING_LOW
        elif pct < 100: col = COLOR_WARNING_HIGH
        else: col = COLOR_DANGER
        self.bar.configure(progress_color=col)
        
        self.lbl_alert.configure(text=f"⚠️ BẠN ĐÃ TIÊU VƯỢT HẠN MỨC: {total-limit:,.0f} VND!" if total > limit else "")

        # 3. Lời khuyên
        self.txt_advice.configure(state="normal")
        self.txt_advice.delete("1.0", tk.END)
        if not cat_sums:
            self.txt_advice.insert(tk.END, f"Chu kỳ {b_type} mới đã bắt đầu. Hãy kiểm soát tốt dòng tiền của bạn nhé!")
        else:
            highest_cat = max(cat_sums, key=cat_sums.get)
            msg = ADVICE_RULES.get(highest_cat, "")
            self.txt_advice.insert(tk.END, f"Nhóm chi nhiều nhất: {highest_cat}.\n💡 {msg}")
        self.txt_advice.configure(state="disabled")


class HistoryLogPanel(ctk.CTkFrame):
    def __init__(self, master, db_engine, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_engine
        self.configure(fg_color=("#F2F4F7", "#1A1C20"), corner_radius=15, border_width=1)
        self.build_widgets()

    def build_widgets(self):
        ctk.CTkLabel(self, text="📜 NHẬT KÝ HOẠT ĐỘNG", font=FONT_SUBTITLE).pack(pady=15, padx=10)
        
        search_box = ctk.CTkFrame(self, fg_color="transparent")
        search_box.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(search_box, text="Lọc tìm kiếm:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        
        self.combo_filter = ctk.CTkOptionMenu(
            search_box, values=["Tất cả"] + CATEGORIES, command=self.refresh_list,
            fg_color="#2E3038", button_color="#43454E", text_color="#FFFFFF",
            dropdown_fg_color="#2E3038", dropdown_text_color="#FFFFFF"
        )
        self.combo_filter.pack(fill="x", pady=5)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=("#E5E7EB", "#1F2125"), label_text="Dòng thời gian chi tiêu")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def refresh_list(self, filter_val=None):
        if filter_val is None: filter_val = self.combo_filter.get()
        
        for w in self.scroll.winfo_children(): w.destroy()
            
        txs = self.db.app_data["transactions"]
        if filter_val != "Tất cả":
            txs = [tx for tx in txs if tx["category"] == filter_val]
            
        if not txs:
            ctk.CTkLabel(self.scroll, text="Trống.", text_color="gray", font=("Segoe UI", 11, "italic")).pack(pady=20)
            return
            
        for tx in reversed(txs):
            card = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2A2D34"), corner_radius=6, border_width=1, border_color="#43454E")
            card.pack(fill="x", pady=4, padx=5)
            
            try: t = datetime.strptime(tx["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
            except: t = "00:00:00"
            
            txt = f"⏱️ {t} [{tx['date_str']}]\n🛒 {tx['detail']}\n💰 {tx['amount']:,.0f} VND\n🗂️ {tx['category']}"
            ctk.CTkLabel(card, text=txt, font=FONT_LOG, justify="left", anchor="w").pack(fill="x", padx=10, pady=6)


# ==============================================================================
# PHẦN 4: TRUNG TÂM ĐIỀU KHIỂN & ỨNG DỤNG CHÍNH (MAIN APP CONTROLLER)
# ==============================================================================
class MoneywiseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Moneywise 1.0.5 - Giải Pháp Quản Lý Chi Tiêu (BFF Team)")
        self.geometry("1200x750")
        self.minsize(1100, 680)

        # 1. Khởi tạo Database Engine
        self.db = MoneywiseDataEngine()

        # 2. Khởi tạo Background System
        self.bg_system = ResponsiveBackground(self, self.db)
        self.bg_system.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_system.lower()

        # 3. Phân khu Grid Layout
        self.grid_columnconfigure(0, weight=3, minsize=320)  
        self.grid_columnconfigure(1, weight=4, minsize=420)  
        self.grid_columnconfigure(2, weight=3, minsize=340)  
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.bind("<Configure>", lambda e: self.bg_system.resize_and_adapt(self.winfo_width(), self.winfo_height()) if e.widget == self else None)
        
        # 4. Nạp dữ liệu lần đầu
        self.refresh_all_panels()

    def _build_ui(self):
        # --- CỘT 1: CÁC KHUNG NHẬP LIỆU & ĐIỀU KHIỂN ---
        self.left_col = ctk.CTkScrollableFrame(self, fg_color=("#F2F4F7", "#1A1C20"), corner_radius=15, border_width=1)
        self.left_col.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        TransactionForm(self.left_col, self.handle_add_tx).pack(pady=(5, 10), padx=5, fill="x")
        ctk.CTkFrame(self.left_col, height=2, fg_color="#43454E").pack(fill="x", padx=5, pady=10)
        
        BudgetConfigForm(self.left_col, self.db, self.refresh_all_panels).pack(pady=5, padx=5, fill="x")
        
        ThemeConfigForm(self.left_col, self.handle_theme_change, self.handle_custom_bg).pack(pady=5, padx=5, fill="x")
        ctk.CTkFrame(self.left_col, height=2, fg_color="#43454E").pack(fill="x", padx=5, pady=15)

        ctk.CTkButton(self.left_col, text="Xuất Báo Cáo HTML", font=("Segoe UI", 13, "bold"), fg_color="#8B5CF6", hover_color="#7C3AED", command=self.export_html).pack(pady=5, padx=5, fill="x")
        ctk.CTkButton(self.left_col, text="Xóa Toàn Bộ Dữ Liệu", font=("Segoe UI", 13, "bold"), fg_color=COLOR_DANGER, hover_color="#DC2626", command=self.factory_reset).pack(pady=(5, 15), padx=5, fill="x")

        # --- CỘT 2: ĐỒ THỊ TRUNG TÂM ---
        self.panel_visual = AnalyticsPanel(self, self.db)
        self.panel_visual.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # --- CỘT 3: NHẬT KÝ CHI TIÊU ---
        self.panel_history = HistoryLogPanel(self, self.db)
        self.panel_history.grid(row=0, column=2, padx=15, pady=15, sticky="nsew")

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN (EVENT HANDLERS) ---
    def handle_add_tx(self, cat, det, amt):
        self.db.add_transaction(cat, det, amt)
        self.refresh_all_panels()

    def handle_theme_change(self, theme_name):
        self.bg_system.set_theme(theme_name, self.winfo_width(), self.winfo_height())
        if self.db.app_data.get("theme_color") != theme_name:
            self.db.app_data["theme_color"] = theme_name
            self.db.save_current_state()

    def handle_custom_bg(self):
        file_path = filedialog.askopenfilename(title="Chọn ảnh", filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            target_path = os.path.join(self.db.custom_bg_dir, f"user_bg{os.path.splitext(file_path)[1]}")
            try:
                shutil.copy(file_path, target_path)
                self.bg_system.set_custom_image(target_path, self.winfo_width(), self.winfo_height())
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải ảnh: {e}")

    def factory_reset(self):
        if messagebox.askyesno("Xác nhận", "Xóa toàn bộ dữ liệu hiện tại?"):
            self.db.clear_all_transactions()
            self.refresh_all_panels()
            messagebox.showinfo("Thành công", "Đã dọn dẹp sạch sẽ lịch sử giao dịch.")

    def export_html(self):
        dest = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")], initialfile="Moneywise_Report.html")
        if not dest: return
        
        try:
            txs = self.db.app_data["transactions"]
            total = sum(t["amount"] for t in txs)
            limit = self.db.get_budget_limit(self.db.app_data["budget_type"])
            
            html = f"""<html><head><meta charset="utf-8"><title>Báo Cáo Moneywise 1.0.5</title></head>
            <body style="font-family: Arial; padding: 40px;">
                <h1 style="color: #2563EB;">📊 BÁO CÁO PHÂN TÍCH TÀI CHÍNH (Nhóm BFF)</h1>
                <p>Tổng chi: <b>{total:,.0f} VND</b> / Hạn mức: <b>{limit:,.0f} VND</b></p>
                <table border="1" cellspacing="0" cellpadding="8" style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f2f2f2;"><th>Thời gian</th><th>Mặt hàng</th><th>Danh mục</th><th>Số tiền</th></tr>"""
            for tx in txs:
                html += f"<tr><td>{tx['timestamp']}</td><td>{tx['detail']}</td><td>{tx['category']}</td><td>{tx['amount']:,.0f}</td></tr>"
            html += "</table></body></html>"
            
            with open(dest, "w", encoding="utf-8") as f: f.write(html)
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo tại:\n{dest}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def refresh_all_panels(self):
        """Cập nhật đồng loạt đồ thị và danh sách khi dữ liệu thay đổi"""
        self.panel_visual.refresh_data()
        self.panel_history.refresh_list()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = MoneywiseApp()
    app.mainloop()