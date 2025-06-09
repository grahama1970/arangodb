# Q&A Generation Flow with Complete Corpus Validation

## Overview

This document explains how the Q&A generation system ensures that all answers are validated against the complete PDF corpus, with validation happening at the Marker stage rather than re-extracting during Q&A generation.

## Architecture

```
PDF → Marker (with validation) → Complete Corpus → ArangoDB → Q&A Generation
```

## Key Components

### 1. Marker Q&A-Optimized Processing

**Files:**
- `/marker/processors/corpus_validator.py` - Validates content against raw PDF
- `/marker/processors/enhanced_table_validator.py` - Ensures all tables are captured
- `/marker/config/qa_optimized.py` - Configuration for accuracy-first processing
- `/marker/scripts/convert_for_qa.py` - CLI tool for Q&A-optimized conversion

**Process:**
```bash
# Convert with full validation
marker-qa convert document.pdf --output-dir ./validated/
```

**Output includes:**
```json
{
  "document": {...},              // Structured content
  "metadata": {...},              // Processing metadata
  "validation": {                 // Validation results
    "corpus_validation": {...},
    "table_validation": {...}
  },
  "raw_corpus": {                 // Complete PDF text
    "full_text": "...",          // All text from PyMuPDF
    "pages": [...],              // Page-by-page text
    "tables": [...]              // Extracted tables
  }
}
```

### 2. ArangoDB Q&A Generation

**Files:**
- `/src/arangodb/qa_generation/generator_marker_aware.py` - Uses Marker corpus
- `/src/arangodb/qa_generation/cli.py` - CLI with Marker awareness

**Process:**
```bash
# Generate Q&A using validated corpus
qa-generate from-marker ./validated/document.json --threshold 0.97
```

**Key Features:**
- Detects Q&A-optimized Marker output
- Uses `raw_corpus` for validation
- Falls back to document content if needed
- Reports validation statistics

## Corpus Validation Flow

### Stage 1: Marker Processing

1. **PyMuPDF Extraction:**
   ```python
   # In corpus_validator.py
   doc = fitz.open(pdf_path)
   full_text = ""
   for page in doc:
       text = page.get_text()
       full_text += text
   ```

2. **Table Validation:**
   ```python
   # In enhanced_table_validator.py
   # Compare Marker tables with PyMuPDF
   # Use Camelot for low-confidence tables
   ```

3. **Corpus Packaging:**
   ```python
   output_data = {
       "document": result.document,
       "raw_corpus": {
           "full_text": full_text,
           "pages": page_texts,
           "tables": table_texts
       }
   }
   ```

### Stage 2: Q&A Generation

1. **Corpus Detection:**
   ```python
   # In generator_marker_aware.py
   raw_corpus = marker_output.get("raw_corpus")
   if not raw_corpus:
       logger.warning("No raw corpus found")
   ```

2. **Answer Validation:**
   ```python
   async def _validate_with_marker_corpus(self, qa_pairs, raw_corpus):
       for qa_pair in qa_pairs:
           segments = self._extract_answer_segments(qa_pair.answer)
           for segment in segments:
               score = fuzz.partial_ratio(segment, raw_corpus["full_text"])
               # Also check pages and tables
   ```

3. **Confidence Scoring:**
   ```python
   qa_pair.validation_score = best_score / 100
   qa_pair.citation_found = best_score >= threshold
   ```

## Table Handling

### Marker Captures Tables Using:
1. **Primary extraction** - Marker's table detection
2. **PyMuPDF validation** - Detect missed tables  
3. **Camelot fallback** - For low-confidence tables
4. **Raw corpus inclusion** - All table text included

### Q&A Validates Against:
1. Structured table data from Marker
2. Raw table text in corpus
3. Page-level text containing tables

## Benefits

1. **Single Extraction Point**
   - PDF processed once by Marker
   - No re-extraction during Q&A generation
   - Consistent corpus across pipeline

2. **Complete Validation**
   - All text validated by PyMuPDF
   - Tables validated by multiple methods
   - Raw corpus preserved for checking

3. **Accuracy First**
   - Q&A-optimized configuration prioritizes accuracy
   - Multiple validation layers
   - High confidence thresholds

## Usage Example

```bash
# Step 1: Convert PDF with Q&A optimization
marker-qa convert research_paper.pdf --output-dir ./qa_ready/

# Step 2: Generate Q&A with corpus validation
qa-generate from-marker ./qa_ready/research_paper.json \
  --max-questions 50 \
  --threshold 0.97

# Step 3: Validate results
qa-generate validate ./qa_output/research_paper_qa.json
```

## Technical Decisions

1. **Why validate in Marker?**
   - Single source of truth
   - Earlier detection of issues
   - More efficient processing

2. **Why include raw corpus?**
   - Ensures nothing is missed
   - Provides fallback validation
   - Supports table verification

3. **Why use multiple methods?**
   - Different tools excel at different tasks
   - Redundancy improves accuracy
   - Critical for Q&A quality