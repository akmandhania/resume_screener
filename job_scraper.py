#!/usr/bin/env python3
"""
Job Description Scraper
Scrapes job descriptions from various job posting websites
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple
import time

class JobDescriptionScraper:
    """Scraper for job descriptions from various websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_job_description(self, url: str) -> Tuple[bool, str, str, str]:
        """
        Scrape job description and company name from a URL
        
        Args:
            url: The job posting URL
            
        Returns:
            Tuple of (success, title, description, company)
        """
        # Clean the URL
        url = url.strip()
        if not url.startswith('http'):
            return False, "", "", "Invalid URL format"
        
        try:
            # Parse the URL to determine the website
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Try scraping with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    if 'linkedin.com' in domain:
                        result = self._scrape_linkedin(url)
                    elif 'indeed.com' in domain:
                        result = self._scrape_indeed(url)
                    elif 'glassdoor.com' in domain:
                        result = self._scrape_glassdoor(url)
                    elif 'monster.com' in domain:
                        result = self._scrape_monster(url)
                    elif 'careerbuilder.com' in domain:
                        result = self._scrape_careerbuilder(url)
                    else:
                        result = self._scrape_generic(url)
                    
                    # If we got a result, return it
                    if result[0]:  # success
                        return result
                    
                    # If this is the last attempt, return the error
                    if attempt == max_retries - 1:
                        return result
                    
                    # Wait before retrying
                    time.sleep(1)
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        return False, "", "", f"Error scraping job description: {str(e)}"
                    time.sleep(1)
            
            return False, "", "", "Failed to scrape after multiple attempts"
                
        except Exception as e:
            return False, "", "", f"Error parsing URL: {str(e)}"
    
    def _scrape_linkedin(self, url: str) -> Tuple[bool, str, str, str]:
        """Scrape job description from LinkedIn, prioritizing 'About the job' section if present"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # --- Title extraction (unchanged) ---
            title = ""
            title_selectors = [
                'h1[class*="job-title"]', 'h1[class*="title"]', '.job-title', '.title', '[data-testid="job-title"]',
                '[class*="job-title"]', 'h1[class*="text-heading"]', 'h1', 'h2', '[class*="title"]', '[class*="heading"]',
                '[data-testid="job-details-jobs-unified-top-card-job-title"]', '[class*="jobs-unified-top-card__job-title"]',
                '[class*="jobs-unified-top-card__title"]', 'h1:first-of-type', 'h2:first-of-type'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 3 and len(title) < 200:
                        break
            if not title or len(title) < 3:
                page_title = soup.find('title')
                if page_title:
                    title_text = page_title.get_text(strip=True)
                    if ' at ' in title_text:
                        title = title_text.split(' at ')[0].strip()
                    elif ' | ' in title_text:
                        title = title_text.split(' | ')[0].strip()
                    elif ' - ' in title_text:
                        title = title_text.split(' - ')[0].strip()

            # --- More targeted job description extraction ---
            description = ""
            
            # First, try to find the main job description container
            # Look for specific LinkedIn job description containers
            main_desc_selectors = [
                '[class*="jobs-description__content"]',
                '[class*="jobs-box__html-content"]',
                '[class*="jobs-description-content__text"]',
                '[class*="job-description__content"]',
                '[class*="description__text"]',
                '.show-more-less-html',
                '[data-testid="job-description"]',
                '[data-testid="job-details-jobs-unified-top-card-job-description"]'
            ]
            
            for selector in main_desc_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    # Filter out content that's clearly UI boilerplate
                    if text and len(text) > 200:
                        # Check if this looks like actual job content (not UI elements)
                        ui_indicators = [
                            'apply', 'join', 'sign in', 'first name', 'last name', 'email', 'password',
                            'agree & join', 'continue', 'security verification', 'already on linkedin',
                            'new to linkedin', 'remove photo', 'forgot password', 'show', 'hide'
                        ]
                        
                        has_ui_content = any(indicator in text.lower() for indicator in ui_indicators)
                        job_indicators = [
                            'requirements', 'qualifications', 'responsibilities', 'about', 'role', 'position',
                            'experience', 'skills', 'duties', 'expectations', 'candidate', 'applicant',
                            'job description', 'what you will do', 'what you\'ll do', 'key responsibilities',
                            'essential functions', 'opportunity', 'mission', 'company', 'team'
                        ]
                        
                        has_job_content = any(indicator in text.lower() for indicator in job_indicators)
                        
                        # Prefer content that has job indicators and minimal UI content
                        if has_job_content and not has_ui_content and len(text) > len(description):
                            description = text
                        elif not description and len(text) > 500:  # Fallback to longer content
                            description = text
            
            # If we still don't have good content, try to extract from specific sections
            if not description or len(description) < 500:
                # Look for sections that typically contain job descriptions
                section_indicators = [
                    'about the job', 'about us', 'about the company', 'what\'s the opportunity',
                    'what will i be doing', 'what skills do i need', 'requirements', 'qualifications'
                ]
                
                for indicator in section_indicators:
                    # Find elements containing these indicators
                    elements = soup.find_all(text=re.compile(indicator, re.IGNORECASE))
                    for elem in elements:
                        if elem.parent:
                            # Get the parent element and extract content from there
                            parent = elem.parent
                            # Look for the next few siblings or children that contain substantial text
                            content_parts = []
                            
                            # Try to get content from siblings
                            for sibling in parent.find_next_siblings():
                                if sibling.name in ['p', 'div', 'li', 'ul', 'ol']:
                                    sibling_text = sibling.get_text(strip=True)
                                    if sibling_text and len(sibling_text) > 20:
                                        content_parts.append(sibling_text)
                                    if len(content_parts) > 10:  # Limit to avoid too much content
                                        break
                            
                            # If we found content, use it
                            if content_parts:
                                description = '\n'.join(content_parts)
                                if len(description) > 500:
                                    break
            
            # Clean up the description
            if description:
                # Remove common unwanted text
                unwanted_patterns = [
                    r'\bcookie\b', r'\bprivacy policy\b', r'\bterms of service\b', r'©.*?all rights reserved',
                    r'\bpowered by\b', r'\bloading\.\.\.\b', r'\bpay found in job post\b', r'\bretrieved from the description\b',
                    r'base pay range\s*\$[\d,]+\.?\d*\s*-\s*\$[\d,]+\.?\d*\s*yr',
                    r'pay range\s*\$[\d,]+\.?\d*\s*-\s*\$[\d,]+\.?\d*\s*yr',
                    # Remove LinkedIn UI elements - be more specific to avoid removing job content
                    r'\bapply\b', r'join or sign in', r'first name', r'last name', r'email', r'password',
                    r'agree & join', r'continue', r'security verification', r'already on linkedin',
                    r'new to linkedin', r'remove photo', r'forgot password',
                    r'use ai to assess', r'am i a good fit', r'tailor my resume', r'sign in to access',
                    r'welcome back', r'not you\?', r'by clicking.*?policy', r'\bor\b', r'you may also apply'
                ]
                
                for pattern in unwanted_patterns:
                    description = re.sub(pattern, '', description, flags=re.IGNORECASE)
                
                description = re.sub(r'\s+', ' ', description).strip()
            
            # Try to extract company name from various sources
            company = ""
            company_selectors = [
                # LinkedIn specific selectors
                '[data-testid="job-details-jobs-unified-top-card-company-name"]',
                '[class*="jobs-unified-top-card__company-name"]',
                '[class*="company-name"]',
                '[class*="employer"]',
                '[class*="organization"]',
                # More generic selectors
                '[class*="company"]',
                '.company',
                '.employer',
                '.organization'
            ]
            
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    if company and len(company) > 2 and len(company) < 100:
                        break

            # Always run page title logic if company is empty or whitespace
            if not company or not company.strip():
                page_title = soup.find('title')
                if page_title:
                    title_text = page_title.get_text(strip=True)
                    print(f"Debug: Page title: {title_text}")  # Debug line
                    # LinkedIn title format: "Company hiring Job Title in Location | LinkedIn"
                    if ' hiring ' in title_text:
                        company = title_text.split(' hiring ')[0].strip()
                    # LinkedIn title format: "Job Title - Company | LinkedIn"
                    elif ' - ' in title_text:
                        parts = title_text.split(' - ')
                        if len(parts) > 1:
                            company = parts[1].split(' | ')[0].strip()
                    # LinkedIn title format: "Job Title at Company | LinkedIn"
                    elif ' at ' in title_text:
                        company = title_text.split(' at ')[1].split(' | ')[0].strip()

            # Clean up company name - remove common UI text
            if company:
                # Remove common UI text that might be mistaken for company names
                ui_text_patterns = [
                    r'you may also apply directly on.*?website',
                    r'apply directly on.*?website',
                    r'powered by.*',
                    r'©.*?all rights reserved',
                    r'loading\.\.\.',
                    r'pay found in job post',
                    r'retrieved from the description'
                ]
                
                for pattern in ui_text_patterns:
                    company = re.sub(pattern, '', company, flags=re.IGNORECASE)
                
                company = company.strip()
                
                # If company is too short or contains suspicious text, try to extract from description
                if len(company) < 3 or any(suspicious in company.lower() for suspicious in ['apply', 'website', 'directly', 'loading']):
                    company = ""
            
            # If still no company found, try to extract from job description using patterns
            if not company:
                # Try to extract company from job description using patterns
                company_patterns = [
                    r'role at ([A-Z][a-zA-Z0-9\s&]+?)(?:\s|$|\.|,)',
                    r'at ([A-Z][a-zA-Z0-9\s&]+?)(?:\s+is|\s+seeking|\s+looking|\s+needs)',
                    r'([A-Z][a-zA-Z0-9\s&]+?)\s+is\s+seeking',
                    r'([A-Z][a-zA-Z0-9\s&]+?)\s+looking\s+for',
                    r'join ([A-Z][a-zA-Z0-9\s&]+?)\s+as',
                    r'([A-Z][a-zA-Z0-9\s&]+?)\s+is\s+hiring',
                    r'([A-Z][a-zA-Z0-9\s&]+?)\s+has\s+an\s+opening',
                    r'([A-Z][a-zA-Z0-9\s&]+?)\s+San Mateo',
                    r'([A-Z][a-zA-Z0-9\s&]+?)\s+CA',
                ]
                
                for pattern in company_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        extracted_company = match.group(1).strip()
                        # Validate the extracted company name
                        if (len(extracted_company) > 2 and len(extracted_company) < 50 and
                            not any(word in extracted_company.lower() for word in ['gaps', 'patient', 'care', 'healthcare', 'quality', 'systems', 'hospitals', 'payers', 'use', 'improve', 'drive', 'member', 'enrollment', 'acquisition', 'retention', 'reimbursement', 'scaling', 'growth', 'hiring', 'staff'])):
                            company = extracted_company
                            break

            # Final fallback: extract the first capitalized word from the description
            if not company:
                match = re.match(r'([A-Z][a-zA-Z0-9&]*)', description.strip())
                if match:
                    company = match.group(1)
            
            if description and len(description) > 200:
                return True, title, description, company
            else:
                return False, "", "Could not find complete job description on LinkedIn page. The page may use dynamic loading or have restricted access."
        except Exception as e:
            return False, "", "", f"Error scraping LinkedIn: {str(e)}"
    
    def _scrape_indeed(self, url: str) -> Tuple[bool, str, str, str]:
        """Scrape job description and company name from Indeed"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job title with multiple selectors
            title = ""
            title_selectors = [
                'h1[data-testid="jobsearch-JobInfoHeader-title"]',
                'h1[class*="jobsearch-JobInfoHeader-title"]',
                'h1[class*="title"]',
                'h1',
                '[data-testid="job-title"]',
                '[class*="job-title"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 3:
                        break
            
            # Find job description with multiple selectors
            description = ""
            desc_selectors = [
                '[data-testid="jobsearch-JobComponent-description"]',
                '[class*="jobsearch-JobComponent-description"]',
                '[class*="job-description"]',
                '[class*="description"]',
                '.job-description',
                '.description',
                '[data-testid="job-description"]'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if description and len(description) > 100:
                        break
            
            # Try to extract company name
            company = ""
            company_selectors = [
                '[data-testid="jobsearch-JobInfoHeader-companyName"]',
                '[class*="company-name"]',
                '[class*="employer"]',
                '.company-name',
                '.employer'
            ]
            
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    if company and len(company) > 2:
                        break
            
            if description:
                return True, title, description, company
            else:
                return False, "", "Could not find job description on Indeed page"
                
        except Exception as e:
            return False, "", "", f"Error scraping Indeed: {str(e)}"
    
    def _scrape_glassdoor(self, url: str) -> Tuple[bool, str, str, str]:
        """Scrape job description and company name from Glassdoor"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job title
            title = ""
            title_elem = soup.select_one('h1[class*="job-title"]')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Find job description
            description = ""
            desc_elem = soup.select_one('[class*="job-description"]')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            if description:
                return True, title, description, "" # Glassdoor doesn't have a dedicated company name selector
            else:
                return False, "", "Could not find job description on Glassdoor page"
                
        except Exception as e:
            return False, "", "", f"Error scraping Glassdoor: {str(e)}"
    
    def _scrape_monster(self, url: str) -> Tuple[bool, str, str, str]:
        """Scrape job description and company name from Monster"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job title
            title = ""
            title_elem = soup.select_one('h1[class*="title"]')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Find job description
            description = ""
            desc_elem = soup.select_one('[class*="job-description"]')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            if description:
                return True, title, description, "" # Monster doesn't have a dedicated company name selector
            else:
                return False, "", "Could not find job description on Monster page"
                
        except Exception as e:
            return False, "", "", f"Error scraping Monster: {str(e)}"
    
    def _scrape_careerbuilder(self, url: str) -> Tuple[bool, str, str, str]:
        """Scrape job description and company name from CareerBuilder"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job title
            title = ""
            title_elem = soup.select_one('h1[class*="title"]')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Find job description
            description = ""
            desc_elem = soup.select_one('[class*="job-description"]')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            if description:
                return True, title, description, "" # CareerBuilder doesn't have a dedicated company name selector
            else:
                return False, "", "Could not find job description on CareerBuilder page"
                
        except Exception as e:
            return False, "", "", f"Error scraping CareerBuilder: {str(e)}"
    
    def _scrape_generic(self, url: str) -> Tuple[bool, str, str, str]:
        """Generic scraper for unknown websites"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find job title
            title = ""
            title_selectors = ['h1', 'h2', '.title', '.job-title', '[class*="title"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Try to find job description
            description = ""
            desc_selectors = [
                '[class*="description"]',
                '[class*="job-description"]',
                '.description',
                '.job-description',
                'main',
                'article'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if len(description) > 100:  # Ensure we got meaningful content
                        break
            
            if description:
                return True, title, description, "" # Generic sites don't have a dedicated company name selector
            else:
                return False, "", "Could not find job description on this page"
                
        except Exception as e:
            return False, "", "", f"Error scraping generic page: {str(e)}"
    
    def clean_description(self, description: str) -> str:
        """Clean and format the scraped description"""
        if not description:
            return ""
        
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove common unwanted text - be conservative to preserve job content
        unwanted_patterns = [
            r'\bcookie\b',
            r'\bprivacy policy\b',
            r'\bterms of service\b',
            r'©.*?all rights reserved',
            r'\bpowered by\b',
            r'\bloading\.\.\.\b',
            # More specific pay range patterns to avoid removing job content
            r'base pay range\s*\$[\d,]+\.?\d*\s*-\s*\$[\d,]+\.?\d*\s*yr',
            r'pay range\s*\$[\d,]+\.?\d*\s*-\s*\$[\d,]+\.?\d*\s*yr',
        ]
        
        for pattern in unwanted_patterns:
            description = re.sub(pattern, '', description, flags=re.IGNORECASE)
        
        # Clean up the text
        description = description.strip()
        
        # Limit length if too long
        if len(description) > 5000:
            description = description[:5000] + "..."
        
        return description

# Create a global instance
job_scraper = JobDescriptionScraper() 