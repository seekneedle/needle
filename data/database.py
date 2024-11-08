from sqlalchemy import create_engine, Column, Integer, String, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr, DeclarativeMeta
from contextlib import contextmanager
import traceback
from utils.log import log

# 创建一个基类，用于定义表结构
Base = declarative_base()

# 创建数据库引擎和Session
engine = create_engine('sqlite:///res/example.db', echo=False)
Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    _session = Session()
    try:
        yield _session
    except Exception as e:
        _session.rollback()
        trace_info = traceback.format_exc()
        log.error(f'Exception for session_scope, e: {e}, trace: {trace_info}')
    finally:
        _session.close()


# 定义一个元类，用于在子类定义时自动创建表
class AutoCreateTableMeta(DeclarativeMeta):
    def __init__(cls, name, bases, dict_):
        super(AutoCreateTableMeta, cls).__init__(name, bases, dict_)
        if name != 'TableModel' and issubclass(cls, TableModel):
            cls.__table__.create(bind=engine, checkfirst=True)


# 定义一个通用的数据表类
class TableModel(Base, metaclass=AutoCreateTableMeta):
    __abstract__ = True

    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)

    def get(self):
        with session_scope() as session:
            # 获取模型的所有列
            columns = inspect(self.__class__).columns
            # 构建查询条件
            filters = {column.name: getattr(self, column.name) for column in columns if
                       getattr(self, column.name) is not None}
            # 执行查询
            result = session.query(self.__class__).filter_by(**filters).first()
            if result:
                # 更新 get_user 的所有列
                for column in columns:
                    setattr(self, column.name, getattr(result, column.name))

    def save(self):
        with session_scope() as session:
            if self.id:
                session.merge(self)
                session.commit()
            else:
                session.add(self)
                session.commit()
                session.refresh(self)

    def delete(self):
        with session_scope() as session:
            session.query(self.__class__).filter_by(id=self.id).delete()
            session.commit()


if __name__ == '__main__':
    class User(TableModel):
        name = Column(String)


    user = User(name='a')
    user.save()

    print(user.id)
    print(user.name)

    user.name = 'b'
    user.save()

    print(user.id)
    print(user.name)

    with session_scope() as query_session:
        user1 = query_session.query(User).filter_by(id=1).first()
        if user1:
            print('first user')
            print(user1.id)
            print(user1.name)
        user2 = query_session.query(User).filter_by(id=2).first()
        if user2:
            print('second user')
            print(user2.id)
            print(user2.name)

    get_user = User(name='b')
    get_user.get()
    print('get_user:')
    print(get_user.id)
    print(get_user.name)

    get_user.name = 'c'
    get_user.save()
    print(get_user.id)
    print(get_user.name)

    with session_scope() as query_session:
        user1 = query_session.query(User).filter_by(id=1).first()
        if user1:
            print('first user')
            print(user1.id)
            print(user1.name)
        user2 = query_session.query(User).filter_by(id=2).first()
        if user2:
            print('second user')
            print(user2.id)
            print(user2.name)

    get_user.delete()

    print('删除user')

    with session_scope() as query_session:
        user1 = query_session.query(User).filter_by(id=1).first()
        if user1:
            print('first user')
            print(user1.id)
            print(user1.name)
        user2 = query_session.query(User).filter_by(id=2).first()
        if user2:
            print('second user')
            print(user2.id)
            print(user2.name)
