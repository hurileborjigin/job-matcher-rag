# test_cv_parser.py
import logging
logging.basicConfig(level=logging.INFO)

from src.cv.cv_parser import get_cv_parser

parser = get_cv_parser()

print("\n" + "="*60)
print("CV Parser Installation Test")
print("="*60)

print(f"\n✅ Supported formats: {list(parser.supported_formats.keys())}")

# Test text parsing
test_text = b"John Doe\nSoftware Engineer\n\nSkills: Python, React, AWS"
try:
    result = parser.parse_cv(test_text, "test.txt")
    print(f"\n✅ TXT parsing works! Extracted {len(result)} chars")
except Exception as e:
    print(f"\n❌ TXT parsing failed: {e}")

# Check PDF support
try:
    from pypdf import PdfReader
    print("\n✅ PDF support is available (pypdf installed)")
except ImportError:
    try:
        from PyPDF2 import PdfReader
        print("\n✅ PDF support is available (PyPDF2 installed)")
    except ImportError:
        print("\n❌ PDF support NOT available - run: pip install pypdf")

# Check DOCX support
try:
    from docx import Document
    print("✅ DOCX support is available")
except ImportError:
    print("❌ DOCX support NOT available - run: pip install python-docx")

print("\n" + "="*60)
print("Test complete!")
print("="*60 + "\n")