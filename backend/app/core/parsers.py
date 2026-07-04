from app.parsers.document_parser import parse_document as _parse_document
import os


def parse_document(file_path: str):
    """
    Core wrapper around enterprise document parser.
    Keeps backward compatibility with existing services.
    """
    return _parse_document(file_path)