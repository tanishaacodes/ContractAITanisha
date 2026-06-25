import sys
from langchain_core.documents import Document

class docstore:
    document = type("document", (), {"Document": Document})

sys.modules["langchain.docstore"] = type("module", (), {"document": docstore.document})()
sys.modules["langchain.docstore.document"] = docstore.document
