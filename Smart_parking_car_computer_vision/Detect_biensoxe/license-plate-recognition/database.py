from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Khởi tạo ORM Base
Base = declarative_base()

# Định nghĩa bảng user_name_monthly với thêm cột loai_ve
class UserNameMonthly(Base):
    __tablename__ = 'user_name_monthly'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255), nullable=False)
    bien_so_xe = Column(String(255), nullable=False)
    rfid_card = Column(String(255), unique=True, nullable=False)
    ve_thang = Column(String(50), nullable=True)  # Thêm cột loai_ve
    # Quan hệ với bảng DailyTicket
    daily_tickets = relationship("DailyTicket", back_populates="user")

class DailyTicket(Base):
    __tablename__ = 'daily_ticket'

    rfid_card = Column(String(255), ForeignKey('user_name_monthly.rfid_card'), primary_key=True)
    bien_so_xe = Column(String(255), nullable=True)  # Thêm cột bien_so_xe
    time_in = Column(DateTime, nullable=True)
    time_out = Column(DateTime, nullable=True)

    # Quan hệ với bảng UserNameMonthly (không bắt buộc)
    user = relationship("UserNameMonthly", back_populates="daily_tickets")

# Kết nối đến SQLite Database
DATABASE_URL = "sqlite:///E:/AVR/CV/Project/Smart_Parking_Car_DATN/danh_sach1.db"
engine = create_engine(DATABASE_URL)

# Tạo bảng nếu chưa tồn tại
Base.metadata.create_all(engine)
print("Database and table created successfully")

# Tạo Session để thao tác với Database
Session = sessionmaker(bind=engine)
session = Session()

class DailyTicketManager:
    def __init__(self, session):
        self.session = session

    def add_daily_ticket(self, rfid_card, time_in=None):
        """Thêm vé ngày mới."""
        if time_in is None:
            time_in = datetime.utcnow()
        daily_ticket = DailyTicket(rfid_card=rfid_card, time_in=time_in)
        try:
            self.session.add(daily_ticket)
            self.session.commit()
            print(f"Daily ticket for RFID {rfid_card} added successfully.")
        except Exception as e:
            self.session.rollback()
            print("Error adding daily ticket:", e)

    def update_time_out(self, rfid_card, time_out=None):
        """Cập nhật thời gian ra cho vé ngày."""
        if time_out is None:
            time_out = datetime.utcnow()
        ticket = self.session.query(DailyTicket).filter_by(rfid_card=rfid_card).first()
        if ticket:
            ticket.time_out = time_out
            try:
                self.session.commit()
                print(f"Time out for RFID {rfid_card} updated successfully.")
            except Exception as e:
                self.session.rollback()
                print("Error updating time out:", e)
        else:
            print(f"No daily ticket found for RFID {rfid_card}.")

    def list_daily_tickets(self):
        """Liệt kê tất cả vé ngày."""
        tickets = self.session.query(DailyTicket).all()
        for ticket in tickets:
            print(f"RFID: {ticket.rfid_card}, Time In: {ticket.time_in}, Time Out: {ticket.time_out}")

# Sử dụng lớp DailyTicketManager
manager = DailyTicketManager(session)

# Thêm ví dụ sử dụng
manager.add_daily_ticket(rfid_card="123456789", time_in=datetime(2025, 1, 1, 8, 0, 0))
manager.update_time_out(rfid_card="123456789", time_out=datetime(2025, 1, 1, 18, 0, 0))
manager.list_daily_tickets()
new_ticket = DailyTicket(
    rfid_card="2202032483",  # Giá trị của cột rfid_card
    bien_so_xe=None,  # Giá trị mẫu cho biển số xe
    time_in=None,  # Thời gian vào hiện tại
    time_out=None  # Thời gian ra để trống
)

# Thêm bản ghi vào session và commit
try:
    session.add(new_ticket)
    session.commit()
    print("New ticket added successfully.")
except Exception as e:
    session.rollback()
    print("Error adding new ticket:", e)