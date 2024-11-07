from sqlalchemy import create_engine, Column, Integer, String, select, and_, update, delete
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr, DeclarativeMeta

# 创建一个基类，用于定义表结构
Base = declarative_base()


def values(**kwargs):
    return kwargs


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

    def commit(self):
        self.session.commit()

    def create_tables(self, *models):
        for model in models:
            model.__table__.create(bind=self.engine, checkfirst=True)

    def add_record(self, model, **kwargs):
        new_record = model(**kwargs)
        self.session.add(new_record)
        self.session.commit()

    def get_records(self, model, **kwargs):
        query = select(model)
        conditions = []

        for key, value in kwargs.items():
            field = getattr(model, key)
            conditions.append(field == value)

        query = query.where(and_(*conditions))
        return self.session.execute(query).scalars().all()

    def get_all_records(self, model):
        return self.session.execute(select(model)).scalars().all()

    def update_records(self, model, values=None, **kwargs):
        if values:
            query = update(model)
            conditions = []

            for key, value in kwargs.items():
                field = getattr(model, key)
                conditions.append(field == value)

            query = query.where(and_(*conditions))
            query = query.values(**values)
            self.session.execute(query)
            self.session.commit()

    def delete_records(self, model, **kwargs):
        query = delete(model)
        conditions = []

        for key, value in kwargs.items():
            field = getattr(model, key)
            conditions.append(field == value)

        query = query.where(and_(*conditions))
        self.session.execute(query)
        self.session.commit()

    def delete_all_records(self, model):
        query = select(model)
        records = self.session.execute(query).scalars().all()
        for record in records:
            self.session.delete(record)
        self.session.commit()


# 定义全局变量 db_url
db_url = 'sqlite:///res/example.db'

# 定义全局变量 db
db = Database(db_url)


# 定义一个元类，用于在子类定义时自动创建表
class AutoCreateTableMeta(DeclarativeMeta):
    def __init__(cls, name, bases, dict_):
        super(AutoCreateTableMeta, cls).__init__(name, bases, dict_)
        if name != 'TableModel':
            db.create_tables(cls)


# 定义一个通用的数据表类
class TableModel(Base, metaclass=AutoCreateTableMeta):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)


# 使用示例
if __name__ == "__main__":
    # 定义一个新的数据类
    class User(TableModel):
        name = Column(String)
        age = Column(Integer)

    # 定义另一个新的数据类
    class Product(TableModel):
        name = Column(String)
        price = Column(Integer)

    with db:
        print("删除所有用户和产品记录")
        db.delete_all_records(User)
        db.delete_all_records(Product)

        # 添加用户
        db.add_record(User, name="Alice", age=30)
        db.add_record(User, name="Bob", age=25)

        # 添加产品
        db.add_record(Product, name="Laptop", price=1000)
        db.add_record(Product, name="Phone", price=500)

        print("打印所有用户和产品:")
        # 查询所有用户
        users = db.get_all_records(User)
        for user in users:
            print(f"User ID: {user.id}, Name: {user.name}, Age: {user.age}")

            if user.name == "Alice":
                # 更新Alice的年龄为15岁
                print("更新Alice的年龄为15岁")
                user.age = 15
                db.commit()

        # 查询所有产品
        products = db.get_all_records(Product)
        for product in products:
            print(f"Product ID: {product.id}, Name: {product.name}, Price: {product.price}")

        # 更新价格等于500的产品名称为Apple
        print("更新价格等于500的产品名称为Apple")
        db.update_records(Product, price=500, values=values(name="Apple"))

        # 删除产品Laptop
        print("删除产品Laptop")
        db.delete_records(Product, name="Laptop")

        print("再次打印所有用户和产品:")
        # 再次查询所有用户
        users = db.get_all_records(User)
        for user in users:
            print(f"User ID: {user.id}, Name: {user.name}, Age: {user.age}")

        # 再次查询所有产品
        products = db.get_all_records(Product)
        for product in products:
            print(f"Product ID: {product.id}, Name: {product.name}, Price: {product.price}")
