
from data.database import TableModel
from sqlalchemy import Column, String, DateTime, func


class TaskStatus:
    RUNNING = 'RUNNING'
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'


class TaskEntry(TableModel):
    task_id = Column(String)
    status = Column(String)
    create_time = Column(DateTime, server_default=func.now())
    modify_time = Column(DateTime, server_default=func.now())

    def set_status(self, status):
        self.status = status
        self.modify_time = func.now()
        self.save()
    @classmethod
    def get_task_info(cls, task_id):
        """
        Retrieve task information based on task_id.
        Returns a TaskEntry object or None if not found.
        """
        return cls.query_by_column_value('task_id', task_id)


