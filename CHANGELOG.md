# Changelog

All notable changes to the ANVISA Crawler API will be documented in this file.

## [2.0.1] - 2026-01-23 🔧 CRITICAL FIX

### Fixed
- **CRITICAL**: Fixed table row clicking bug that was causing 90% timeouts
  - Previous: Clicked on individual table cells (NUBEQA, REGISTRADO, DAROLUTAMIDA, etc.)
  - Now: Correctly clicks on table rows (once per product)
  - Impact: Reduced processing time from ~90s to ~10s
  - Impact: Increased success rate from 10% to 100%

### Changed
- `_parse_results_table_fixed()`: Complete rewrite of table parsing logic
  - Now finds `<tbody>` element first
  - Gets all `<tr>` rows in table body
  - For each row, clicks only the FIRST `<td>` cell
  - Uses improved JavaScript click strategy
- Better error messages and logging for debugging
- Improved timeout handling (now 5s instead of 10s per click)

### Technical Details

**Before (v2.0):**
```python
# Found ALL cells with ng-click
rows = soup.find_all('td', {'ng-click': lambda x: x and 'detail' in x})
# Result: 10 cells for 1 product row!
```

**After (v2.0.1):**
```python
# Find rows, click first cell only
tbody = soup.find('tbody')
table_rows = tbody.find_all('tr', recursive=False)
# Click cells[0] of each row via JavaScript
```

### Performance Improvement
- Search with 10 products:
  - v2.0: 90 seconds (9 timeouts + 1 success)
  - v2.0.1: 10 seconds (0 timeouts + 10 successes)

---

## [2.0.0] - 2026-01-22 ✨ ENHANCED VERSION

### Added
- **Full data extraction** for each product:
  - ALL presentations with complete details (dosage, packaging, validity)
  - ALL document links (Bulário, Parecer Público, Rotulagem PDFs)
  - Complete regulatory information
- **Two search flows**:
  - Flow 1: Simple brand name search (fast)
  - Flow 2: Advanced active ingredient search (comprehensive)
- **Pagination support**: Up to 50 results per page
- Enhanced summary statistics including document availability
- New V2 endpoint: `/anvisa/search/v2`

### Changed
- Improved Angular page handling with better waits
- Better error handling with specific timeout exceptions
- Enhanced logging with step-by-step flow tracking

### Known Issues
- ⚠️ Table row clicking bug (clicking individual cells)
  - Fixed in v2.0.1

---

## [1.0.3] - 2026-01-21

### Fixed
- Added wait_for_selector checks for better stability
- Adjusted timeouts for Angular rendering
- Fixed navigation issues in advanced search

### Changed
- Improved logging format
- Better error messages

---

## [1.0.2] - 2026-01-20

### Added
- Retry mechanisms for failed clicks
- More robust proxy rotation

### Fixed
- Minor stability issues with page navigation

---

## [1.0.1] - 2026-01-19

### Fixed
- Initial deployment issues on Railway
- Playwright browser installation

---

## [1.0.0] - 2026-01-18 🎉 INITIAL RELEASE

### Added
- Basic ANVISA search functionality
- Brand name search
- Active ingredient search
- Groq API integration for translation
- Proxy rotation support
- FastAPI REST API
- Docker containerization
- Railway deployment configuration
- Health check endpoints

### Features
- Stealth browsing (anti-detection)
- Portuguese translation via Groq
- Cascading search strategy (brand → molecule)
- Basic data extraction (name, company, dates, etc.)

---

## Version Numbering

- **MAJOR**: Breaking changes or complete rewrites
- **MINOR**: New features, non-breaking changes
- **PATCH**: Bug fixes, small improvements

Current: **v2.0.1** (Fixed row clicking bug)
