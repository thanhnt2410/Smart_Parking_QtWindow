from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Khởi tạo ORM Base
Base = declarative_base()

# Định nghĩa bảng user_name_monthly
class UserNameMonthly(Base):
    __tablename__ = 'user_name_monthly'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255), nullable=False)
    bien_so_xe = Column(String(255), nullable=False)
    rfid_card = Column(String(255), unique=True, nullable=False)

# Kết nối đến SQLite Database
DATABASE_URL = "sqlite:///E:/AVR/CV/Project/Smart_Parking_Car_DATN/danh_sach.db"
engine = create_engine(DATABASE_URL)

# Tạo bảng nếu chưa tồn tại
Base.metadata.create_all(engine)
print("Database and table created successfully.")

# Tạo Session để thao tác với Database
Session = sessionmaker(bind=engine)
session = Session()

# Ví dụ thêm dữ liệu vào bảng
# new_user = UserNameMonthly(user_name="Nguyen Van A", bien_so_xe="30E-12345", rfid_card="123456789")
# session.add(new_user)
# session.commit()
# print("New user added successfully.")

# Lấy tất cả dữ liệu từ bảng
users = session.query(UserNameMonthly).all()
for user in users:
    print(f"ID: {user.user_id}, Name: {user.user_name}, Plate: {user.bien_so_xe}, RFID: {user.rfid_card}")
