from database.SqlAlchemyDatabase import SqlAlchemyBase

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "users"
    serialize_only = ("tg_id", "name", "score")

    tg_id = Column(Integer, primary_key=True)
    name = Column(String(320), nullable=False)
    score = Column(Integer, nullable=False)
    completed = Column(Boolean, nullable=False)

    def __repr__(self) -> str:
        return str(self.to_dict())
