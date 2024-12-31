from data.database import TableModel
from sqlalchemy import Column, String, Text


class StoreEntity(TableModel):
    store_id = Column(String)
    category_id = Column(String)


class DocumentEntity(TableModel):
    category_id = Column(String)
    doc_name = Column(String)
    doc_id = Column(String)
    local_path = Column(String)
