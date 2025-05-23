import datetime
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.orm import Session, selectinload
from db.models import UserCreate, RequestCreate
from db.tables import User, Request
from db.client import db_client


def create_user(
		session: Session, new_user: UserCreate
) -> User | None:
	new_user = User(**new_user.model_dump())
	session.add(new_user)
	session.commit()
	return new_user


def get_user(session: Session, user_id: int) -> User | None:
	current_user = session.scalar(select(User).where(User.user_id == user_id).options(
		selectinload(User.user_requests)
	))
	return current_user


def get_users(session: Session) -> List[User]:
	users = session.scalars(select(User).options(
		selectinload(User.user_requests)
	)).all()
	return [u for u in users]


def check_user(session: Session, user_id: int) -> bool:
	_user = session.scalars(select(User).where(User.user_id == user_id)).one_or_none()
	return _user is not None


def create_request(
		session: Session, new_request: RequestCreate
):
	request = Request(**new_request.model_dump())
	session.add(request)
	session.commit()
	return request


def get_user_requests_count(session: Session, user_id: int) -> int:
	user_requests = session.scalars(select(Request).where(Request.user_id == user_id)).all()
	req_count = len(user_requests)
	print(f'Найдено {req_count} запросов пользователя ID {user_id}:')
	return req_count


def get_user_requests(session: Session, user_id: int):
	user_requests = session.scalars(select(Request).where(Request.user_id == user_id)).all()
	return user_requests


def get_last_user_request_by_type(session: Session, user_id: int, req_type: int):
	last_request = session.scalars(select(Request).where(
		and_(Request.user_id == user_id, Request.request_type == req_type)
	).order_by(Request.request_timestamp.desc())).first()
	return last_request


if __name__ == '__main__':
	db_client.re_create()
	_new_user: UserCreate = UserCreate(
		user_id=32243,
		user_name="username",
		user_phone='79111212',
		user_reg_timestamp=datetime.datetime.now()
	)

	_new_request = RequestCreate(
		user_id=32243,
		request_data="awdawdawd",
		request_type=2,
		request_timestamp=datetime.datetime.now()
	)
	with db_client.session_factory() as _session:
		user = create_user(_session, _new_user)
		print(check_user(_session, user.user_id))
		print(check_user(_session, 444))
		create_request(_session, _new_request)


