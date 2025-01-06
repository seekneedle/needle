from pydantic import BaseModel
from data.task import FileTaskEntity
from utils.files_utils import read_file


class FileContentResponse(BaseModel):
    content: str = None


def get_file(file_id):
    tasks = FileTaskEntity.query_all(doc_id=file_id)
    for task in tasks:
        if task.local_path is not None and task.local_path != '':
            content = read_file(task.local_path)
            return FileContentResponse(content=content)
    return FileContentResponse()
