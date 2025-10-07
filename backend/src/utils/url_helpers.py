# backend\src\utils\url_helpers.py
"""
URL Helper Utilities
Handles URL validation, normalization, and analysis operations.
"""

import re
import validators
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, quote, unquote
from uuid import UUID


class URLHelper:
    """
    Utility class for URL operations: validation, normalization, and analysis.
    """
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Validate if a string is a properly formatted URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            Boolean indicating if URL is valid
        """
        try:
            return validators.url(url)
        except:
            return False
    
    @staticmethod
    def normalize_url(url: str, force_https: bool = True, remove_trailing_slash: bool = True) -> str:
        """
        Normalize a URL to a standard format.
        
        Args:
            url: URL to normalize
            force_https: Whether to convert HTTP to HTTPS
            remove_trailing_slash: Whether to remove trailing slashes
            
        Returns:
            Normalized URL
        """
        if not url:
            return url
            
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # Force HTTPS if requested
            if force_https and parsed.scheme == 'http':
                parsed = parsed._replace(scheme='https')
            
            # Remove trailing slash if requested
            path = parsed.path
            if remove_trailing_slash and path.endswith('/'):
                path = path.rstrip('/')
            
            # Reconstruct the URL
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),  # Normalize domain to lowercase
                path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            return normalized
            
        except Exception:
            return url
    
    @staticmethod
    def get_domain_from_url(url: str) -> Optional[str]:
        """
        Extract domain name from a URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name or None if invalid URL
        """
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                # Remove port number and www prefix if present
                domain = parsed.netloc.lower()
                if ':' in domain:
                    domain = domain.split(':')[0]
                if domain.startswith('www.'):
                    domain = domain[4:]
                return domain
            return None
        except:
            return None
    
    @staticmethod
    def get_base_url(url: str) -> Optional[str]:
        """
        Get base URL (scheme + domain) from a full URL.
        
        Args:
            url: Full URL
            
        Returns:
            Base URL or None if invalid
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
            return None
        except:
            return None
    
    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """
        Check if two URLs belong to the same domain.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            Boolean indicating if domains match
        """
        domain1 = URLHelper.get_domain_from_url(url1)
        domain2 = URLHelper.get_domain_from_url(url2)
        
        return domain1 is not None and domain1 == domain2
    
    @staticmethod
    def add_query_params(url: str, params: Dict[str, str]) -> str:
        """
        Add query parameters to a URL.
        
        Args:
            url: Base URL
            params: Dictionary of query parameters to add
            
        Returns:
            URL with added query parameters
        """
        try:
            parsed = urlparse(url)
            query_dict = parse_qs(parsed.query)
            
            # Update with new parameters
            for key, value in params.items():
                query_dict[key] = [value]
            
            # Build new query string
            new_query = urlencode(query_dict, doseq=True)
            
            # Reconstruct URL
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            
        except Exception:
            return url
    
    @staticmethod
    def remove_query_params(url: str, params_to_remove: List[str]) -> str:
        """
        Remove specific query parameters from a URL.
        
        Args:
            url: URL to modify
            params_to_remove: List of parameter names to remove
            
        Returns:
            URL with specified parameters removed
        """
        try:
            parsed = urlparse(url)
            query_dict = parse_qs(parsed.query)
            
            # Remove specified parameters
            for param in params_to_remove:
                query_dict.pop(param, None)
            
            # Build new query string
            new_query = urlencode(query_dict, doseq=True)
            
            # Reconstruct URL
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            
        except Exception:
            return url
    
    @staticmethod
    def encode_url_component(component: str) -> str:
        """
        URL-encode a string component.
        
        Args:
            component: String to encode
            
        Returns:
            URL-encoded string
        """
        return quote(component, safe='')
    
    @staticmethod
    def decode_url_component(component: str) -> str:
        """
        URL-decode a string component.
        
        Args:
            component: String to decode
            
        Returns:
            URL-decoded string
        """
        return unquote(component)
    
    @staticmethod
    def extract_path_segments(url: str) -> List[str]:
        """
        Extract path segments from a URL.
        
        Args:
            url: URL to parse
            
        Returns:
            List of path segments
        """
        try:
            parsed = urlparse(url)
            # Remove empty segments and leading/trailing slashes
            segments = [seg for seg in parsed.path.split('/') if seg]
            return segments
        except:
            return []
    
    @staticmethod
    def is_internal_link(base_url: str, link_url: str) -> bool:
        """
        Check if a link is internal to a base URL.
        
        Args:
            base_url: Base website URL
            link_url: Link URL to check
            
        Returns:
            Boolean indicating if link is internal
        """
        if not link_url or not base_url:
            return False
            
        # Handle relative URLs
        if link_url.startswith('/') or link_url.startswith('#'):
            return True
            
        # Handle absolute URLs
        base_domain = URLHelper.get_domain_from_url(base_url)
        link_domain = URLHelper.get_domain_from_url(link_url)
        
        return base_domain is not None and base_domain == link_domain
    
    @staticmethod
    def make_absolute_url(base_url: str, relative_url: str) -> str:
        """
        Convert a relative URL to absolute using a base URL.
        
        Args:
            base_url: Base absolute URL
            relative_url: Relative URL to convert
            
        Returns:
            Absolute URL
        """
        if not relative_url:
            return base_url
            
        # If already absolute, return as-is
        if URLHelper.is_valid_url(relative_url):
            return relative_url
            
        try:
            base_parsed = urlparse(base_url)
            
            # Handle different relative URL types
            if relative_url.startswith('//'):
                # Protocol-relative URL
                return f"{base_parsed.scheme}:{relative_url}"
                
            elif relative_url.startswith('/'):
                # Root-relative URL
                return f"{base_parsed.scheme}://{base_parsed.netloc}{relative_url}"
                
            elif relative_url.startswith('#'):
                # Fragment URL
                return f"{base_url}{relative_url}"
                
            else:
                # Path-relative URL
                base_path = base_parsed.path
                if not base_path.endswith('/'):
                    base_path = base_path.rsplit('/', 1)[0] + '/'
                return f"{base_parsed.scheme}://{base_parsed.netloc}{base_path}{relative_url}"
                
        except Exception:
            return base_url
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize a URL by removing potentially dangerous components.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
        """
        try:
            parsed = urlparse(url)
            
            # Remove JavaScript and data URIs
            if parsed.scheme in ['javascript', 'data']:
                return ''
                
            # Remove suspicious query parameters
            query_dict = parse_qs(parsed.query)
            suspicious_params = ['javascript', 'onload', 'onerror', 'onclick']
            for param in suspicious_params:
                query_dict.pop(param, None)
                
            # Rebuild query string
            new_query = urlencode(query_dict, doseq=True)
            
            # Reconstruct sanitized URL
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            
        except Exception:
            return url
    
    @staticmethod
    def extract_utm_params(url: str) -> Dict[str, str]:
        """
        Extract UTM parameters from a URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary of UTM parameters
        """
        utm_params = {}
        try:
            parsed = urlparse(url)
            query_dict = parse_qs(parsed.query)
            
            utm_keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
            for key in utm_keys:
                if key in query_dict:
                    utm_params[key] = query_dict[key][0]
                    
        except Exception:
            pass
            
        return utm_params
    
    @staticmethod
    def generate_canonical_url(url: str) -> str:
        """
        Generate a canonical URL by removing tracking parameters and normalizing.
        
        Args:
            url: Original URL
            
        Returns:
            Canonical URL
        """
        try:
            # Remove common tracking parameters
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'msclkid', 'dclid', 'yclid',
                '_ga', '_gl', 'mc_cid', 'mc_eid'
            ]
            
            cleaned_url = URLHelper.remove_query_params(url, tracking_params)
            return URLHelper.normalize_url(cleaned_url)
            
        except Exception:
            return url


# Create a singleton instance
url_helper = URLHelper()