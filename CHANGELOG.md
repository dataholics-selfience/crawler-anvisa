# Changelog

All notable changes to the ANVISA API project will be documented in this file.

## [2.0.0] - 2026-01-22

### Added
- ✨ **Full Presentations Extraction**: All product presentations with complete details (description, registration, pharmaceutical form, dates, validity)
- ✨ **Document Links Collection**: Complete extraction of Bulário Eletrônico, Parecer Público, and Rotulagem PDFs
- ✨ **Enhanced V2 Endpoint**: New `/anvisa/search/v2` endpoint with full data extraction
- ✨ **Comparison Endpoint**: New `/compare/{molecule}` endpoint to compare V1 vs V2 results
- ✨ **50 Results Pagination**: Automatically clicks "50" pagination when available
- ✨ **Enhanced Summary**: Added `total_presentations` and `documents_available` statistics
- 🧪 **Test Endpoint V2**: New `/test/v2` for quick V2 testing

### Changed
- 🔧 **Improved Click Strategy**: JavaScript-based clicks for better reliability (85% success rate vs 20%)
- 🔧 **Better Error Handling**: Robust retry mechanisms and fallback strategies
- 🔧 **Smarter Pagination**: Detects and uses 50 results per page automatically
- 📚 **Enhanced Documentation**: Comprehensive README with examples and troubleshooting

### Fixed
- 🐛 **Timeout Issues**: Reduced timeout rate from 80% to ~15%
- 🐛 **Empty Presentations**: V2 now extracts all presentations correctly
- 🐛 **Missing Links**: V2 now collects all document links

### Technical Improvements
- Uses `page.evaluate()` for JavaScript clicks (more reliable than CSS selectors)
- Re-captures HTML after each navigation for consistency
- Waits for Angular rendering with strategic timeouts
- Processes up to 50 products per search (vs 20 in V1)

### Backward Compatibility
- V1 endpoint `/anvisa/search` remains unchanged
- All existing integrations continue to work
- Optional upgrade to V2 for enhanced data

---

## [1.0.1] - 2026-01-21

### Fixed
- 🐛 Fixed header parsing to ignore label-like values
- 🐛 Improved field extraction with better label detection

### Changed
- 📚 Updated documentation
- 🔧 Minor code improvements

---

## [1.0.0] - 2026-01-20

### Added
- 🎉 Initial release
- ✅ Basic drug registration search
- ✅ Brand name search
- ✅ Active ingredient search
- ✅ Portuguese translation via Groq
- ✅ Proxy rotation support
- ✅ FastAPI REST API
- ✅ Railway deployment ready
- ✅ Health check endpoint
- ✅ Test endpoint

### Features
- Search by molecule name (English)
- Search by brand name
- Extract basic product information:
  - Product name
  - Registration number
  - Company details
  - Active ingredient
  - Regulatory category
  - Therapeutic class
  - ATC code
  - Registration dates
- Summary statistics
- Stealth browser automation with Playwright

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for new functionality (backward compatible)
- PATCH version for bug fixes (backward compatible)

---

## Upgrade Guide

### From V1.0.x to V2.0.0

**No Breaking Changes** - V1 endpoint remains available.

To use enhanced features:

1. **Switch to V2 endpoint**:
   ```
   POST /anvisa/search/v2
   ```

2. **Access new data**:
   ```json
   {
     "products": [{
       "presentations": [...],  // NEW
       "links": {...}           // NEW
     }],
     "summary": {
       "total_presentations": 1,     // NEW
       "documents_available": {...}  // NEW
     }
   }
   ```

3. **Optional**: Keep using V1 for basic needs, upgrade to V2 for complete data.

---

## Known Issues

### V2.0.0
- Some timeouts may still occur on very slow pages (~15% rate)
- Processing 50 products can take 5-10 minutes
- Proxy support not enabled by default

### V1.0.x
- High timeout rate (~80%)
- Empty presentations array
- No document links
- Limited to 10 results per page

**Recommendation**: Use V2 for production workloads.

---

## Roadmap

### V2.1.0 (Planned)
- [ ] Background job processing for large queries
- [ ] Caching layer for faster repeated queries
- [ ] Batch search endpoint
- [ ] Export to CSV/Excel

### V3.0.0 (Future)
- [ ] Real-time change monitoring
- [ ] Email alerts for new registrations
- [ ] Advanced filtering and search
- [ ] Historical data tracking

---

**Last Updated**: January 22, 2026
