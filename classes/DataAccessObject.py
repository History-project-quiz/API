import sqlalchemy.exc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class DataAccessObject:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def delete_object(self, db_object):
        await self.session.delete(db_object)
        await self.session.commit()

    async def add_object(self, db_object) -> bool:
        self.session.add(db_object)
        try:
            await self.session.commit()
            return True
        except sqlalchemy.exc.IntegrityError:
            return False

    async def get_objects(self, db_class,
                          offset: int = None,
                          limit: int = None,
                          property_filter: list = None,
                          join: list = None,
                          orm_relationship: list = None):
        stmt = select(db_class)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        if join is not None:
            for el in join:
                stmt = stmt.join(el)
        if property_filter is not None:
            for property_el in property_filter:
                stmt = stmt.where(property_el[0] == property_el[1])
        if orm_relationship is not None:
            for relationship in orm_relationship:
                stmt = stmt.options(selectinload(relationship))
        db_object = (await self.session.execute(stmt)).all()
        return db_object
