# Master's Thesis – Tracing Feminist Currents

**Conceptual Shifts in Heresies Magazine (1977–1993)**  
University of Vienna, 2026

This repository contains the code used to process and analyse the corpus of *Heresies: A Feminist Publication on Art and Politics* for my master's thesis.

## Data

Source: Transkribus  
Raw data is not included in this repository due to licensing restrictions.

## Repository Structure

```
notebooks/
  01_transkribus_export.ipynb     # Export and retrieve data from Transkribus
  02_xml_parsing_new.ipynb        # Parse PAGE-XML exports
  03_ocr_validation_new.ipynb     # Validate OCR quality
  04_corpus_split.ipynb           # Split corpus into subcorpora
  05_remove_formatting.ipynb      # Remove formatting artefacts
  06_tokenization.ipynb           # Tokenization
  07_punctuation.ipynb            # Punctuation normalisation
  h1_analysis/                    # Hypothesis 1: n-gram and frequency analysis
  h2_analysis/                    # Hypothesis 2: named entity recognition
  h3_analysis/                    # Hypothesis 3: NER and conceptual term analysis
  AI_prompts/                     # Prompts used with AI assistants during development

src/
  collect_ocr_pages_for_cer.py    # Select pages for character error rate evaluation
  training/
    select_ground_truth.py        # Select ground truth pages for HTR training

latex_images/                     # Figures exported for the thesis document
```

## Workflow

1. Export transcriptions from Transkribus (`01`)
2. Parse PAGE-XML and extract text (`02`)
3. Validate OCR/HTR quality (`03`)
4. Split corpus into subcorpora (`04`)
5. Clean and normalise text (`05`–`07`)
6. Run hypothesis-specific analysis (`h1_analysis/`, `h2_analysis/`, `h3_analysis/`)

## Setup

```bash
pip install -r requirements.txt
```

Then run notebooks in order, starting from `01_transkribus_export.ipynb`.
