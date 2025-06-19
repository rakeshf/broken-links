import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import csv
import tempfile
import os
from broken_link_checker import BrokenLinkChecker


class TestBrokenLinkChecker:
    """Test suite for BrokenLinkChecker class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.checker = BrokenLinkChecker(max_urls=10, max_depth=1, delay=0.1)
        self.test_url = "https://example.com"
        self.test_domain = "example.com"
    
    def test_initialization(self):
        """Test BrokenLinkChecker initialization"""
        checker = BrokenLinkChecker(max_urls=50, max_depth=3, delay=2.0, same_domain_only=False)
        assert checker.max_urls == 50
        assert checker.max_depth == 3
        assert checker.delay == 2.0
        assert checker.same_domain_only == False
        assert checker.visited_urls == set()
        assert checker.checked_urls == set()
        assert checker.broken_links == []
        assert checker.working_links == []
        assert checker.error_links == []
        assert checker.urls_processed == 0
        assert checker.start_domain is None
    
    def test_is_valid_url(self):
        """Test URL validation"""
        # Valid URLs
        assert self.checker.is_valid_url("https://example.com") == True
        assert self.checker.is_valid_url("http://example.com") == True
        assert self.checker.is_valid_url("https://subdomain.example.com/path") == True
        
        # Invalid URLs
        assert self.checker.is_valid_url("") == False
        assert self.checker.is_valid_url("not-a-url") == False
        assert self.checker.is_valid_url("ftp://example.com") == True  # Has scheme and netloc
        assert self.checker.is_valid_url("//example.com") == False  # No scheme
    
    def test_is_same_domain(self):
        """Test domain filtering"""
        self.checker.start_domain = "example.com"
        self.checker.same_domain_only = True
        
        # Same domain
        assert self.checker.is_same_domain("https://example.com") == True
        assert self.checker.is_same_domain("https://example.com/path") == True
        
        # Different domain
        assert self.checker.is_same_domain("https://other.com") == False
        assert self.checker.is_same_domain("https://subdomain.example.com") == False
        
        # When same_domain_only is False
        self.checker.same_domain_only = False
        assert self.checker.is_same_domain("https://other.com") == True
    
    @patch('requests.get')
    def test_get_all_links_success(self, mock_get):
        """Test successful link extraction"""
        html_content = """
        <html>
        <body>
            <a href="https://example.com/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="https://external.com">External</a>
            <a href="mailto:test@example.com">Email</a>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        self.checker.start_domain = "example.com"
        self.checker.same_domain_only = True
        
        links = self.checker.get_all_links("https://example.com")
        
        # Should contain same-domain links only
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://external.com" not in links
    
    @patch('requests.get')
    def test_get_all_links_with_external(self, mock_get):
        """Test link extraction with external links enabled"""
        html_content = """
        <html>
        <body>
            <a href="https://example.com/page1">Page 1</a>
            <a href="https://external.com">External</a>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        self.checker.same_domain_only = False
        
        links = self.checker.get_all_links("https://example.com")
        
        # Should contain all valid links
        assert "https://example.com/page1" in links
        assert "https://external.com" in links
    
    @patch('requests.get')
    def test_get_all_links_request_error(self, mock_get):
        """Test link extraction when request fails"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        links = self.checker.get_all_links("https://example.com")
        
        assert links == set()
        assert len(self.checker.error_links) == 1
        assert self.checker.error_links[0]['url'] == "https://example.com"
        assert self.checker.error_links[0]['type'] == 'extraction'
        assert "Connection error" in self.checker.error_links[0]['error']
    
    @patch('requests.head')
    def test_check_link_working(self, mock_head):
        """Test checking a working link"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_head.return_value = mock_response
        
        self.checker.check_link("https://example.com")
        
        assert "https://example.com" in self.checker.checked_urls
        assert len(self.checker.working_links) == 1
        assert self.checker.working_links[0]['url'] == "https://example.com"
        assert self.checker.working_links[0]['status_code'] == 200
        assert self.checker.urls_processed == 1
    
    @patch('requests.head')
    def test_check_link_broken(self, mock_head):
        """Test checking a broken link"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.url = "https://example.com/notfound"
        mock_head.return_value = mock_response
        
        self.checker.check_link("https://example.com/notfound")
        
        assert len(self.checker.broken_links) == 1
        assert self.checker.broken_links[0]['url'] == "https://example.com/notfound"
        assert self.checker.broken_links[0]['status_code'] == 404
    
    @patch('requests.head')
    def test_check_link_redirect(self, mock_head):
        """Test checking a link that redirects"""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_response.url = "https://example.com/new-location"
        mock_head.return_value = mock_response
        
        self.checker.check_link("https://example.com/old-location")
        
        assert len(self.checker.working_links) == 1
        assert self.checker.working_links[0]['final_url'] == "https://example.com/new-location"
    
    @patch('requests.head')
    def test_check_link_error(self, mock_head):
        """Test checking a link that causes an error"""
        mock_head.side_effect = requests.exceptions.Timeout("Request timeout")
        
        self.checker.check_link("https://timeout.com")
        
        assert len(self.checker.error_links) == 1
        assert self.checker.error_links[0]['url'] == "https://timeout.com"
        assert self.checker.error_links[0]['type'] == 'check'
        assert "Request timeout" in self.checker.error_links[0]['error']
    
    def test_check_link_duplicate(self):
        """Test that duplicate URLs are not checked twice"""
        with patch('requests.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com"
            mock_head.return_value = mock_response
            
            # Check the same URL twice
            self.checker.check_link("https://example.com")
            self.checker.check_link("https://example.com")
            
            # Should only be called once
            assert mock_head.call_count == 1
            assert self.checker.urls_processed == 1
    
    def test_get_results_json(self):
        """Test JSON results generation"""
        # Add some test data
        self.checker.working_links = [
            {'url': 'https://example.com', 'status_code': 200, 'final_url': 'https://example.com', 'timestamp': '2024-01-01T00:00:00'}
        ]
        self.checker.broken_links = [
            {'url': 'https://example.com/404', 'status_code': 404, 'final_url': 'https://example.com/404', 'timestamp': '2024-01-01T00:01:00'}
        ]
        self.checker.error_links = [
            {'url': 'https://timeout.com', 'error': 'Timeout', 'type': 'check', 'timestamp': '2024-01-01T00:02:00'}
        ]
        self.checker.urls_processed = 3
        self.checker.start_domain = "example.com"
        
        results = self.checker.get_results_json()
        
        assert 'scan_info' in results
        assert 'statistics' in results
        assert 'results' in results
        
        # Check statistics
        assert results['statistics']['total_urls_processed'] == 3
        assert results['statistics']['working_links_count'] == 1
        assert results['statistics']['broken_links_count'] == 1
        assert results['statistics']['error_links_count'] == 1
        
        # Check scan info
        assert results['scan_info']['start_domain'] == "example.com"
        assert results['scan_info']['max_urls'] == 10
    
    def test_save_json_report(self):
        """Test JSON report saving"""
        # Add test data
        self.checker.working_links = [
            {'url': 'https://example.com', 'status_code': 200, 'final_url': 'https://example.com', 'timestamp': '2024-01-01T00:00:00'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_filename = f.name
        
        try:
            result = self.checker.save_json_report(temp_filename)
            assert result == True
            
            # Verify file contents
            with open(temp_filename, 'r') as f:
                data = json.load(f)
                assert 'scan_info' in data
                assert 'statistics' in data
                assert 'results' in data
        finally:
            os.unlink(temp_filename)
    
    def test_save_csv_report(self):
        """Test CSV report saving"""
        # Add test data
        self.checker.working_links = [
            {'url': 'https://example.com', 'status_code': 200, 'final_url': 'https://example.com', 'timestamp': '2024-01-01T00:00:00'}
        ]
        self.checker.broken_links = [
            {'url': 'https://example.com/404', 'status_code': 404, 'final_url': 'https://example.com/404', 'timestamp': '2024-01-01T00:01:00'}
        ]
        self.checker.error_links = [
            {'url': 'https://timeout.com', 'error': 'Timeout', 'type': 'check', 'timestamp': '2024-01-01T00:02:00'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_filename = f.name
        
        try:
            result = self.checker.save_csv_report(temp_filename)
            assert result == True
            
            # Verify file contents
            with open(temp_filename, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 3
                
                # Check working link
                working_row = next(row for row in rows if row['status'] == 'working')
                assert working_row['url'] == 'https://example.com'
                assert working_row['status_code'] == '200'
                
                # Check broken link
                broken_row = next(row for row in rows if row['status'] == 'broken')
                assert broken_row['url'] == 'https://example.com/404'
                assert broken_row['status_code'] == '404'
                
                # Check error link
                error_row = next(row for row in rows if row['status'] == 'error')
                assert error_row['url'] == 'https://timeout.com'
                assert error_row['error'] == 'Timeout'
        finally:
            os.unlink(temp_filename)


class TestBrokenLinkCheckerIntegration:
    """Integration tests for full crawling functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.checker = BrokenLinkChecker(max_urls=5, max_depth=1, delay=0.1)
    
    @patch('requests.get')
    @patch('requests.head')
    def test_crawl_website_basic(self, mock_head, mock_get):
        """Test basic website crawling"""
        # Mock the initial page
        html_content = """
        <html>
        <body>
            <a href="https://example.com/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
        </body>
        </html>
        """
        
        mock_get_response = Mock()
        mock_get_response.text = html_content
        mock_get.return_value = mock_get_response
        
        # Mock HEAD requests for link checking
        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head_response.url = "https://example.com"
        mock_head.return_value = mock_head_response
        
        self.checker.crawl_website("https://example.com")
        
        # Should have processed the main page and found links
        assert self.checker.urls_processed > 0
        assert self.checker.start_domain == "example.com"
        assert "https://example.com" in self.checker.visited_urls
    
    @patch('requests.get')
    @patch('requests.head')
    def test_crawl_website_with_broken_links(self, mock_head, mock_get):
        """Test crawling with mixed working and broken links"""
        html_content = """
        <html>
        <body>
            <a href="https://example.com/working">Working Link</a>
            <a href="https://example.com/broken">Broken Link</a>
        </body>
        </html>
        """
        
        mock_get_response = Mock()
        mock_get_response.text = html_content
        mock_get.return_value = mock_get_response
        
        # Mock different responses for different URLs
        def mock_head_side_effect(url, **kwargs):
            response = Mock()
            response.url = url
            if 'broken' in url:
                response.status_code = 404
            else:
                response.status_code = 200
            return response
        
        mock_head.side_effect = mock_head_side_effect
        
        self.checker.crawl_website("https://example.com")
        
        # Should have both working and broken links
        assert len(self.checker.working_links) > 0
        assert len(self.checker.broken_links) > 0
    
    @patch('requests.get')
    @patch('requests.head')
    def test_crawl_website_max_urls_limit(self, mock_head, mock_get):
        """Test that max_urls limit is respected"""
        # Create a page with many links
        links = ['<a href="https://example.com/page{0}">Page {0}</a>'.format(i) for i in range(20)]
        html_content = f"<html><body>{''.join(links)}</body></html>"
        
        mock_get_response = Mock()
        mock_get_response.text = html_content
        mock_get.return_value = mock_get_response
        
        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head_response.url = "https://example.com"
        mock_head.return_value = mock_head_response
        
        # Set a low max_urls limit
        self.checker.max_urls = 3
        self.checker.crawl_website("https://example.com")
        
        # Should not exceed max_urls
        assert self.checker.urls_processed <= 3


class TestBrokenLinkCheckerEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.checker = BrokenLinkChecker(max_urls=10, max_depth=1, delay=0.1)
    
    @patch('requests.get')
    def test_malformed_html(self, mock_get):
        """Test handling of malformed HTML"""
        malformed_html = "<html><body><a href='unclosed link</body></html>"
        
        mock_response = Mock()
        mock_response.text = malformed_html
        mock_get.return_value = mock_response
        
        # Should not crash on malformed HTML
        links = self.checker.get_all_links("https://example.com")
        assert isinstance(links, set)
    
    @patch('requests.get')
    def test_empty_html(self, mock_get):
        """Test handling of empty HTML"""
        mock_response = Mock()
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        links = self.checker.get_all_links("https://example.com")
        assert links == set()
    
    @patch('requests.get')
    def test_html_with_no_links(self, mock_get):
        """Test handling of HTML with no links"""
        html_content = "<html><body><p>No links here</p></body></html>"
        
        mock_response = Mock()
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        links = self.checker.get_all_links("https://example.com")
        assert links == set()
    
    def test_save_report_permission_error(self):
        """Test handling of file permission errors"""
        # Try to save to a directory that doesn't exist or has no permissions
        result = self.checker.save_json_report("/nonexistent/path/report.json")
        assert result == False
        
        result = self.checker.save_csv_report("/nonexistent/path/report.csv")
        assert result == False


# Pytest fixtures
@pytest.fixture
def sample_checker():
    """Fixture providing a sample BrokenLinkChecker instance"""
    return BrokenLinkChecker(max_urls=10, max_depth=2, delay=0.1)


@pytest.fixture
def mock_html_response():
    """Fixture providing a mock HTML response"""
    return """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <a href="https://example.com/page1">Page 1</a>
        <a href="https://example.com/page2">Page 2</a>
        <a href="https://external.com">External Link</a>
        <a href="/relative">Relative Link</a>
        <a href="mailto:test@example.com">Email Link</a>
    </body>
    </html>
    """


# Performance tests
class TestPerformance:
    """Performance-related tests"""
    
    def test_large_url_set_performance(self):
        """Test performance with large sets of URLs"""
        checker = BrokenLinkChecker(max_urls=1000, max_depth=1, delay=0)
        
        # Add many URLs to visited set
        for i in range(1000):
            checker.visited_urls.add(f"https://example.com/page{i}")
        
        # Should handle large sets efficiently
        assert len(checker.visited_urls) == 1000
        assert f"https://example.com/page500" in checker.visited_urls


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 