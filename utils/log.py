from data.database import TableModel
from sqlalchemy import Column, Integer, String
import logging
import os
from datetime import datetime
from utils.config import config


# 定义日志模型
class LogEntry(TableModel):
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String)
    message = Column(String)
    timestamp = Column(String)


# 自定义日志处理器
class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = LogEntry(
            level=record.levelname,
            message=self.format(record),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        log_entry.save()


# 配置日志记录
def get_log():
    path = os.path.join(os.path.dirname(__file__), '..', 'output')
    if not os.path.exists(path):
        os.mkdir(path)

    level = logging.INFO if config['log_level'] == 'info' else logging.DEBUG
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=os.path.join(os.path.dirname(__file__), '..', 'output', 'server.log')
    )

    # 添加自定义的日志处理器
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(level)
    db_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(db_handler)

    return logging.getLogger()


log = get_log()


if __name__ == '__main__':
    log.info('test')
    logs = LogEntry()
    for _log in logs.iter():
        id = _log.id
        level = _log.level
        message = _log.message
        timestamp = _log.timestamp
        print(f'id: {id}, level: {level}, message: {message}, timestamp: {timestamp}')
