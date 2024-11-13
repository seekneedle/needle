from data.database import TableModel
from sqlalchemy import Column, String, Text


class CreateStoreDocumentEntity(TableModel):
    task_id = Column(String)
    doc_name = Column(String)
    doc_id = Column(String)
    status = Column(String)


class CreateStoreEntity(TableModel):
    task_id = Column(String)
    index_id = Column(String)
    message = Column(Text)
