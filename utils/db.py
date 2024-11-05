from sqlalchemy import create_engine

# 创建一个 SQLite 数据库引擎，数据库文件名为 'example.db'
engine = create_engine('sqlite:///example.db', echo=True)