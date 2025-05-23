import datetime
from typing import Annotated

from annotated_types import MinLen, MaxLen
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
	user_id: int
	user_name: Annotated[str, MinLen(3), MaxLen(20)]
	user_phone: str
	user_reg_timestamp: datetime.datetime


class UserCreate(UserBase):
	pass


class UserModel(UserBase):
	model_config = ConfigDict(from_attributes=True)
	id: int


class RequestBase(BaseModel):
	request_type: int
	request_data: str
	request_timestamp: datetime.datetime
	user_id: int


class RequestCreate(RequestBase):
	pass


class RequestModel(RequestBase):
	model_config = ConfigDict(from_attributes=True)
	id: int
