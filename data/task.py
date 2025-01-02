from data.database import TableModel
from sqlalchemy import Column, String, DateTime, text


class TaskStatus:
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class TaskEntity(TableModel):
    __abstract__ = True

    task_id = Column(String)
    status = Column(String)
    message = Column(String)


class StoreTaskEntity(TaskEntity):
    store_id = Column(String)
    job_id = Column(String)


class FileTaskEntity(TaskEntity):
    file_id = Column(String)
