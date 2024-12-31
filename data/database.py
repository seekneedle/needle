from sqlalchemy import create_engine, Column, Integer, String, inspect, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from contextlib import contextmanager
import traceback

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
        print(f'Exception for session_scope, e: {e}, trace: {trace_info}')
    finally:
        _session.close()


# 定义一个通用的数据表类
class TableModel(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    modify_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    @classmethod
    def query_by_column_value(cls, column_name, value):
        """
        Query the database for the first entry matching a specific column value.
        Returns the first matching instance or None if not found.
        """
        with session_scope() as session:
            return session.query(cls).filter(getattr(cls, column_name) == value).first()
        
    def load(self):
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

    def iter(self):
        with session_scope() as session:
            # 获取模型的所有列
            columns = inspect(self.__class__).columns
            # 构建查询条件
            filters = {column.name: getattr(self, column.name) for column in columns if
                       getattr(self, column.name) is not None}
            # 执行查询
            results = session.query(self.__class__).filter_by(**filters).all()
            for result in results:
                yield result

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

    def set(self, **kwargs):
        columns = inspect(self.__class__).columns
        for column in columns:
            if column.name in kwargs.keys():
                setattr(self, column.name, kwargs[column.name])
        self.save()

    @classmethod
    def query(cls, **kwargs):
        instance = cls(**kwargs)
        instance.load()
        return instance

    @classmethod
    def query_all(cls, **kwargs):
        instance = cls(**kwargs)
        for ins in instance.iter():
            yield ins


def connect_db():
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    class User(TableModel):
        name = Column(String)

    connect_db()

    user = User()
    user.set(name='a')
    print(f'save {user.id}, name = {user.name}')

    user.set(name='b')
    print(f'update {user.id}, name = {user.name}')

    for query_user in User.query_all():
        print(f'query {query_user.id}, name = {query_user.name}')

    get_user = User.query(name='b')

    print(f'get {get_user.id}, name = {get_user.name}')

    get_user.set(name='c')

    print(f'update {get_user.id}, name = {get_user.name}')

    for query_user in User.query_all():
        print(f'query {query_user.id}, name = {query_user.name}')

    get_user.delete()

    for query_user in User.query_all():
        print(f'after delete {query_user.id}, name = {query_user.name}')
    else:
        print(f"delete all")
