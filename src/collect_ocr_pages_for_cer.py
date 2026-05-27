"""
Collect source OCR page XMLs that correspond to the ground truth pages
in the combined ground truth document, for CER calculation.

Ground truth pages come from:
- Pages named "0128_heresies1_page-0001.xml" etc.: directly maps to
  heresies_01_pagexml/page_1.xml, heresies_26_pagexml/page_2.xml, etc.
- Pages named "0001_p002.xml" etc.: matched by text content search across
  all source heresies_XX_pagexml directories.
"""

import re
import shutil
from pathlib import Path
from lxml import etree

NAMESPACE = {"pc": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"}

GT_PAGE_DIR = Path(
    "/Users/sophiehamann/master-thesis-code/data/processed/training_data/ground_truth/page"
)
RAW_DIR = Path("/Users/sophiehamann/master-thesis-code/data/raw")
OUTPUT_DIR = Path(
    "/Users/sophiehamann/master-thesis-code/data/processed/training_data/ocr_pages_for_cer"
)


def extract_text_lines(xml_path: Path) -> list[str]:
    """Extract all non-empty TextLine Unicode texts from a PAGE XML file."""
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        lines = []
        for tl in root.findall(".//pc:TextLine", NAMESPACE):
            u = tl.find("pc:TextEquiv/pc:Unicode", NAMESPACE)
            if u is not None and u.text and u.text.strip():
                lines.append(u.text.strip())
        return lines
    except Exception as e:
        print(f"  WARNING: could not parse {xml_path}: {e}")
        return []


def build_source_index(raw_dir: Path) -> dict[str, tuple[Path, list[str]]]:
    """
    Build an index: {source_file_stem: (path, text_lines)} for all source XMLs.
    Also build a quick lookup by text fingerprint.
    Returns: dict mapping file stem to (path, lines).
    """
    index = {}
    pagexml_dirs = sorted(raw_dir.glob("heresies_*_pagexml"))
    print(f"Indexing {len(pagexml_dirs)} source directories...")
    for d in pagexml_dirs:
        for xml_file in sorted(d.glob("page_*.xml")):
            lines = extract_text_lines(xml_file)
            index[xml_file.stem + "|" + d.name] = (xml_file, lines)
    print(f"Indexed {len(index)} source page XMLs.")
    return index


def extract_words(lines: list[str]) -> set[str]:
    """Extract a set of meaningful words (>4 chars) from text lines."""
    words = set()
    for line in lines:
        for word in line.split():
            word = word.strip(".,;:!?\"'()[]{}¬-")
            if len(word) > 4:
                words.add(word.lower())
    return words


def find_matching_source(
    gt_lines: list[str],
    source_index: dict[str, tuple[Path, list[str]]],
) -> tuple[Path | None, int]:
    """
    Find the source XML that best matches the ground truth text lines.

    Uses a two-pass strategy:
    1. Exact line matching: count how many complete GT lines appear verbatim in source.
    2. Word overlap: fraction of GT words found in source (used as tiebreaker).
    Returns (matching_path, match_score) where score is exact-line matches (×10) +
    word-overlap percentage.
    """
    if not gt_lines:
        return None, 0

    # Build candidate sets: medium-length lines most likely to match exactly
    medium_lines = [l for l in gt_lines if 8 < len(l) < 120]
    gt_words = extract_words(gt_lines)

    best_path = None
    best_score = 0.0

    for key, (src_path, src_lines) in source_index.items():
        src_text = " ".join(src_lines)
        src_words = extract_words(src_lines)

        # Exact line hits (each hit worth 10 points)
        exact_hits = sum(1 for line in medium_lines if line in src_text)

        # Word overlap (0–100 points based on fraction of GT words in source)
        if gt_words:
            overlap = len(gt_words & src_words) / len(gt_words) * 100
        else:
            overlap = 0.0

        score = exact_hits * 10 + overlap

        if score > best_score:
            best_score = score
            best_path = src_path

    return best_path, best_score


# Hardcoded fallbacks for pages with almost no text (image-only pages where
# text matching fails). Identified manually by page number + surrounding context.
MANUAL_FALLBACKS: dict[str, tuple[str, int]] = {
    "0026_p027.xml": ("heresies_14_pagexml", 10),  # printed page 9, image-only
    "0027_p028.xml": ("heresies_14_pagexml", 18),  # printed page 22, image-only
    "0056_p057.xml": ("heresies_02_pagexml", 67),  # printed pages 25/26/69, image spread
}


def parse_explicit_filename(filename: str) -> tuple[str, int] | None:
    """
    Parse filenames like '0128_heresies1_page-0001.xml'.
    Returns (issue_dir_name, page_number) or None.
    """
    m = re.match(r"\d+_heresies(\d+)_page-(\d+)\.xml", filename)
    if m:
        issue_num = int(m.group(1))
        page_num = int(m.group(2))
        issue_dir = f"heresies_{issue_num:02d}_pagexml"
        return issue_dir, page_num
    return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gt_pages = sorted(GT_PAGE_DIR.glob("*.xml"))
    print(f"Found {len(gt_pages)} ground truth pages.\n")

    # Build source index for text-based matching
    source_index = build_source_index(RAW_DIR)
    print()

    matched = []
    unmatched = []

    for gt_page in gt_pages:
        filename = gt_page.name

        # --- Strategy 0: manual fallback for image-only pages ---
        if filename in MANUAL_FALLBACKS:
            issue_dir, page_num = MANUAL_FALLBACKS[filename]
            src_path = RAW_DIR / issue_dir / f"page_{page_num}.xml"
            if src_path.exists():
                dest_name = f"{gt_page.stem}__{issue_dir}__page_{page_num}.xml"
                shutil.copy2(src_path, OUTPUT_DIR / dest_name)
                matched.append((filename, src_path))
                print(f"[MANUAL]   {filename} → {issue_dir}/page_{page_num}.xml")
            else:
                print(f"[MISSING]  {filename} → {src_path} (not found)")
                unmatched.append(filename)
            continue

        # --- Strategy 1: explicit issue+page in filename ---
        parsed = parse_explicit_filename(filename)
        if parsed:
            issue_dir, page_num = parsed
            src_path = RAW_DIR / issue_dir / f"page_{page_num}.xml"
            if src_path.exists():
                dest_name = f"{gt_page.stem}__{issue_dir}__page_{page_num}.xml"
                shutil.copy2(src_path, OUTPUT_DIR / dest_name)
                matched.append((filename, src_path))
                print(f"[EXPLICIT] {filename} → {issue_dir}/page_{page_num}.xml")
            else:
                print(f"[MISSING]  {filename} → {src_path} (not found)")
                unmatched.append(filename)
            continue

        # --- Strategy 2: text-based matching ---
        gt_lines = extract_text_lines(gt_page)
        if not gt_lines:
            print(f"[EMPTY]    {filename} — no text, skipping")
            unmatched.append(filename)
            continue

        src_path, score = find_matching_source(gt_lines, source_index)
        if src_path and score >= 20:
            issue_dir = src_path.parent.name
            page_stem = src_path.stem
            dest_name = f"{gt_page.stem}__{issue_dir}__{page_stem}.xml"
            shutil.copy2(src_path, OUTPUT_DIR / dest_name)
            matched.append((filename, src_path))
            label = "MATCHED" if score >= 50 else "WEAK   "
            print(f"[{label}]  {filename} → {issue_dir}/{page_stem}.xml  (score={score:.1f})")
        else:
            print(f"[NO MATCH] {filename} — best score={score:.1f}, no confident source found")
            unmatched.append(filename)

    print(f"\n{'='*60}")
    print(f"Matched:   {len(matched)} / {len(gt_pages)}")
    print(f"Unmatched: {len(unmatched)} / {len(gt_pages)}")
    print(f"Output:    {OUTPUT_DIR}")

    if unmatched:
        print("\nUnmatched ground truth pages:")
        for f in unmatched:
            print(f"  {f}")


if __name__ == "__main__":
    main()
