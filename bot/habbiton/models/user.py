from sqlalchemy import Integer, String, Date, select, ForeignKey, update
from habbiton import Base, session
from sqlalchemy.orm import mapped_column
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String, nullable=True)
    start_date = mapped_column(Date, nullable=True, default = datetime.now().date())
    current_level = mapped_column(ForeignKey("levels.name"), nullable=False,  default="main")
    latest_msg_id = mapped_column(Integer, nullable=True)
    session = session

    @classmethod
    def set_session(cls, session) -> None:
        cls.session = session

    @classmethod
    async def from_id(cls, id: int) -> 'User':
        async with cls.session() as ses:
            stmt = select(cls).where(cls.id == id)
            return (await ses.execute(stmt)).scalar()
        
    @classmethod
    async def new(cls, id: int, name: str) -> 'User':
        try:
            async with cls.session() as ses:
                ses.add(cls(id = id, username = name))
                await ses.commit()
        except:
            pass
        
        return await cls.from_id(id)
    
    async def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
        async with self.session() as ses:
            stm = update(User).where(User.id == self.id).values(**kwargs)
            await ses.execute(stm)
            await ses.commit()
    