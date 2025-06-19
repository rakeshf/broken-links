# 🔍 Broken Link Checker [![CodeFactor](https://www.codefactor.io/repository/github/rakeshf/broken-links/badge/main)](https://www.codefactor.io/repository/github/rakeshf/broken-links/overview/main)

A powerful Python tool for scanning websites to identify broken links, dead URLs, and accessibility issues. Perfect for website maintenance, SEO audits, and quality assurance.

## ✨ Features

- **Comprehensive Link Scanning**: Crawls websites recursively to find all links
- **Multiple Export Formats**: Export results to JSON and CSV formats
- **Configurable Depth**: Control how deep the crawler goes into your site
- **Domain Filtering**: Option to scan only same-domain links or include external links
- **Rate Limiting**: Built-in delays to be respectful to target servers
- **Detailed Reporting**: Categorizes links as working, broken, or error states
- **Real-time Progress**: Live updates during scanning with emoji indicators
- **Flexible Configuration**: Customizable via command-line arguments

## 📋 Requirements

- Python 3.7+
- Required packages:
  - `requests` - HTTP library for making web requests
  - `beautifulsoup4` - HTML parsing library
  - `lxml` - XML and HTML parser (recommended for BeautifulSoup)

## 🚀 Installation

1. **Clone or download the script**:
   ```bash
   wget https://raw.githubusercontent.com/your-repo/broken_link_checker.py
   # or
   curl -O https://raw.githubusercontent.com/your-repo/broken_link_checker.py
   ```

2. **Install dependencies**:
   ```bash
   pip install requests beautifulsoup4 lxml
   ```

3. **Make it executable** (optional):
   ```bash
   chmod +x broken_link_checker.py
   ```

## 📖 Usage

### Basic Usage

```bash
python broken_link_checker.py <website_url>
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-urls <number>` | Maximum URLs to scan | 100 |
| `--max-depth <number>` | Maximum crawl depth | 2 |
| `--delay <seconds>` | Delay between requests (be respectful!) | 1.0 |
| `--external` | Include external links (default: same domain only) | False |
| `--json <filename>` | Save results to JSON file | None |
| `--csv <filename>` | Save results to CSV file | None |

### 📝 Examples

**Basic website scan:**
```bash
python broken_link_checker.py https://example.com
```

**Comprehensive scan with custom settings:**
```bash
python broken_link_checker.py https://example.com \
  --max-urls 500 \
  --max-depth 3 \
  --delay 2 \
  --external
```

**Export results to files:**
```bash
# JSON export
python broken_link_checker.py https://example.com --json results.json

# CSV export
python broken_link_checker.py https://example.com --csv results.csv

# Both formats
python broken_link_checker.py https://example.com \
  --json results.json \
  --csv results.csv
```

**Large website audit:**
```bash
python broken_link_checker.py https://mybigsite.com \
  --max-urls 1000 \
  --max-depth 4 \
  --delay 1.5 \
  --json comprehensive_audit.json \
  --csv comprehensive_audit.csv
```

## 📊 Output Formats

### Console Output

The tool provides real-time feedback with emoji indicators:
- 🕷️ Crawling pages
- ✅ Working links
- ❌ Broken links  
- ⚠️ Error links
- 📊 CSV report saved
- 💾 JSON report saved

### JSON Export

```json
{
  "scan_info": {
    "start_time": "2024-01-15T10:30:00",
    "end_time": "2024-01-15T10:35:30",
    "duration_seconds": 330.5,
    "start_domain": "example.com",
    "max_urls": 100,
    "max_depth": 2,
    "delay": 1.0,
    "same_domain_only": true
  },
  "statistics": {
    "total_urls_processed": 87,
    "working_links_count": 82,
    "broken_links_count": 3,
    "error_links_count": 2,
    "visited_pages_count": 15
  },
  "results": {
    "working_links": [...],
    "broken_links": [...],
    "error_links": [...]
  }
}
```

### CSV Export

| url | status | status_code | final_url | error | type | timestamp |
|-----|--------|-------------|-----------|-------|------|-----------|
| https://example.com/page1 | working | 200 | https://example.com/page1 | | | 2024-01-15T10:30:15 |
| https://example.com/broken | broken | 404 | https://example.com/broken | | | 2024-01-15T10:30:20 |
| https://timeout.com/page | error | | | Connection timeout | check | 2024-01-15T10:30:25 |

## 🎯 Use Cases

### Website Maintenance
- **Regular Health Checks**: Schedule weekly/monthly scans to catch broken links early
- **Post-Migration Audits**: Verify all links work after site migrations or redesigns
- **Content Updates**: Check links after major content updates

### SEO & Marketing
- **SEO Audits**: Broken links hurt SEO rankings - find and fix them
- **User Experience**: Ensure visitors don't hit dead ends
- **Link Building**: Verify outgoing links to maintain site credibility

### Development & QA
- **Pre-Launch Testing**: Scan staging sites before going live
- **Continuous Integration**: Integrate into CI/CD pipelines
- **Quality Assurance**: Regular checks as part of QA processes

## ⚙️ Configuration Tips

### Performance Tuning

**For small sites (< 100 pages):**
```bash
--max-urls 200 --max-depth 3 --delay 0.5
```

**For medium sites (100-1000 pages):**
```bash
--max-urls 500 --max-depth 2 --delay 1.0
```

**For large sites (1000+ pages):**
```bash
--max-urls 1000 --max-depth 2 --delay 2.0
```

### Respectful Crawling

- **Always use delays** (`--delay`) to avoid overwhelming servers
- **Start with smaller scans** to test site behavior
- **Monitor server response** and increase delays if needed
- **Consider time zones** - scan during off-peak hours for target sites

## 🚨 Common Issues & Solutions

### Issue: "Connection timeout" errors
**Solution**: Increase delay (`--delay 2`) or reduce concurrent requests

### Issue: "Too many requests" (429 errors)
**Solution**: Increase delay significantly (`--delay 5`) and reduce max URLs

### Issue: Running out of memory on large sites
**Solution**: Reduce `--max-urls` and run multiple smaller scans

### Issue: External links timing out
**Solution**: Use `--external` flag carefully, consider separate scans for internal/external

## 📄 Output File Examples

The tool generates detailed reports that can be used for:
- **Spreadsheet Analysis**: Open CSV in Excel/Google Sheets
- **Database Import**: Import CSV into databases for further analysis
- **API Integration**: Use JSON output in other tools and services
- **Reporting**: Generate management reports from the data

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional export formats (XML, HTML reports)
- Web interface
- Database storage options
- Advanced filtering options
- Performance optimizations

## 📜 License

This project is open source. Feel free to use, modify, and distribute.

## 🔧 Troubleshooting

### Dependencies Issues
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install requests beautifulsoup4 lxml
```

### Permission Issues
```bash
# Make script executable
chmod +x broken_link_checker.py

# Run with Python explicitly
python3 broken_link_checker.py https://example.com
```

### Memory Issues on Large Scans
- Use smaller `--max-urls` values
- Reduce `--max-depth`
- Run multiple focused scans instead of one large scan

---

**Happy Link Checking! 🔍✨**

For questions, issues, or feature requests, please open an issue in the repository.
