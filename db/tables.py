import datetime

from sqlalchemy import MetaData, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BotBase(DeclarativeBase):
	__abstract__ = True
	metadata = MetaData()
	id: Mapped[int] = mapped_column(primary_key=True)


class User(BotBase):
	__tablename__ = "users"

	user_id: Mapped[int] = mapped_column(unique=True)
	user_name: Mapped[str] = mapped_column(nullable=True)
	user_phone: Mapped[str] = mapped_column(nullable=True)
	user_reg_timestamp: Mapped[datetime.datetime] = mapped_column(nullable=False)

	user_requests = relationship("Request", back_populates="user", cascade="all, delete-orphan")


class Request(BotBase):
	__tablename__ = "requests"

	request_data: Mapped[str] = mapped_column(nullable=False)
	request_type: Mapped[int] = mapped_column(nullable=False)
	request_timestamp: Mapped[datetime.datetime] = mapped_column(nullable=False)

	user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
	user = relationship("User", back_populates="user_requests")
