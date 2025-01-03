from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database import UserNameMonthly, engine
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QFormLayout, QLineEdit, QLabel, QTableWidget, QTableWidgetItem

# Tạo Session từ engine
Session = sessionmaker(bind=engine)
session = Session()

class RFIDManagementWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RFID Management")
        self.setGeometry(150, 150, 600, 400)

        self.layout = QVBoxLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Form for Adding New User
        self.form_layout = QFormLayout()

        self.rfid_input = QLineEdit()
        self.name_input = QLineEdit()
        self.plate_input = QLineEdit()

        self.form_layout.addRow("RFID Code:", self.rfid_input)
        self.form_layout.addRow("Name:", self.name_input)
        self.form_layout.addRow("License Plate:", self.plate_input)

        self.add_card_button = QPushButton("Add New User")
        self.add_card_button.clicked.connect(self.add_new_user)

        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.add_card_button)

        # Remove User Button
        self.remove_card_button = QPushButton("Remove Selected User")
        self.remove_card_button.clicked.connect(self.remove_selected_user)
        self.layout.addWidget(self.remove_card_button)

        # List All Users Button
        self.list_cards_button = QPushButton("List All Users")
        self.list_cards_button.clicked.connect(self.list_all_users)
        self.layout.addWidget(self.list_cards_button)

        # Table to display users
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["RFID Code", "Name", "License Plate"])
        self.layout.addWidget(self.user_table)

    def add_new_user(self):
        rfid = self.rfid_input.text()
        name = self.name_input.text()
        license_plate = self.plate_input.text()

        if rfid and name and license_plate:
            new_user = UserNameMonthly(user_name=name, bien_so_xe=license_plate, rfid_card=rfid)
            try:
                session.add(new_user)
                session.commit()
                self.rfid_input.clear()
                self.name_input.clear()
                self.plate_input.clear()
                print("User added successfully.")
                self.list_all_users()
            except Exception as e:
                session.rollback()
                print("Error adding user:", e)
        else:
            print("Please fill in all fields.")

    def remove_selected_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row != -1:
            rfid = self.user_table.item(selected_row, 0).text()
            user = session.query(UserNameMonthly).filter_by(rfid_card=rfid).first()
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
        users = session.query(UserNameMonthly).all()

        self.user_table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            self.user_table.setItem(row_idx, 0, QTableWidgetItem(user.rfid_card))
            self.user_table.setItem(row_idx, 1, QTableWidgetItem(user.user_name))
            self.user_table.setItem(row_idx, 2, QTableWidgetItem(user.bien_so_xe))

    def closeEvent(self, event):
        session.close()

    def get_rfid_from_plate(self, license_plate):
        """Truy vấn RFID từ biển số xe"""
        user = session.query(UserNameMonthly).filter_by(bien_so_xe=license_plate).first()
        if user:
            return user.rfid_card
        else:
            return None  # Nếu không tìm thấy

