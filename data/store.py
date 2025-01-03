from data.database import TableModel
from sqlalchemy import Column, String, Text


class StoreEntity(TableModel):
    index_id = Column(String, unique=True)
    category_id = Column(String)


class FileEntity(TableModel):
    store_id = Column(String)
    doc_name = Column(String)
    doc_id = Column(String)
    local_path = Column(String)
