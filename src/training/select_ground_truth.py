"""
Master’s Thesis – Ground Truth Selection

This script selects random pages from PDF files exported
from Transkribus in order to create ground truth data
for HTR training.

The data itself is stored outside the GitHub repository
for licensing and size reasons.

Author: Sophie Hamann (ChatGPT-assisted)
"""

import random
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter


# --------------------------------------------------
# Configuration
# --------------------------------------------------

# Path to the external Transkribus data directory
TRANSKRIBUS_DATA_DIR = Path(
    "/Users/sophiehamann/Documents/MA_Universität_Wien/2025WiSe_MA/digitization/transkribus_data"
)

INPUT_DIR = TRANSKRIBUS_DATA_DIR / "heresies_pdf_files"
OUTPUT_DIR = TRANSKRIBUS_DATA_DIR / "baseline_model_training_data"
OUTPUT_FILE = OUTPUT_DIR / "heresies_ground_truth.pdf"

PAGES_PER_PDF = 1
RANDOM_SEED = 42  # ensures reproducibility


# --------------------------------------------------
# Setup
# --------------------------------------------------

random.seed(RANDOM_SEED)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pdf_files = sorted(INPUT_DIR.glob("heresies*.pdf"))

if not pdf_files:
    raise FileNotFoundError(f"No matching PDFs found in {INPUT_DIR}")


# --------------------------------------------------
# Processing
# --------------------------------------------------

output_pdf = PdfWriter()

for pdf_path in pdf_files:
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)

    pages_to_select = min(PAGES_PER_PDF, num_pages)
    selected_pages = sorted(
        random.sample(range(num_pages), pages_to_select)
    )

    for page_num in selected_pages:
        output_pdf.add_page(reader.pages[page_num])


# --------------------------------------------------
# Save output
# --------------------------------------------------

with open(OUTPUT_FILE, "wb") as f:
    output_pdf.write(f)

print(f"Ground truth PDF written to: {OUTPUT_FILE}")