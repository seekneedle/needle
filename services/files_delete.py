from pydantic import BaseModel
from utils.bailian import delete_store_files, delete_file
import traceback
from utils.log import log
import time


class DeleteFilesRequest(BaseModel):
    id: str
    file_ids: list[str]


class DeleteFilesResponse(BaseModel):
    file_ids: list[str]


def delete_files(request: DeleteFilesRequest):
    deleted_ids = delete_store_files(request.id, request.file_ids)
    for i, file_id in enumerate(deleted_ids):
        try:
            delete_file(file_id)
            if (i + 1) % 10 == 0:
                time.sleep(1)
        except Exception as e:
            trace_info = traceback.format_exc()
            log.error(f'Exception for files_delete, file id:{file_id} , e: {e}, trace: {trace_info}')
    return DeleteFilesResponse(file_ids=deleted_ids)
