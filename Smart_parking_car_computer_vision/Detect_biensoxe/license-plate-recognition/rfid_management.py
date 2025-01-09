from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
# from database import UserNameMonthly, engine, DailyTicket
from create_database import RFIDList, MonthlyCards, DailyCards, engine
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QFormLayout, QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QGridLayout
from datetime import datetime, timedelta

# Tạo Session từ engine
Session = sessionmaker(bind=engine)
session = Session()

class RFIDManagementWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RFID Management")
        self.setGeometry(150, 150, 800, 400)  # Điều chỉnh kích thước cửa sổ

        # Sử dụng QGridLayout
        self.layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Form for Adding New User
        self.form_layout = QFormLayout()

        self.rfid_input = QLineEdit()
        self.name_input = QLineEdit()
        self.plate_input = QLineEdit()
        self.card_type = QLineEdit()

        self.daily_ticket_manager = DailyTicketManager(session)

        self.form_layout.addRow("RFID Code:", self.rfid_input)
        self.form_layout.addRow("Name:", self.name_input)
        self.form_layout.addRow("License Plate:", self.plate_input)
        self.form_layout.addRow("Card Type:", self.card_type)

        # Thêm form vào layout
        self.layout.addLayout(self.form_layout, 0, 0, 1, 2)  # Chiếm 2 cột

        # Tạo các nút
        self.add_user_button = QPushButton("Add New User")
        self.add_user_button.clicked.connect(self.add_new_user)

        self.add_card_button = QPushButton("Add New RFID Card")
        self.add_card_button.clicked.connect(self.add_new_rfid_card)

        self.remove_card_button = QPushButton("Remove Selected User")
        self.remove_card_button.clicked.connect(self.remove_selected_user)

        self.list_monthly_users_button = QPushButton("List Users Monthly")
        self.list_monthly_users_button.clicked.connect(self.list_all_users)

        self.list_daily_users_button = QPushButton("List Users Daily")
        self.list_daily_users_button.clicked.connect(self.list_daily_tickets)

        self.list_rfid_button = QPushButton("List RFID Cards")
        self.list_rfid_button.clicked.connect(self.list_rfid_cards)  # Thêm hàm mới

        # Sắp xếp các nút thành 2 cột
        self.layout.addWidget(self.add_user_button, 1, 0)
        self.layout.addWidget(self.add_card_button, 1, 1)
        self.layout.addWidget(self.remove_card_button, 2, 0)
        self.layout.addWidget(self.list_monthly_users_button, 2, 1)
        self.layout.addWidget(self.list_daily_users_button, 3, 0)
        self.layout.addWidget(self.list_rfid_button, 3, 1)

        # Table to display users
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["RFID Code", "Name", "License Plate"])
        self.layout.addWidget(self.user_table, 4, 0, 1, 2)  # Chiếm 2 cột


    def add_new_user(self):
        rfid = self.rfid_input.text()
        name = self.name_input.text()
        license_plate = self.plate_input.text()
        # ticket_type = self.ticket_type_input.text()

        if rfid and name and license_plate:
            try:
                # ticket_type_bool = ticket_type.lower() == 'true'
                new_user = MonthlyCards(user_name=name, bien_so_xe=license_plate, rfid_card=rfid)
                session.add(new_user)
                session.commit()
                self.rfid_input.clear()
                self.name_input.clear()
                self.plate_input.clear()
                # self.ticket_type_input.clear()
                print("User added successfully.")
                self.list_all_users()
            except Exception as e:
                session.rollback()
                print("Error adding user:", e)
        else:
            print("Please fill in all fields.")

    def add_new_rfid_card(self):
        rfid = self.rfid_input.text()
        card_type = self.card_type.text()

        if rfid and card_type:
            try:
                # ticket_type_bool = ticket_type.lower() == 'true'
                new_user = RFIDList(rfid_card=rfid, card_type=card_type)
                session.add(new_user)
                session.commit()
                self.rfid_input.clear()
                self.card_type.clear()
                print("User added successfully.")
                self.list_rfid_cards()
            except Exception as e:
                session.rollback()
                print("Error adding user:", e)
        else:
            print("Please fill in all fields.")

    def remove_selected_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row != -1:
            rfid = self.user_table.item(selected_row, 0).text()
            user = session.query(MonthlyCards).filter_by(rfid_card=rfid).first()
            if user:
                session.delete(user)
                session.commit()
                print(f"User with RFID {rfid} removed successfully.")
                self.list_all_users()
            else:
                print("Selected user not found in the database.")
        else:
            print("Please select a user to remove.")

    def list_all_users(self):
        """Liệt kê tất cả người dùng có vé tháng."""
        users = session.query(MonthlyCards).all()

        # Đảm bảo bảng hiển thị đúng 3 cột
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["RFID Code", "Name", "License Plate"])

        # Clear bảng hiển thị
        self.user_table.setRowCount(0)

        # Hiển thị dữ liệu nếu có
        self.user_table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            self.user_table.setItem(row_idx, 0, QTableWidgetItem(user.rfid_card))
            self.user_table.setItem(row_idx, 1, QTableWidgetItem(user.user_name))
            self.user_table.setItem(row_idx, 2, QTableWidgetItem(user.bien_so_xe))

    def list_daily_tickets(self):
        """Liệt kê tất cả vé ngày."""
        tickets = session.query(DailyCards).all()

        # Đảm bảo bảng hiển thị đúng 4 cột
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["RFID", "License Plate", "Time In", "Time Out"])

        # Clear bảng hiển thị
        self.user_table.setRowCount(0)

        # Nếu có vé ngày, hiển thị thông tin lên bảng
        if tickets:
            self.user_table.setRowCount(len(tickets))

            for row_idx, ticket in enumerate(tickets):
                self.user_table.setItem(row_idx, 0, QTableWidgetItem(ticket.rfid_card))
                self.user_table.setItem(row_idx, 1, QTableWidgetItem(ticket.bien_so_xe))
                self.user_table.setItem(row_idx, 2, QTableWidgetItem(ticket.time_in.strftime('%Y-%m-%d %H:%M:%S')))
                self.user_table.setItem(row_idx, 3, QTableWidgetItem(ticket.time_out.strftime('%Y-%m-%d %H:%M:%S') if ticket.time_out else ""))
        else:
            # Nếu không có vé ngày, vẫn giữ tiêu đề cột và một hàng trống
            self.user_table.setRowCount(1)
            for col_idx in range(4):
                self.user_table.setItem(0, col_idx, QTableWidgetItem(""))
            print("No daily tickets found.")

    def list_rfid_cards(self):
        """Hiển thị danh sách các thẻ RFID từ bảng rfid_list."""
        rfids = session.query(RFIDList).all()

        # Clear bảng hiển thị
        self.user_table.setRowCount(0)

        # Đảm bảo bảng có 2 cột
        self.user_table.setColumnCount(2)
        self.user_table.setHorizontalHeaderLabels(["RFID Card", "Card Type"])

        if rfids:
            self.user_table.setRowCount(len(rfids))
            for row_idx, rfid in enumerate(rfids):
                self.user_table.setItem(row_idx, 0, QTableWidgetItem(rfid.rfid_card))
                self.user_table.setItem(row_idx, 1, QTableWidgetItem(rfid.card_type))
        else:
            print("No RFID cards found.")



    def closeEvent(self, event):
        session.close()

    def get_rfid_month_from_plate(self, license_plate):
        """Truy vấn RFID từ biển số xe"""
        user = session.query(MonthlyCards).filter_by(bien_so_xe=license_plate).first()
        if user:
            return user.rfid_card
        else:
            return None  # Nếu không tìm thấy
    
    def get_rfid_day_from_plate(self, bien_so_xe):
        """Truy vấn RFID ngày từ biển số xe"""
        # Kiểm tra bản ghi mới nhất của RFID
        latest_ticket = (
            session.query(DailyCards)
            .filter(DailyCards.bien_so_xe == bien_so_xe)
            .order_by(DailyCards.id.desc())
            .first()
        )

        if latest_ticket and latest_ticket.time_out is None:
            print(f"{bien_so_xe} đã tồn tại trong DailyCards với id={latest_ticket.id} và chưa có time_out.")
            return latest_ticket.rfid_card
        elif latest_ticket:
            # print(f"xe {bien_so_xe} đã ra khỏi bãi")
            return 
        
class DailyTicketManager:
    def __init__(self, session):
        self.session = session
    def add_daily_ticket(self, rfid_card, bien_so_xe, time_in=None):
        """Cập nhật thông tin vé ngày với biển số xe và thời gian vào."""
        if time_in is None:
            time_in = datetime.utcnow() + timedelta(hours=7)
            
        try:
            # Kiểm tra bản ghi mới nhất của RFID
            latest_ticket = (
                self.session.query(DailyCards)
                .filter(DailyCards.rfid_card == rfid_card)
                .order_by(DailyCards.id.desc())
                .first()
            )

            if latest_ticket and latest_ticket.time_out is None:
                print(f"RFID {rfid_card} đã tồn tại trong DailyCards với id={latest_ticket.id} và chưa có time_out.")
                return
            elif latest_ticket:
                print(f"RFID {rfid_card} đã có time_out trong bản ghi gần nhất (id={latest_ticket.id}). Thêm mới bản ghi.")

            # Tạo bản ghi mới trong bảng DailyCards
            new_ticket = DailyCards(rfid_card=rfid_card, bien_so_xe=bien_so_xe, time_in=time_in)
            self.session.add(new_ticket)
            self.session.commit()
            print(f"Added new daily ticket for RFID {rfid_card} with license plate {bien_so_xe}.")
            
        except Exception as e:
            self.session.rollback()
            print(f"Error adding new daily ticket for RFID {rfid_card}: {e}")


    def update_time_out(self, rfid_card, time_out=None):
        """Cập nhật thời gian ra cho vé ngày."""
        time_out = datetime.utcnow() + timedelta(hours=7)
        try:
            # Tìm bản ghi mới nhất chưa có time_out
            latest_ticket = (
                self.session.query(DailyCards)
                .filter(
                    DailyCards.rfid_card == rfid_card,
                    DailyCards.time_out.is_(None)  # Chỉ lấy bản ghi chưa có time_out
                )
                .order_by(DailyCards.id.desc())
                .first()
            )

            if not latest_ticket:
                print(f"No daily ticket found for RFID {rfid_card}.")
                return

            # Cập nhật time_out
            latest_ticket.time_out = time_out
            try:
                self.session.commit()
                print(f"Time out for RFID {rfid_card} (id={latest_ticket.id}) updated successfully.")
            except Exception as e:
                self.session.rollback()
                print(f"Error updating time out for RFID {rfid_card}: {e}")
        except Exception as e:
            print(f"Error processing RFID {rfid_card}: {e}")

    def update_time_in(self, rfid_card, time_in=None):
        """Cập nhật thời gian vào cho vé ngày."""
        if time_in is None:
            time_in = datetime.utcnow() + timedelta(hours=7)
        ticket = self.session.query(DailyCards).filter_by(rfid_card=rfid_card).first()
        if ticket:
            ticket.time_in = time_in
            try:
                self.session.commit()
                print(f"Time in for RFID {rfid_card} updated successfully.")
            except Exception as e:
                self.session.rollback()
                print("Error updating time in:", e)
        else:
            print(f"No daily ticket found for RFID {rfid_card}.")

    def list_daily_tickets(self):
        """Liệt kê tất cả vé ngày."""
        tickets = session.query(DailyCards).all()

        # Clear bảng hiển thị
        self.user_table.setRowCount(0)

        # Nếu có vé ngày, hiển thị thông tin lên bảng
        if tickets:
            self.user_table.setRowCount(len(tickets))
            self.user_table.setColumnCount(4)  # Đảm bảo bảng có 4 cột
            self.user_table.setHorizontalHeaderLabels(["RFID", "License Plate", "Time In", "Time Out"])

            for row_idx, ticket in enumerate(tickets):
                self.user_table.setItem(row_idx, 0, QTableWidgetItem(ticket.rfid_card))
                self.user_table.setItem(row_idx, 1, QTableWidgetItem(ticket.bien_so_xe))
                self.user_table.setItem(row_idx, 2, QTableWidgetItem(ticket.time_in.strftime('%Y-%m-%d %H:%M:%S')))
                self.user_table.setItem(row_idx, 3, QTableWidgetItem(ticket.time_out.strftime('%Y-%m-%d %H:%M:%S') if ticket.time_out else ""))
        else:
            print("No daily tickets found.")

    def handle_rfid_message(self, rfid_message, bien_so_xe):
        """
        Xử lý dữ liệu từ topic "esp32/rfid_send".
        Nếu RFID chưa tồn tại trong bảng daily_ticket, gọi hàm add_daily_ticket từ DailyTicketManager.
        """
        try:
            # Lấy thời gian hiện tại
            current_time = datetime.utcnow() + timedelta(hours=7)

            # Lấy RFID từ tin nhắn và loại bỏ khoảng trắng
            rfid_card = rfid_message.strip()

            # Kiểm tra RFID trong bảng daily_ticket
            existing_ticket = session.query(RFIDList).filter_by(rfid_card=rfid_card).first()

            if existing_ticket:
                                # Gọi hàm add_daily_ticket để cập nhật thông tin
                self.add_daily_ticket(
                    rfid_card=rfid_card,
                    bien_so_xe=bien_so_xe,
                    time_in=current_time
                )
                print("done add card daily")

        except Exception as e:
            print(f"Error handling RFID message: {e}")



        
    

