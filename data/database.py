from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr

# 创建一个基类，用于定义表结构
Base = declarative_base()


# 定义一个通用的数据表类
class BaseModel(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)


# 封装数据库连接类
class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def __enter__(self):
        self.session = self.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def create_tables(self, *models):
        for model in models:
            model.__table__.create(bind=self.engine, checkfirst=True)

    def add_record(self, model, **kwargs):
        new_record = model(**kwargs)
        self.session.add(new_record)
        self.session.commit()

    def get_record(self, model, record_id):
        return self.session.get(model, record_id)

    def get_all_records(self, model):
        return self.session.execute(select(model)).scalars().all()

    def update_record(self, model, record_id, **kwargs):
        record = self.session.get(model, record_id)
        if record:
            for key, value in kwargs.items():
                setattr(record, key, value)
            self.session.commit()

    def delete_record(self, model, record_id):
        record = self.session.get(model, record_id)
        if record:
            self.session.delete(record)
            self.session.commit()


# 定义全局变量 db_url
db_url = 'sqlite:///res/example.db'

# 定义全局变量 db
db = Database(db_url)

# 使用示例
if __name__ == "__main__":
    # 定义一个新的数据类
    class User(BaseModel):
        name = Column(String)
        age = Column(Integer)

    # 定义另一个新的数据类
    class Product(BaseModel):
        name = Column(String)
        price = Column(Integer)


    with db:
        db.create_tables(User, Product)  # 创建表结构

        # 添加用户
        db.add_record(User, name="Alice", age=30)
        db.add_record(User, name="Bob", age=25)

        # 添加产品
        db.add_record(Product, name="Laptop", price=1000)
        db.add_record(Product, name="Phone", price=500)

        # 查询所有用户
        users = db.get_all_records(User)
        for user in users:
            print(f"User ID: {user.id}, Name: {user.name}, Age: {user.age}")

        # 查询所有产品
        products = db.get_all_records(Product)
        for product in products:
            print(f"Product ID: {product.id}, Name: {product.name}, Price: {product.price}")

        # 更新用户信息
        db.update_record(User, 1, name="Alice Smith", age=31)

        # 删除产品
        db.delete_record(Product, 2)

        # 再次查询所有用户
        users = db.get_all_records(User)
        for user in users:
            print(f"User ID: {user.id}, Name: {user.name}, Age: {user.age}")

        # 再次查询所有产品
        products = db.get_all_records(Product)
        for product in products:
            print(f"Product ID: {product.id}, Name: {product.name}, Price: {product.price}")
