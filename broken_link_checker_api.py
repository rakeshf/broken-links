import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import time
import json
import csv
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import re

SCAN_DB_FILE = "scan_db.json"
DOWNLOAD_DIR = "downloads"

class BrokenLinkChecker:
    def __init__(self, max_urls=100, max_depth=2, delay=1.0, same_domain_only=True):
        self.visited_urls = set()
        self.checked_urls = set()
        self.broken_links = []
        self.working_links = []
        self.error_links = []
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.delay = delay
        self.same_domain_only = same_domain_only
        self.start_domain = None
        self.urls_processed = 0
        self.start_time = datetime.now()
        
    def is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    
    def is_same_domain(self, url):
        if not self.same_domain_only or not self.start_domain:
            return True
        parsed = urlparse(url)
        return parsed.netloc == self.start_domain
    
    def get_all_links(self, url):
        links = set()
        try:
            print(f"[*] Extracting links from: {url}")
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Get all anchor tags with href
            for a_tag in soup.find_all("a", href=True):
                try:
                    href_attr = a_tag.attrs.get('href', '')
                    if href_attr and isinstance(href_attr, str):
                        full_url = urljoin(url, href_attr)
                        if self.is_valid_url(full_url):
                            # Filter by domain if same_domain_only is True
                            if self.same_domain_only and not self.is_same_domain(full_url):
                                continue
                            links.add(full_url)
                except (AttributeError, KeyError):
                    # Skip tags that don't have proper href attributes
                    continue
                    
        except Exception as e:
            print(f"[!] Error getting links from {url}: {e}")
            self.error_links.append({
                'url': url, 
                'error': str(e), 
                'type': 'extraction',
                'timestamp': datetime.now().isoformat()
            })
        
        return links
    
    def check_link(self, url):
        if url in self.checked_urls:
            return
            
        self.checked_urls.add(url)
        self.urls_processed += 1
        
        try:
            print(f"[{self.urls_processed}/{self.max_urls}] Checking: {url}")
            response = requests.head(url, allow_redirects=True, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code >= 400:
                print(f"  ❌ [BROKEN] Status code: {response.status_code}")
                self.broken_links.append({
                    'url': url, 
                    'status_code': response.status_code,
                    'final_url': response.url,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"  ✅ [OK] Status code: {response.status_code}")
                self.working_links.append({
                    'url': url, 
                    'status_code': response.status_code,
                    'final_url': response.url,
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            print(f"  ⚠️  [ERROR] {e}")
            self.error_links.append({
                'url': url, 
                'error': str(e), 
                'type': 'check',
                'timestamp': datetime.now().isoformat()
            })
        
        # Add delay to be respectful to the server
        if self.delay > 0:
            time.sleep(self.delay)
    
    def crawl_website(self, start_url, current_depth=0):
        if current_depth > self.max_depth or self.urls_processed >= self.max_urls:
            return
            
        if start_url in self.visited_urls:
            return
            
        self.visited_urls.add(start_url)
        
        # Set start domain for filtering
        if self.start_domain is None:
            parsed = urlparse(start_url)
            self.start_domain = parsed.netloc
        
        print(f"\n[🕷️ ] Crawling (depth {current_depth}): {start_url}")
        
        # Check the current URL
        self.check_link(start_url)
        
        if self.urls_processed >= self.max_urls:
            print(f"\n[*] Reached maximum URL limit ({self.max_urls}). Stopping crawl.")
            return
        
        # Get all links from current page
        links = self.get_all_links(start_url)
        
        # Check each link found on the page
        for link in links:
            if self.urls_processed >= self.max_urls:
                break
                
            self.check_link(link)
        
        # Recursively crawl links (only if we haven't hit the limit)
        if current_depth < self.max_depth and self.urls_processed < self.max_urls:
            for link in links:
                if self.urls_processed >= self.max_urls:
                    break
                self.crawl_website(link, current_depth + 1)
    
    def get_results_json(self):
        """Return results in JSON format"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        return {
            "scan_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": round(duration, 2),
                "start_domain": self.start_domain,
                "max_urls": self.max_urls,
                "max_depth": self.max_depth,
                "delay": self.delay,
                "same_domain_only": self.same_domain_only
            },
            "statistics": {
                "total_urls_processed": self.urls_processed,
                "working_links_count": len(self.working_links),
                "broken_links_count": len(self.broken_links),
                "error_links_count": len(self.error_links),
                "visited_pages_count": len(self.visited_urls)
            },
            "results": {
                "working_links": self.working_links,
                "broken_links": self.broken_links,
                "error_links": self.error_links
            }
        }
    
    def save_json_report(self, filename):
        """Save results to JSON file"""
        try:
            results = self.get_results_json()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 JSON report saved to: {filename}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving JSON report: {e}")
            return False
    
    def save_csv_report(self, filename):
        """Save results to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['url', 'status', 'status_code', 'final_url', 'error', 'type', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write working links
                for link in self.working_links:
                    writer.writerow({
                        'url': link['url'],
                        'status': 'working',
                        'status_code': link['status_code'],
                        'final_url': link['final_url'],
                        'error': '',
                        'type': '',
                        'timestamp': link['timestamp']
                    })
                
                # Write broken links
                for link in self.broken_links:
                    writer.writerow({
                        'url': link['url'],
                        'status': 'broken',
                        'status_code': link['status_code'],
                        'final_url': link['final_url'],
                        'error': '',
                        'type': '',
                        'timestamp': link['timestamp']
                    })
                
                # Write error links
                for link in self.error_links:
                    writer.writerow({
                        'url': link['url'],
                        'status': 'error',
                        'status_code': '',
                        'final_url': '',
                        'error': link['error'],
                        'type': link['type'],
                        'timestamp': link['timestamp']
                    })
            
            print(f"\n📊 CSV report saved to: {filename}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving CSV report: {e}")
            return False
    
    def print_summary(self, json_output=None, csv_output=None):
        print("\n" + "="*60)
        print("🔍 BROKEN LINK CHECKER SUMMARY")
        print("="*60)
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print(f"Scan Duration: {duration:.2f} seconds")
        print(f"Total URLs processed: {self.urls_processed}")
        print(f"Working links: {len(self.working_links)}")
        print(f"Broken links: {len(self.broken_links)}")
        print(f"Error links: {len(self.error_links)}")
        
        if self.broken_links:
            print(f"\n❌ BROKEN LINKS ({len(self.broken_links)}):")
            for link in self.broken_links:
                print(f"  • {link['url']} (Status: {link['status_code']})")
        
        if self.error_links:
            print(f"\n⚠️  ERROR LINKS ({len(self.error_links)}):")
            for link in self.error_links:
                print(f"  • {link['url']} ({link['error']})")
        
        print("\n" + "="*60)
        
        # Save reports if requested
        if json_output:
            self.save_json_report(json_output)
        
        if csv_output:
            self.save_csv_report(csv_output)

def load_scans():
    if not os.path.exists(SCAN_DB_FILE):
        return {}
    with open(SCAN_DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Reconstruct BrokenLinkChecker objects from stored dicts
    scans = {}
    for scan_id, scan_data in data.items():
        checker = BrokenLinkChecker(
            max_urls=scan_data["scan_info"]["max_urls"],
            max_depth=scan_data["scan_info"]["max_depth"],
            delay=scan_data["scan_info"]["delay"],
            same_domain_only=scan_data["scan_info"]["same_domain_only"]
        )
        checker.start_domain = scan_data["scan_info"]["start_domain"]
        checker.urls_processed = scan_data["statistics"]["total_urls_processed"]
        checker.working_links = scan_data["results"]["working_links"]
        checker.broken_links = scan_data["results"]["broken_links"]
        checker.error_links = scan_data["results"]["error_links"]
        scans[scan_id] = checker
    return scans

def save_scans(scans):
    data = {}
    for scan_id, checker in scans.items():
        data[scan_id] = checker.get_results_json()
    with open(SCAN_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

app = FastAPI()
scans = load_scans()  # Load from file at startup

class ScanRequest(BaseModel):
    url: str
    max_urls: Optional[int] = 100
    max_depth: Optional[int] = 2
    delay: Optional[float] = 1.0
    same_domain_only: Optional[bool] = True

# Ensure the download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def safe_filename_from_url(url: str, date: str = None) -> str:
    # Remove scheme and replace non-alphanumeric with underscores
    name = re.sub(r'^https?://', '', url)
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    return f"{name}_{date}.json"

@app.post("/scan")
def start_scan(request: ScanRequest):
    scan_id = str(uuid.uuid4())
    checker = BrokenLinkChecker(
        max_urls=request.max_urls,
        max_depth=request.max_depth,
        delay=request.delay,
        same_domain_only=request.same_domain_only
    )
    try:
        checker.crawl_website(request.url)
        scans[scan_id] = checker
        save_scans(scans)  # Save to file after each scan

        # Create filename from URL and date in the download directory
        filename = safe_filename_from_url(request.url, datetime.now().strftime("%Y%m%d"))
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(checker.get_results_json(), f, indent=2, ensure_ascii=False)

        return {
            "message": "Scan completed",
            "scan_id": scan_id,
            "result_file": filepath,
            "statistics": checker.get_results_json()["statistics"],
            "max_urls": checker.max_urls
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/results/{scan_id}")
def get_results(scan_id: str):
    checker = scans.get(scan_id)
    if not checker:
        raise HTTPException(status_code=404, detail="Scan ID not found.")
    return checker.get_results_json()

@app.get("/status/{scan_id}")
def get_status(scan_id: str):
    checker = scans.get(scan_id)
    if not checker:
        raise HTTPException(status_code=404, detail="Scan ID not found.")
    status = (
        "completed"
        if checker.urls_processed >= checker.max_urls
        else "in_progress"
    )
    return {
        "status": status,
        "total_urls_processed": checker.urls_processed,
        "working_links": len(checker.working_links),
        "broken_links": len(checker.broken_links),
        "error_links": len(checker.error_links),
        "broken_links_list": checker.broken_links,
        "error_links_list": checker.error_links,
        "start_domain": checker.start_domain,
        "max_urls": checker.max_urls,
        "max_depth": checker.max_depth,
        "delay": checker.delay,
        "same_domain_only": checker.same_domain_only
    }

def main():
    print("Please use this script via the API (run with 'python broken_link_checker.py api') or import the BrokenLinkChecker class in your own script.")

# Optional: Run FastAPI if this script is executed directly
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        import uvicorn
        uvicorn.run("broken_link_checker:app", host="0.0.0.0", port=8000, reload=True)
    else:
        main()
