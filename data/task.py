from data.database import TableModel
from sqlalchemy import Column, String, DateTime, text


class TaskStatus:
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class TaskEntity(TableModel):
    __abstract__ = True

    task_id = Column(String(36))
    status = Column(String(10))
    message = Column(String(50))


class StoreTaskEntity(TaskEntity):
    index_id = Column(String(10))
    job_id = Column(String(36))


class FileTaskEntity(TaskEntity):
    doc_id = Column(String(50))
    doc_name = Column(String(128))
    local_path = Column(String(255))
