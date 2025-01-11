from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QDateEdit, QApplication, QFileDialog  
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta
from create_database import DailyCards, engine
from sqlalchemy.orm import Session
from sqlalchemy import select
import sys
import pandas as pd


class DoanhThu(QWidget):
    def __init__(self, daily_ticket_manager=None):
        super().__init__()
        self.daily_ticket_manager = daily_ticket_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filter section
        filter_layout = QHBoxLayout()
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))  # Mặc định 7 ngày trước
        filter_layout.addWidget(QLabel("Start Date:"))
        filter_layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())  # Mặc định ngày hiện tại
        filter_layout.addWidget(QLabel("End Date:"))
        filter_layout.addWidget(self.end_date_edit)

        filter_button = QPushButton("Filter")
        filter_button.clicked.connect(self.update_table)
        filter_layout.addWidget(filter_button)

        # Thêm nút Export Excel
        export_button = QPushButton("Export to Excel")
        export_button.clicked.connect(self.export_to_excel)
        filter_layout.addWidget(export_button)

        layout.addLayout(filter_layout)

        # Summary section
        summary_layout = QVBoxLayout()

        self.date_range_label = QLabel()
        self.date_range_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        summary_layout.addWidget(self.date_range_label)

        stats_layout = QHBoxLayout()

        self.total_vehicles_label = QLabel()
        self.total_vehicles_label.setStyleSheet("font-size: 14px; margin-right: 20px;")
        stats_layout.addWidget(self.total_vehicles_label)

        self.total_revenue_label = QLabel()
        self.total_revenue_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        stats_layout.addWidget(self.total_revenue_label)

        stats_layout.addStretch()  # Đẩy các label về bên trái
        summary_layout.addLayout(stats_layout)

        layout.addLayout(summary_layout)

        # Create table for entry/exit records
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "RFID", "License Plate", "Entry Time", "Exit Time", "Duration", "Fee"
        ])
        
        # Set column widths
        self.table.setColumnWidth(0, 120)  # RFID
        self.table.setColumnWidth(1, 120)  # License Plate
        self.table.setColumnWidth(2, 160)  # Entry Time
        self.table.setColumnWidth(3, 160)  # Exit Time
        self.table.setColumnWidth(4, 100)  # Duration
        self.table.setColumnWidth(5, 100)  # Fee

        layout.addWidget(self.table)

        # Revenue summary section
        summary_layout = QHBoxLayout()
        
        self.total_revenue_label = QLabel("Total Revenue: 0 VND")
        self.total_revenue_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        layout.addWidget(self.total_revenue_label)
        
        self.setLayout(layout)

        self.update_table()

    def get_filtered_records(self, start_date, end_date):
        """Lấy dữ liệu từ bảng daily_cards trong khoảng thời gian được chọn"""
        with Session(engine) as session:
            stmt = select(DailyCards).where(
                DailyCards.time_in >= start_date,
                DailyCards.time_in <= end_date
            )
            results = session.execute(stmt).scalars().all()
            
            records = []
            for record in results:
                records.append({
                    'rfid': record.rfid_card,
                    'license_plate': record.bien_so_xe,
                    'time_in': record.time_in.strftime("%Y-%m-%d %H:%M:%S") if record.time_in else None,
                    'time_out': record.time_out.strftime("%Y-%m-%d %H:%M:%S") if record.time_out else None
                })
            return records


    def get_filtered_records(self, start_date, end_date):
        """Lấy dữ liệu từ bảng daily_cards dựa trên thời gian xe ra trong khoảng được chọn"""
        with Session(engine) as session:
            stmt = select(DailyCards).where(
                DailyCards.time_out >= start_date,
                DailyCards.time_out < end_date,
                DailyCards.time_out.isnot(None)  # Chỉ lấy những xe đã ra khỏi bãi
            )
            results = session.execute(stmt).scalars().all()
            
            records = []
            for record in results:
                records.append({
                    'rfid': record.rfid_card,
                    'license_plate': record.bien_so_xe,
                    'time_in': record.time_in.strftime("%Y-%m-%d %H:%M:%S") if record.time_in else None,
                    'time_out': record.time_out.strftime("%Y-%m-%d %H:%M:%S") if record.time_out else None
                })
            return records

    def update_table(self):
        self.table.setRowCount(0)
        total_revenue = 0

        # Lấy ngày từ widget
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()+ timedelta(days=1)

        # Cập nhật label hiển thị khoảng thời gian
        self.date_range_label.setText(
            f"Report Period: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        )

        # Lấy dữ liệu từ database trong khoảng thời gian
        records = self.get_filtered_records(start_date, end_date)
        completed_vehicles = len(records)  # Số xe đã hoàn thành là tổng số records vì chỉ lấy xe đã ra
        
        for row, record in enumerate(records):
            self.table.insertRow(row)
            
            entry_time = datetime.strptime(record['time_in'], "%Y-%m-%d %H:%M:%S")
            exit_time = datetime.strptime(record['time_out'], "%Y-%m-%d %H:%M:%S")
            
            # Tính phí
            fee = self.calculate_fee(entry_time, exit_time)
            total_revenue += fee
            
            # Tính duration và chuyển đổi thành chuỗi
            duration = exit_time - entry_time
            hours = duration.total_seconds() / 3600
            duration_str = f"{int(hours)} hours {int((hours % 1) * 60)} min"
            fee_str = f"{fee:,} VND"

            items = [
                record['rfid'],
                record['license_plate'],
                entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                exit_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration_str,
                fee_str
            ]
            
            for col, item in enumerate(items):
                table_item = QTableWidgetItem(str(item))
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, table_item)

        # Cập nhật các label thống kê
        self.total_vehicles_label.setText(
            f"Total Completed Vehicles: {completed_vehicles}"
        )
        self.total_revenue_label.setText(f"Total Revenue: {total_revenue:,} VND")

    def export_to_excel(self):
        """Xuất dữ liệu từ bảng sang file Excel"""
        if self.table.rowCount() == 0:
            return

        # Lấy ngày để đặt tên file
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        # Tạo DataFrame từ dữ liệu trong bảng
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            data.append(row_data)

        df = pd.DataFrame(
            data,
            columns=["RFID", "License Plate", "Entry Time", "Exit Time", "Duration", "Fee"]
        )

        # Tạo file name mặc định
        default_filename = f"revenue_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"

        # Mở dialog để chọn nơi lưu file
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Excel",
            default_filename,
            "Excel Files (*.xlsx)"
        )

        if filename:
            # Đảm bảo filename có đuôi .xlsx
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'

            # Tạo Excel writer
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                # Ghi DataFrame vào sheet đầu tiên
                df.to_excel(writer, sheet_name='Revenue Report', index=False)
                
                # Lấy workbook và worksheet để định dạng
                workbook = writer.book
                worksheet = writer.sheets['Revenue Report']

                # Định dạng tiêu đề
                header_format = workbook.add_format({
                    'bold': True,
                    'align': 'center',
                    'bg_color': '#D8E4BC'
                })

                # Định dạng các cột
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    
                # Điều chỉnh độ rộng cột
                worksheet.set_column('A:B', 15)  # RFID, License Plate
                worksheet.set_column('C:D', 20)  # Entry/Exit Time
                worksheet.set_column('E:E', 12)  # Duration
                worksheet.set_column('F:F', 15)  # Fee

                # Thêm thông tin tổng kết ở cuối
                summary_row = len(df) + 2
                bold_format = workbook.add_format({'bold': True})
                
                worksheet.write(summary_row, 0, 'Report Period:', bold_format)
                worksheet.write(summary_row, 1, f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
                
                worksheet.write(summary_row + 1, 0, 'Total Vehicles:', bold_format)
                worksheet.write(summary_row + 1, 1, str(len(df)))
                
                # Lấy tổng doanh thu
                total_revenue = sum(int(fee.replace(',', '').replace(' VND', '')) for fee in df['Fee'] if 'VND' in fee)
                worksheet.write(summary_row + 2, 0, 'Total Revenue:', bold_format)
                worksheet.write(summary_row + 2, 1, f"{total_revenue:,} VND")


    def calculate_fee(self, entry_time, exit_time):
        """
        Tính phí gửi xe dựa trên thời gian vào và ra, với phí tối đa mỗi ngày là 12.000đ
        Một ngày được tính từ 6h sáng đến 6h sáng hôm sau
        
        Args:
            entry_time (datetime): Thời gian vào
            exit_time (datetime): Thời gian ra
            
        Returns:
            int: Số tiền phải trả (VND)
        """
        if exit_time < entry_time:
            raise ValueError("Thời gian ra phải sau thời gian vào")
        
        def get_day_start(dt):
            """Trả về thời điểm 6h sáng của ngày tính phí chứa dt"""
            if dt.hour < 6:
                return (dt - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
            return dt.replace(hour=6, minute=0, second=0, microsecond=0)
        
        total_fee = 0
        current_time = entry_time
        daily_fee = 0
        current_day_start = get_day_start(entry_time)
        next_day_start = current_day_start + timedelta(days=1)
        
        while current_time < exit_time:
            # Kiểm tra nếu đã sang ngày mới (sau 6h sáng)
            if current_time >= next_day_start:
                # Cập nhật tổng phí với phí của ngày trước (tối đa 12.000đ)
                total_fee += min(daily_fee, 12000)
                daily_fee = 0
                current_day_start = next_day_start
                next_day_start = current_day_start + timedelta(days=1)
            
            # Lấy thời điểm kết thúc của khoảng thời gian hiện tại
            if current_time.hour < 6:
                # Đang trong khung đêm, tính đến 6h sáng
                period_end = current_time.replace(hour=6, minute=0, second=0, microsecond=0)
                if period_end > exit_time:
                    period_end = exit_time
                fee_rate = 10000  # Phí ban đêm
            elif current_time.hour < 18:
                # Đang trong khung ngày, tính đến 18h
                period_end = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
                if period_end > exit_time:
                    period_end = exit_time
                fee_rate = 5000  # Phí ban ngày
            else:
                # Đang trong khung đêm, tính đến 6h sáng hôm sau
                period_end = (current_time + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
                if period_end > exit_time:
                    period_end = exit_time
                fee_rate = 10000  # Phí ban đêm
            
            # Cộng phí vào phí ngày hiện tại
            daily_fee += fee_rate
            
            # Chuyển sang khoảng thời gian tiếp theo
            current_time = period_end
        
        # Thêm phí của ngày cuối cùng (tối đa 12.000đ)
        total_fee += min(daily_fee, 12000)
        
        return total_fee


# Code để chạy trực tiếp file này
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create main window to hold the tab
    main_window = QWidget()
    main_window.setWindowTitle("Doanh thu")
    main_window.setGeometry(100, 100, 800, 600)
    
    # Create layout for main window
    layout = QVBoxLayout(main_window)

    
    # Create revenue management tab
    revenue_tab = RevenueManagementTab()
    layout.addWidget(revenue_tab)
    
    main_window.show()
    sys.exit(app.exec())
