"""
Moneywise Database Management Module
Phát triển tối ưu cho Python 3.13.7 và SQLite3
Chức năng: Quản lý vòng đời dữ liệu, CRUD, thống kê nâng cao, sao lưu và nạp tệp CSV.
An toàn bảo mật - Chạy cục bộ không yêu cầu quyền Admin hệ thống.
"""

import os
import csv
import shutil
import sqlite3
import logging
from datetime import datetime, timedelta

# Cấu hình đường dẫn lưu trữ thông minh cục bộ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "moneywise.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

# Khởi tạo hệ thống ghi nhật ký lỗi (Logging) nội bộ để kiểm soát ứng dụng
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DB_DIR, "database.log") if os.path.exists(DB_DIR) else "database.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class DatabaseManager:
    """
    Bộ điều phối kỹ thuật xử lý toàn bộ các tác vụ truy vấn, lưu trữ,
    đọc ghi và bảo mật dữ liệu tài chính cho ứng dụng Moneywise.
    """
    def __init__(self):
        self._initialize_directories()
        self.create_tables()
        self.auto_purge_old_backups()

    def _initialize_directories(self):
        """Tạo các thư mục lưu trữ dữ liệu và sao lưu nếu chưa tồn tại"""
        for directory in [DB_DIR, BACKUP_DIR]:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logging.info(f"Đã khởi tạo thành công thư mục: {directory}")
                except Exception as e:
                    logging.error(f"Không thể tạo thư mục {directory}: {e}")
                    raise RuntimeError(f"Lỗi phân quyền hệ thống: {e}")

    def _get_connection(self):
        """Khởi tạo kết nối SQLite với cấu hình timeout chống nghẽn luồng"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            # Kích hoạt tính năng Foreign Key nếu mở rộng bảng trong tương lai
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            logging.error(f"Lỗi kết nối cơ sở dữ liệu SQLite: {e}")
            raise e

    # ==============================================================================
    # TẦNG KHỞI TẠO CẤU TRÚC BẢNG (SCHEMA INITIALIZATION)
    # ==============================================================================
    def create_tables(self):
        """Xây dựng cấu trúc các bảng dữ liệu chuẩn hóa nguyên tử (Atomic)"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                detail TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                date_str TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS budgets (
                period_type TEXT PRIMARY KEY CHECK(period_type IN ('Tuần', 'Tháng', 'Năm')), 
                amount REAL NOT NULL CHECK(amount >= 0)
            );
            """
        ]
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                
                # Khởi tạo hạn mức mặc định ban đầu nếu cơ sở dữ liệu mới tinh
                default_budgets = [("Tuần", 1000000.0), ("Tháng", 5000000.0), ("Năm", 50000000.0)]
                cursor.executemany(
                    "INSERT OR IGNORE INTO budgets (period_type, amount) VALUES (?, ?);",
                    default_budgets
                )
                conn.commit()
                logging.info("Đồng bộ cấu trúc bảng cơ sở dữ liệu thành công.")
        except sqlite3.Error as e:
            logging.error(f"Thất bại khi cấu hình bảng dữ liệu: {e}")
            raise e

    # ==============================================================================
    # NGHIỆP VỤ CRUD NHẬT KÝ CHI TIÊU (TRANSACTION CRUD)
    # ==============================================================================
    def add_transaction(self, category, detail, amount):
        """Thêm mới một bản ghi chi tiêu vào dòng thời gian"""
        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
            INSERT INTO transactions (category, detail, amount, date_str, timestamp) 
            VALUES (?, ?, ?, ?, ?);
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (category, detail, amount, date_str, timestamp))
                conn.commit()
                logging.info(f"Đã lưu giao dịch: {detail} - {amount} VND vào danh mục {category}")
                return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi chèn giao dịch mới: {e}")
            return None

    def delete_transaction(self, tx_id):
        """Xóa một bản ghi cụ thể theo ID khóa chính"""
        query = "DELETE FROM transactions WHERE id = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (tx_id,))
                conn.commit()
                logging.info(f"Đã xóa bản ghi chi tiêu có ID: {tx_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Không thể xóa giao dịch {tx_id}: {e}")
            return False

    def update_transaction(self, tx_id, category, detail, amount):
        """Cập nhật nội dung sửa đổi cho một bản ghi đã tồn tại"""
        query = """
            UPDATE transactions 
            SET category = ?, detail = ?, amount = ? 
            WHERE id = ?;
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (category, detail, amount, tx_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Lỗi chỉnh sửa bản ghi {tx_id}: {e}")
            return False

    def get_filtered_transactions(self, period_type, category_filter="Tất cả"):
        """
        Truy vấn danh sách chi tiêu được lọc tối ưu bằng thuật toán thời gian của SQLite.
        Đáp ứng chuẩn đầu ra cho cả Panel UI và Generator Báo Cáo HTML.
        """
        now = datetime.now()
        base_query = "SELECT timestamp, date_str, detail, amount, category FROM transactions WHERE 1=1"
        params = []

        # Xử lý tính toán mốc thời gian động bằng SQL tinh gọn
        if period_type == "Tuần":
            # Lấy từ đầu tuần hiện tại (Thứ 2 lúc 00:00:00)
            start_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            base_query += " AND timestamp >= ?"
            params.append(start_week.strftime("%Y-%m-%d %H:%M:%S"))
        elif period_type == "Tháng":
            # Lấy từ ngày đầu tiên của tháng hiện tại
            start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            base_query += " AND timestamp >= ?"
            params.append(start_month.strftime("%Y-%m-%d %H:%M:%S"))
        elif period_type == "Năm":
            # Lấy từ ngày 1 tháng 1 của năm hiện tại
            start_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            base_query += " AND timestamp >= ?"
            params.append(start_year.strftime("%Y-%m-%d %H:%M:%S"))

        # Áp dụng bộ lọc phân loại danh mục
        if category_filter != "Tất cả":
            base_query += " AND category = ?"
            params.append(category_filter)

        # Sắp xếp theo dòng thời gian mới nhất hiện lên trên cùng
        base_query += " ORDER BY timestamp DESC, id DESC"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(base_query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Lỗi truy vấn danh sách lọc giao dịch: {e}")
            return []

    # ==============================================================================
    # NGHIỆP VỤ QUẢN LÝ HẠN MỨC TRẦN (BUDGET OPERATIONS)
    # ==============================================================================
    def get_budget(self, period_type):
        """Lấy ngưỡng hạn mức tối đa quy định cho chu kỳ được chọn"""
        query = "SELECT amount FROM budgets WHERE period_type = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (period_type,))
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except sqlite3.Error as e:
            logging.error(f"Lỗi lấy hạn mức chu kỳ {period_type}: {e}")
            return 0.0

    def update_budget(self, period_type, amount):
        """Cập nhật lại giá trị hạn mức cảnh báo mới"""
        query = "UPDATE budgets SET amount = ? WHERE period_type = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (amount, period_type))
                conn.commit()
                logging.info(f"Đã cập nhật hạn mức mới cho [{period_type}]: {amount} VND")
                return True
        except sqlite3.Error as e:
            logging.error(f"Không thể cập nhật hạn mức: {e}")
            return False

    # ==============================================================================
    # TẦNG PHÂN TÍCH THỐNG KÊ TOÁN HỌC CAO CẤP (ANALYTICS ENGINE)
    # ==============================================================================
    def get_category_distribution_dict(self, period_type):
        """
        Tính tổng tiền gom nhóm theo từng danh mục trực tiếp bằng SQL.
        Trả về Dictionary phục vụ cho biểu đồ quạt Matplotlib.
        """
        raw_data = self.get_filtered_transactions(period_type, category_filter="Tất cả")
        distribution = {}
        for row in raw_data:
            _, _, _, amount, category = row
            distribution[category] = distribution.get(category, 0.0) + amount
        return distribution

    def get_highest_spending_category(self, period_type):
        """Tìm ra tên danh mục ngốn nhiều ngân sách nhất để sinh lời khuyên thông minh"""
        distribution = self.get_category_distribution_dict(period_type)
        if not distribution:
            return None
        return max(distribution, key=distribution.get)

    # ==============================================================================
    # HỆ THỐNG SAO LƯU & AN TOÀN DỮ LIỆU (BACKUP & UTILITIES)
    # ==============================================================================
    def create_automated_backup(self):
        """Sinh một bản sao lưu vật lý bảo vệ tệp DB kèm mốc thời gian"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"moneywise_backup_{timestamp}.db"
        backup_dest = os.path.join(BACKUP_DIR, backup_filename)
        
        try:
            if os.path.exists(DB_PATH):
                shutil.copy2(DB_PATH, backup_dest)
                logging.info(f"Đã tạo bản sao lưu hệ thống an toàn tại: {backup_dest}")
                return True
        except IOError as e:
            logging.error(f"Lỗi vật lý khi đang sao lưu tệp dữ liệu: {e}")
        return False

    def auto_purge_old_backups(self, max_days=7):
        """Tự động dọn dẹp các file sao lưu cũ hơn 7 ngày để tiết kiệm dung lượng đĩa"""
        try:
            now = datetime.now()
            for filename in os.listdir(BACKUP_DIR):
                file_path = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(file_path) and filename.startswith("moneywise_backup_"):
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if now - file_time > timedelta(days=max_days):
                        os.remove(file_path)
                        logging.info(f"Đã giải phóng bản sao lưu lỗi thời: {filename}")
        except Exception as e:
            logging.error(f"Lỗi trong tiến trình quét dọn bản sao lưu cũ: {e}")

    def clear_all_data(self):
        """Xóa sạch nhật ký giao dịch và đưa hạn mức về trạng thái xuất xưởng"""
        try:
            # Tạo một bản sao lưu khẩn cấp trước khi thực thi lệnh xóa diện rộng
            self.create_automated_backup()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions;")
                cursor.execute("UPDATE budgets SET amount = 1000000.0 WHERE period_type = 'Tuần';")
                cursor.execute("UPDATE budgets SET amount = 5000000.0 WHERE period_type = 'Tháng';")
                cursor.execute("UPDATE budgets SET amount = 50000000.0 WHERE period_type = 'Năm';")
                conn.commit()
                logging.warning("Hành động dọn sạch hệ thống (Factory Reset) đã được thực thi hoàn tất.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi cố gắng xóa sạch dữ liệu hệ thống: {e}")
            return False

    # ==============================================================================
    # ĐỘNG CƠ NHẬP/XUẤT DỮ LIỆU FILE NGOÀI (CSV IMPORT / EXPORT CORES)
    # ==============================================================================
    def export_to_csv(self, target_csv_path):
        """Xuất toàn bộ cơ sở dữ liệu nhật ký chi tiêu ra file bảng tính CSV"""
        query = "SELECT id, category, detail, amount, date_str, timestamp FROM transactions ORDER BY id ASC;"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                
                with open(target_csv_path, mode="w", encoding="utf-8-sig", newline="") as csv_file:
                    writer = csv.writer(csv_file)
                    # Ghi hàng tiêu đề chuẩn hóa
                    writer.writerow(["ID Bản Ghi", "Danh Mục", "Chi Tiết Giao Dịch", "Số Tiền (VND)", "Ngày Ghi Nhận", "Timestamp Hệ Thống"])
                    writer.writerows(rows)
                
                logging.info(f"Đã kết xuất dữ liệu CSV thành công ra vị trí: {target_csv_path}")
                return True, f"Xuất file thành công! Ghi nhận {len(rows)} dòng dữ liệu."
        except Exception as e:
            logging.error(f"Lỗi kết xuất tệp CSV: {e}")
            return False, str(e)

    def import_from_csv(self, source_csv_path):
        """Nạp dữ liệu từ file văn bản CSV bên ngoài nối tiếp vào cơ sở dữ liệu hiện tại"""
        query = "INSERT INTO transactions (category, detail, amount, date_str, timestamp) VALUES (?, ?, ?, ?, ?);"
        try:
            with open(source_csv_path, mode="r", encoding="utf-8-sig") as csv_file:
                reader = csv.reader(csv_file)
                header = next(reader, None) # Bỏ qua dòng tiêu đề bảng tính
                
                records_to_insert = []
                for row_idx, row in enumerate(reader, start=2):
                    if not row or len(row) < 5:
                        continue # Bỏ qua dòng trống lỗi định dạng
                    
                    # Xử lý bóc tách các trường: Tùy biến vị trí nếu file có chứa cột ID bản ghi ở đầu
                    if len(row) == 6:
                        _, category, detail, amount_str, date_str, timestamp = row
                    else:
                        category, detail, amount_str, date_str, timestamp = row[:5]
                    
                    try:
                        amount = float(amount_str)
                        if amount <= 0: raise ValueError()
                    except ValueError:
                        logging.warning(f"Bỏ qua dòng {row_idx} trong file CSV do số tiền không hợp lệ.")
                        continue
                        
                    records_to_insert.append((category.strip(), detail.strip(), amount, date_str.strip(), timestamp.strip()))
                
                if records_to_insert:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.executemany(query, records_to_insert)
                        conn.commit()
                    logging.info(f"Nạp thành công {len(records_to_insert)} dòng dữ liệu từ CSV vào SQLite.")
                    return True, f"Đã nhập thành công {len(records_to_insert)} bản ghi mới vào nhật ký!"
                else:
                    return False, "Không tìm thấy dữ liệu hợp lệ trong file CSV cung cấp."
        except Exception as e:
            logging.error(f"Sự cố khi đọc file nạp CSV: {e}")
            return False, str(e)