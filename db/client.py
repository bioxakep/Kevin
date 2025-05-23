from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from config import bot_config
from db.tables import BotBase


class SQLiteClient:
	def __init__(self, echo: bool = False):
		self.engine = create_engine(
			url=f"sqlite:///{bot_config.db_path}", echo=echo
		)
		self.session_factory = sessionmaker(
			bind=self.engine,
			autoflush=False,
			autocommit=False,
			expire_on_commit=False,
		)
		self.metadata = MetaData()
		self.metadata.reflect(bind=self.engine)

	def re_create(self):
		try:
			tables = list(self.metadata.tables)
			for t in tables:
				table = self.metadata.tables.get(t)
				table.drop(self.engine, checkfirst=True)
				self.metadata.remove(table)
			self.metadata = BotBase.metadata
			self.metadata.create_all(bind=self.engine)
			return True, "OK"
		except Exception as e:
			return False, ','.join(e.args)

	def __enter__(self):
		return self


db_client = SQLiteClient()

if __name__ == '__main__':
	db_client.re_create()
