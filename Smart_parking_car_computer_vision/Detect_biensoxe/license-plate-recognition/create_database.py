from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Khởi tạo ORM Base
Base = declarative_base()

# Bảng 1: Danh sách các thẻ RFID
class RFIDList(Base):
    __tablename__ = 'rfid_list'

    rfid_card = Column(String(255), primary_key=True)  # Khóa chính
    card_type = Column(String(50), nullable=False)     # Loại thẻ: 'day' hoặc 'month'

    # Quan hệ với bảng MonthlyCards và DailyCards
    monthly_card = relationship("MonthlyCards", back_populates="rfid_info", uselist=False)
    # daily_card = relationship("DailyCards", back_populates="rfid_info", uselist=False)

# Bảng 2: Thẻ tháng
class MonthlyCards(Base):
    __tablename__ = 'monthly_cards'

    rfid_card = Column(String(255), ForeignKey('rfid_list.rfid_card'), primary_key=True)
    user_name = Column(String(255), nullable=False)    # Họ tên
    bien_so_xe = Column(String(255), nullable=False)   # Biển số xe

    # Quan hệ với bảng RFIDList
    rfid_info = relationship("RFIDList", back_populates="monthly_card")

# Bảng 3: Thẻ ngày
class DailyCards(Base):
    __tablename__ = 'daily_cards'

    id = Column(Integer, primary_key=True, autoincrement=True)  # ID tự động tăng, làm khóa chính
    rfid_card = Column(String(255), nullable=False)  # Không còn là khóa chính
    bien_so_xe = Column(String(255), nullable=True)    # Biển số xe
    time_in = Column(DateTime, nullable=True)          # Thời gian vào
    time_out = Column(DateTime, nullable=True)         # Thời gian ra
    # Các cột mới
    tien = Column(Integer, nullable=True, default=0)   # Số tiền (float, giá trị mặc định là 0.0)
    img_in = Column(String(255), nullable=True)        # Đường dẫn hoặc tên file ảnh vào
    img_out = Column(String(255), nullable=True)       # Đường dẫn hoặc tên file ảnh ra

    # # Quan hệ với bảng RFIDList
    # rfid_info = relationship("RFIDList", back_populates="daily_card")

# Kết nối đến SQLite Database
DATABASE_URL = "sqlite:///E:/AVR/CV/Project/Smart_Parking_Car_DATN/rfid_management.db"
engine = create_engine(DATABASE_URL)

# Tạo bảng nếu chưa tồn tại
Base.metadata.create_all(engine)
print("Database and tables created successfully.")

# Tạo Session để thao tác với Database
Session = sessionmaker(bind=engine)
session = Session()

# Thêm dữ liệu mẫu
try:
    # Thêm thẻ RFID vào danh sách
    rfid_day = RFIDList(rfid_card="2202032483", card_type="day")
    rfid_month = RFIDList(rfid_card="1234567890", card_type="month")

    # Thêm thông tin thẻ tháng
    monthly_card = MonthlyCards(
        rfid_card="1234567890",
        user_name="Nguyen Van A",
        bien_so_xe="30A-12345"
    )

    # Thêm thông tin thẻ ngày
    daily_card = DailyCards(
        rfid_card="2202032483",
        bien_so_xe="29B-67890",
        time_in=None,
        time_out=None
    )

    # Thêm vào session
    session.add_all([rfid_day, rfid_month, monthly_card, daily_card])
    session.commit()
    print("Sample data added successfully.")
except Exception as e:
    session.rollback()
    print("Error adding sample data:", e)

# Kiểm tra dữ liệu
rfids = session.query(RFIDList).all()
print("RFID List:")
for rfid in rfids:
    print(f"RFID: {rfid.rfid_card}, Type: {rfid.card_type}")
