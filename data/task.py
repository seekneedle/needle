
from data.database import TableModel
from sqlalchemy import Column, String, DateTime, func


class TaskStatus:
    RUNNING = 'RUNNING'
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'


class TaskEntry(TableModel):
    task_id = Column(String)
    status = Column(String)
    create_time = Column(DateTime, server_default=func.now)
    modify_time = Column(DateTime, server_default=func.now)

    def set_status(self, status):
        self.status = status
        self.modify_time = func.now()
        self.save()
