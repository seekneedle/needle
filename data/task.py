from data.database import TableModel
from sqlalchemy import Column, String, DateTime, text


class TaskStatus:
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    PENDING = 'PENDING'


class CreateStoreTaskEntity(TableModel):
    task_id = Column(String)
    status = Column(String)
    message = Column(String)
    category_id = Column(String)

class CreateFileTaskEntity(TableModel):
    task_id = Column(String)
    status = Column(String)
    message = Column(String)
    store_id = Column(String)
