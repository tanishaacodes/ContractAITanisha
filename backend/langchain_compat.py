"""
Compatibility shim for old langchain imports.
This fixes the issue where PaddleX expects old langchain module structure.
"""
import sys
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Create fake modules to satisfy old import paths
class FakeDocstoreDocument:
    Document = Document

class FakeDocstore:
    document = FakeDocstoreDocument()

class FakeTextSplitter:
    RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter

# Inject into sys.modules to redirect old imports to new locations
sys.modules['langchain.docstore'] = FakeDocstore()
sys.modules['langchain.docstore.document'] = FakeDocstoreDocument()
sys.modules['langchain.text_splitter'] = FakeTextSplitter()
