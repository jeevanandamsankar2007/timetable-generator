import sys
import os
import pprint
sys.path.insert(0, os.path.abspath('d:/Timetable Table 2/backend'))

from app.pdf_engine.reader import PDFReader
from app.pdf_engine.table_detector import TableDetector
from app.pdf_engine.grid_extractor import GridExtractor
from app.pdf_engine.subject_master_extractor import SubjectMasterExtractor
from app.mapping_engine.mapper import TimetableMapper

file_path = "d:/Timetable Table 2/backend/uploads/pdf/2_Class TT II YEAR.pdf"
print(f"Testing {file_path}")

reader = PDFReader(file_path)
pdf_data = reader.read()

if not pdf_data.get("tables"):
    print("No tables found in PDF")
    sys.exit(1)

print(f"Detected {len(pdf_data['tables'])} tables from Camelot.")

classified = TableDetector.classify_tables(pdf_data["tables"])
print(f"Found {len(classified['timetable_grids'])} timetable grids and {len(classified['subject_master_tables'])} subject master tables")

subject_master = []
master_extractor = SubjectMasterExtractor()
for sm_table in classified["subject_master_tables"]:
    extracted, debug_log = master_extractor.extract(sm_table["data"])
    subject_master.extend(extracted)

print(f"Extracted {len(subject_master)} subjects from Subject Master tables.")
for sm in subject_master[:3]:
    print(sm)

mapper = TimetableMapper(subject_master)
all_mapped_cells = []

for grid in classified["timetable_grids"]:
    structure = TableDetector.detect_structure(grid["data"])
    extractor = GridExtractor(grid["data"], structure)
    cells = extractor.extract_cells()
    mapped = mapper.map_cells(cells)
    all_mapped_cells.extend(mapped)

print(f"Total mapped cells: {len(all_mapped_cells)}")
if all_mapped_cells:
    print("First 3 mapped cells:")
    pprint.pprint(all_mapped_cells[:3])
