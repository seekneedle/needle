
from data.database import TableModel
from sqlalchemy import Column, String, DateTime, text


class TaskStatus:
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    PENDING = 'PENDING'


class TaskEntry(TableModel):
    task_id = Column(String)
    status = Column(String)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    modify_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    def set_status(self, status):
        self.status = status
        self.save()
