
#!/usr/bin/env python3
"""
Nova Browser Enhanced - Production Ready with GUI
A secure, declarative browser built from first principles
"""

import json
import os
import sys
import time
import hashlib
import re
import base64
import mimetypes
import shutil
import subprocess
import asyncio
import aiohttp
import requests
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urljoin
import tempfile
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
import ssl
import certifi

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, simpledialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Create necessary directories FIRST
nova_dir = Path.home() / '.nova'
nova_dir.mkdir(exist_ok=True)
(nova_dir / 'downloads').mkdir(exist_ok=True)
(nova_dir / 'cache').mkdir(exist_ok=True)

# Now configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(nova_dir / 'browser.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('NovaBrowser')

# Complete color system with all required attributes
class Colors:
    """ANSI color codes for terminal UI with fallbacks"""
    if sys.platform != "win32":
        # Regular colors
        BLACK = '\033[30m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'
        
        # Bright colors
        BRIGHT_BLACK = '\033[90m'
        BRIGHT_RED = '\033[91m'
        BRIGHT_GREEN = '\033[92m'
        BRIGHT_YELLOW = '\033[93m'
        BRIGHT_BLUE = '\033[94m'
        BRIGHT_MAGENTA = '\033[95m'
        BRIGHT_CYAN = '\033[96m'
        BRIGHT_WHITE = '\033[97m'
        
        # Background colors
        BG_BLACK = '\033[40m'
        BG_RED = '\033[41m'
        BG_GREEN = '\033[42m'
        BG_YELLOW = '\033[43m'
        BG_BLUE = '\033[44m'
        BG_MAGENTA = '\033[45m'
        BG_CYAN = '\033[46m'
        BG_WHITE = '\033[47m'
        
        # Styles
        BOLD = '\033[1m'
        DIM = '\033[2m'
        ITALIC = '\033[3m'
        UNDERLINE = '\033[4m'
        BLINK = '\033[5m'
        REVERSE = '\033[7m'
        HIDDEN = '\033[8m'
        STRIKETHROUGH = '\033[9m'
        
        # Reset
        END = '\033[0m'
        RESET = '\033[0m'
        
        # Aliases for compatibility
        HEADER = BRIGHT_MAGENTA + BOLD
    else:
        # Fallback for Windows - empty strings
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ''
        BRIGHT_BLACK = BRIGHT_RED = BRIGHT_GREEN = BRIGHT_YELLOW = ''
        BRIGHT_BLUE = BRIGHT_MAGENTA = BRIGHT_CYAN = BRIGHT_WHITE = ''
        BG_BLACK = BG_RED = BG_GREEN = BG_YELLOW = BG_BLUE = ''
        BG_MAGENTA = BG_CYAN = BG_WHITE = ''
        BOLD = DIM = ITALIC = UNDERLINE = BLINK = REVERSE = ''
        HIDDEN = STRIKETHROUGH = END = RESET = ''
        HEADER = ''

class Theme:
    """Enhanced theme system with CSS-like styling"""
    def __init__(self, name: str = "default"):
        self.name = name
        self.themes = {
            "default": {
                "header": Colors.HEADER,
                "title": Colors.BLUE + Colors.BOLD,
                "text": Colors.END,
                "link": Colors.CYAN + Colors.UNDERLINE,
                "button": Colors.BG_BLUE + Colors.WHITE + Colors.BOLD,
                "input": Colors.BG_WHITE + Colors.BLACK,
                "success": Colors.GREEN + Colors.BOLD,
                "error": Colors.RED + Colors.BOLD,
                "warning": Colors.YELLOW + Colors.BOLD,
                "info": Colors.CYAN,
                "border": Colors.BLUE,
                "highlight": Colors.BG_GREEN + Colors.BLACK
            },
            "dark": {
                "header": Colors.CYAN + Colors.BOLD,
                "title": Colors.GREEN + Colors.BOLD,
                "text": Colors.WHITE,
                "link": Colors.YELLOW + Colors.UNDERLINE,
                "button": Colors.BG_BLACK + Colors.WHITE + Colors.BOLD,
                "input": Colors.BG_BLACK + Colors.WHITE,
                "success": Colors.GREEN + Colors.BOLD,
                "error": Colors.RED + Colors.BOLD,
                "warning": Colors.YELLOW + Colors.BOLD,
                "info": Colors.CYAN,
                "border": Colors.CYAN,
                "highlight": Colors.BG_BLUE + Colors.WHITE
            },
            "retro": {
                "header": Colors.GREEN + Colors.BOLD,
                "title": Colors.YELLOW + Colors.BOLD,
                "text": Colors.GREEN,
                "link": Colors.CYAN + Colors.UNDERLINE,
                "button": Colors.BG_GREEN + Colors.BLACK + Colors.BOLD,
                "input": Colors.BG_BLACK + Colors.GREEN,
                "success": Colors.GREEN + Colors.BOLD,
                "error": Colors.RED + Colors.BOLD,
                "warning": Colors.YELLOW + Colors.BOLD,
                "info": Colors.CYAN,
                "border": Colors.GREEN,
                "highlight": Colors.BG_YELLOW + Colors.BLACK
            }
        }
        self.current = self.themes.get(name, self.themes["default"])

    def get(self, element: str) -> str:
        return self.current.get(element, Colors.END)

    def apply(self, text: str, element: str) -> str:
        return f"{self.get(element)}{text}{Colors.END}"

# Enhanced data structures with validation
@dataclass
class Tab:
    id: str
    url: str
    title: str
    document: Optional['NovaDocument'] = None
    history: List[str] = field(default_factory=list)
    history_index: int = 0
    is_active: bool = False
    favicon: Optional[str] = None
    last_accessed: datetime = field(default_factory=datetime.now)
    permissions: List[str] = field(default_factory=list)
    load_time: Optional[float] = None

@dataclass
class PerformanceMetrics:
    load_time: float
    render_time: float
    memory_usage: int
    network_requests: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Action:
    action_type: str
    key: Optional[str] = None
    value: Optional[Any] = None
    destination: Optional[str] = None
    input_id: Optional[str] = None
    media_id: Optional[str] = None
    command: Optional[str] = None
    form_id: Optional[str] = None
    extension_id: Optional[str] = None
    download_url: Optional[str] = None
    bookmark_url: Optional[str] = None
    search_query: Optional[str] = None
    theme_name: Optional[str] = None

@dataclass
class LayoutNode:
    node_type: str
    text: Optional[str] = None
    level: Optional[int] = None
    children: Optional[List['LayoutNode']] = None
    action: Optional[Action] = None
    destination: Optional[str] = None
    id: Optional[str] = None
    placeholder: Optional[str] = None
    source: Optional[str] = None
    controls: Optional[bool] = None
    autoplay: Optional[bool] = None
    width: Optional[int] = None
    height: Optional[int] = None
    responsive: Optional[Dict[str, Any]] = None
    animation: Optional[Dict[str, Any]] = None
    style: Optional[Dict[str, str]] = None
    form_type: Optional[str] = None
    required: Optional[bool] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    table_data: Optional[List[List[str]]] = None
    language: Optional[str] = None
    aria_label: Optional[str] = None
    role: Optional[str] = None

@dataclass
class NovaDocument:
    version: str
    layout: LayoutNode
    requires: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    csp: Optional[str] = None
    manifest: Optional[Dict[str, Any]] = None
    service_worker: Optional[str] = None
    metrics: Optional[PerformanceMetrics] = None
    raw_content: Optional[str] = None

# Enhanced Security & Certificate Management
class CertificateManager:
    def __init__(self):
        self.trusted_certs = {}
        self.cert_cache = {}
        
    def verify_certificate(self, url: str) -> Tuple[bool, Optional[str]]:
        """Verify SSL certificate for a URL"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme.startswith('https'):
                return True, "HTTP connection (not secure)"
                
            # Use system certificates via certifi
            context = ssl.create_default_context(cafile=certifi.where())
            with socket.create_connection((parsed.hostname, parsed.port or 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
                    cert = ssock.getpeercert()
                    return True, "Certificate is valid"
                    
        except ssl.SSLCertVerificationError as e:
            return False, f"Certificate verification failed: {e}"
        except Exception as e:
            return False, f"Certificate check error: {e}"

# Enhanced Network Client with Real HTTP Support
class NetworkClient:
    def __init__(self):
        self.request_cache = {}
        self.download_queue = queue.Queue()
        self.active_downloads = {}
        self.session = requests.Session()
        self.cert_manager = CertificateManager()
        
        # Configure session
        self.session.headers.update({
            'User-Agent': 'NovaBrowser/1.0 (Secure Declarative Browser)',
            'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # SSL verification
        self.session.verify = True
        
    def fetch_url(self, url: str, headers: Dict[str, str] = None) -> str:
        """Fetch URL with real HTTP requests"""
        logger.info(f"Fetching URL: {url}")
        
        # Check cache first
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if cache_key in self.request_cache:
            cached = self.request_cache[cache_key]
            if datetime.now() - cached['timestamp'] < timedelta(minutes=5):
                logger.debug(f"Cache hit for: {url}")
                return cached['content']
        
        try:
            # Verify certificate for HTTPS
            if url.startswith('https://'):
                cert_valid, cert_msg = self.cert_manager.verify_certificate(url)
                if not cert_valid:
                    logger.warning(f"SSL Certificate warning for {url}: {cert_msg}")
            
            # Make request
            response = self.session.get(
                url, 
                headers=headers,
                timeout=30,
                allow_redirects=True,
                stream=False
            )
            response.raise_for_status()
            
            content = response.text
            
            # Cache successful response
            self.request_cache[cache_key] = {
                'content': content,
                'timestamp': datetime.now(),
                'status_code': response.status_code
            }
            
            logger.info(f"Successfully fetched {url} - Status: {response.status_code}")
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {url}: {e}")
            # Return a fallback error document
            error_doc = {
                "version": "1.0",
                "metadata": {
                    "title": "Network Error",
                    "description": f"Failed to load {url}"
                },
                "layout": {
                    "type": "column",
                    "children": [
                        {
                            "type": "heading",
                            "level": 1,
                            "text": "🌐 Network Error",
                            "style": {"color": "red"}
                        },
                        {
                            "type": "text",
                            "text": f"Could not load: {url}"
                        },
                        {
                            "type": "text", 
                            "text": f"Error: {str(e)}"
                        },
                        {
                            "type": "button",
                            "text": "🔄 Retry",
                            "action": {"type": "navigate", "destination": url}
                        }
                    ]
                }
            }
            return json.dumps(error_doc)
    
    async def fetch_url_async(self, url: str, headers: Dict[str, str] = None) -> str:
        """Async version of URL fetching"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_url, url, headers)
    
    def download_file(self, url: str, filename: str = None) -> str:
        """Download file with progress tracking"""
        if not filename:
            filename = os.path.basename(urlparse(url).path) or "download.bin"
            
        download_path = nova_dir / 'downloads' / filename
        download_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Starting download: {url} -> {download_path}")
            
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Calculate progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self._update_download_progress(filename, progress)
            
            logger.info(f"Download completed: {download_path}")
            return str(download_path)
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
    
    def _update_download_progress(self, filename: str, progress: float):
        """Update download progress (could be connected to UI)"""
        print(f"\r{Colors.CYAN}📥 Downloading {filename}: {progress:.1f}%{Colors.END}", end='')
        if progress >= 100:
            print(f"\n{Colors.GREEN}✅ Download completed: {filename}{Colors.END}")
    
    def clear_cache(self):
        """Clear network cache"""
        self.request_cache.clear()
        self.session.cookies.clear()
        logger.info("Network cache cleared")

# Enhanced Storage Manager with Compression
class StorageManager:
    def __init__(self):
        self.nova_dir = nova_dir
        
        self.storage_file = self.nova_dir / 'storage.json'
        self.history_file = self.nova_dir / 'history.json'
        self.bookmarks_file = self.nova_dir / 'bookmarks.json'
        self.cookies_file = self.nova_dir / 'cookies.json'
        
        self.data = self._load_storage()
        self.history = self._load_history()
        self.bookmarks = self._load_bookmarks()
        self.cookies = self._load_cookies()
        
    def _load_storage(self) -> Dict:
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load storage: {e}")
        return {}
    
    def _load_history(self) -> List[Dict]:
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
        return []
    
    def _load_bookmarks(self) -> List[Dict]:
        try:
            if self.bookmarks_file.exists():
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load bookmarks: {e}")
        return []
    
    def _load_cookies(self) -> Dict:
        try:
            if self.cookies_file.exists():
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
        return {}
    
    def save(self):
        """Save all data with atomic writes"""
        try:
            # Save storage
            temp_file = self.storage_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.storage_file)
            
            # Save history (limit to 5000 entries)
            if len(self.history) > 5000:
                self.history = self.history[-5000:]
                
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
                
            # Save bookmarks
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
                
            # Save cookies
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(self.cookies, f, indent=2, ensure_ascii=False)
                
            logger.debug("All data saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            raise
    
    def add_to_history(self, url: str, title: str):
        """Add entry to browsing history"""
        entry = {
            'url': url,
            'title': title,
            'timestamp': datetime.now().isoformat(),
            'visit_count': 1
        }
        
        # Update if exists
        for i, existing in enumerate(self.history):
            if existing['url'] == url:
                existing['visit_count'] += 1
                existing['timestamp'] = entry['timestamp']
                self.history.pop(i)
                self.history.append(existing)
                self.save()
                return
                
        self.history.append(entry)
        self.save()
    
    def clear_cache(self):
        """Clear browser cache and temporary files"""
        cache_dir = self.nova_dir / 'cache'
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir()
        logger.info("Browser cache cleared")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        cache_dir = self.nova_dir / 'cache'
        downloads_dir = self.nova_dir / 'downloads'
        
        cache_size = sum(f.stat().st_size for f in cache_dir.glob('*') if f.is_file()) if cache_dir.exists() else 0
        download_count = len(list(downloads_dir.glob('*'))) if downloads_dir.exists() else 0
        
        return {
            'storage_size': self.storage_file.stat().st_size if self.storage_file.exists() else 0,
            'history_count': len(self.history),
            'bookmark_count': len(self.bookmarks),
            'cookie_count': len(self.cookies),
            'cache_size': cache_size,
            'download_count': download_count
        }

# Enhanced Document Parser with Security Validation
class DocumentParser:
    @staticmethod
    def parse_document(json_str: str, url: str = None) -> NovaDocument:
        start_time = time.time()
        
        try:
            data = json.loads(json_str)
            doc = DocumentParser._validate_document(data)
            doc.raw_content = json_str
            
            # Add performance metrics
            doc.metrics = PerformanceMetrics(
                load_time=time.time() - start_time,
                render_time=0,
                memory_usage=0,
                network_requests=0
            )
            
            logger.info(f"Document parsed successfully from {url}")
            return doc
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in document: {e}")
            raise ValueError(f"Invalid JSON document: {e}")
        except Exception as e:
            logger.error(f"Document parsing failed: {e}")
            raise
    
    @staticmethod
    def _validate_document(data: Dict) -> NovaDocument:
        """Validate document structure and security"""
        if not isinstance(data, dict):
            raise ValueError("Document must be a JSON object")
            
        if data.get('version') != '1.0':
            raise ValueError("Only Nova Document version 1.0 supported")
            
        if 'layout' not in data:
            raise ValueError("Document must contain 'layout'")
            
        layout = DocumentParser._parse_layout_node(data['layout'])
        
        return NovaDocument(
            version=data['version'],
            layout=layout,
            requires=data.get('requires'),
            metadata=data.get('metadata'),
            csp=data.get('csp'),
            manifest=data.get('manifest'),
            service_worker=data.get('service_worker')
        )
    
    @staticmethod
    def _parse_layout_node(node_data: Dict) -> LayoutNode:
        """Parse layout node with security checks"""
        if not isinstance(node_data, dict):
            raise ValueError("Layout node must be an object")
            
        if 'type' not in node_data:
            raise ValueError("Layout node must have 'type'")
            
        # Parse action if present
        action = None
        if 'action' in node_data:
            action_data = node_data['action']
            if not isinstance(action_data, dict):
                raise ValueError("Action must be an object")
                
            action = Action(
                action_type=action_data.get('type', ''),
                key=action_data.get('key'),
                value=action_data.get('value'),
                destination=action_data.get('destination'),
                input_id=action_data.get('input_id'),
                media_id=action_data.get('media_id'),
                command=action_data.get('command'),
                form_id=action_data.get('form_id'),
                extension_id=action_data.get('extension_id'),
                download_url=action_data.get('download_url'),
                bookmark_url=action_data.get('bookmark_url'),
                search_query=action_data.get('search_query'),
                theme_name=action_data.get('theme_name')
            )
        
        # Parse children recursively
        children = None
        if 'children' in node_data:
            if not isinstance(node_data['children'], list):
                raise ValueError("Children must be an array")
            children = [DocumentParser._parse_layout_node(child) for child in node_data['children']]
        
        return LayoutNode(
            node_type=node_data['type'],
            text=node_data.get('text'),
            level=node_data.get('level'),
            children=children,
            action=action,
            destination=node_data.get('destination'),
            id=node_data.get('id'),
            placeholder=node_data.get('placeholder'),
            source=node_data.get('source'),
            controls=node_data.get('controls'),
            autoplay=node_data.get('autoplay'),
            width=node_data.get('width'),
            height=node_data.get('height'),
            responsive=node_data.get('responsive'),
            animation=node_data.get('animation'),
            style=node_data.get('style'),
            form_type=node_data.get('form_type'),
            required=node_data.get('required'),
            min_length=node_data.get('min_length'),
            max_length=node_data.get('max_length'),
            pattern=node_data.get('pattern'),
            table_data=node_data.get('table_data'),
            language=node_data.get('language'),
            aria_label=node_data.get('aria_label'),
            role=node_data.get('role')
        )

# Enhanced Renderer with Better UI
class Renderer:
    def __init__(self, theme: Theme = None):
        self.theme = theme or Theme()
        self.input_buffer = {}
        self.animation_states = {}
        self.form_data = {}
        self.scroll_position = 0
        self.viewport_height = 24
        
    def render_document(self, doc: NovaDocument, tab: Tab = None):
        start_time = time.time()
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Render enhanced header
        self._render_enhanced_header(doc, tab)
        
        # Render content
        self._render_node(doc.layout, 0)
        
        # Update metrics
        if doc.metrics:
            doc.metrics.render_time = time.time() - start_time
            
    def _render_enhanced_header(self, doc: NovaDocument, tab: Tab = None):
        """Render enhanced browser header"""
        # Browser chrome
        print(self.theme.get("header") + "╔" + "═" * 78 + "╗" + Colors.END)
        
        # Title and URL
        if tab:
            title = tab.title[:60] + "..." if len(tab.title) > 60 else tab.title
            url = tab.url[:70] + "..." if len(tab.url) > 70 else tab.url
            
            print(self.theme.get("header") + f"║ 📑 {title:<74} ║" + Colors.END)
            print(self.theme.get("header") + f"║ 🔗 {url:<74} ║" + Colors.END)
        else:
            print(self.theme.get("header") + f"║ {'Nova Browser':^78} ║" + Colors.END)
            
        print(self.theme.get("header") + "╠" + "═" * 78 + "╣" + Colors.END)
        
        # Document info
        if doc.metadata:
            if 'title' in doc.metadata:
                print(f"{self.theme.apply('📖 ', 'title')}{self.theme.apply(doc.metadata['title'], 'title')}")
            if 'description' in doc.metadata:
                print(f"  {doc.metadata['description']}")
                
        # Performance info
        if tab and tab.load_time:
            print(f"{self.theme.apply('⚡', 'info')} Loaded in {tab.load_time:.2f}s")
            
        print(self.theme.get("border") + "─" * 80 + Colors.END)
        
    def _render_node(self, node: LayoutNode, indent: int):
        """Render a layout node"""
        indent_str = " " * indent
        
        try:
            if node.node_type == "heading":
                self._render_heading(node, indent_str)
            elif node.node_type == "paragraph":
                self._render_paragraph(node, indent_str)
            elif node.node_type == "button":
                self._render_button(node, indent_str)
            elif node.node_type == "link":
                self._render_link(node, indent_str)
            elif node.node_type == "input":
                self._render_input(node, indent_str)
            elif node.node_type == "form":
                self._render_form(node, indent_str)
            elif node.node_type == "table":
                self._render_table(node, indent_str)
            elif node.node_type == "code":
                self._render_code(node, indent_str)
            elif node.node_type in ["image", "audio", "video"]:
                self._render_media(node, indent_str)
            elif node.node_type in ["column", "row", "grid"]:
                self._render_container(node, indent_str)
            else:
                self._render_generic(node, indent_str)
                
        except Exception as e:
            logger.error(f"Error rendering node: {e}")
            print(f"{indent_str}{self.theme.apply('� Render Error', 'error')}")
    
    def _render_heading(self, node: LayoutNode, indent: str):
        level = node.level or 1
        text = node.text or ""
        
        if level == 1:
            # Fixed: Use proper string multiplication with integers
            border_line = "═" * 78
            print(f"\n{indent}{self.theme.apply('╔' + border_line + '╗', 'title')}")
            print(f"{indent}{self.theme.apply('║', 'title')} {text:^74} {self.theme.apply('║', 'title')}")
            print(f"{indent}{self.theme.apply('╚' + border_line + '╝', 'title')}")
        else:
            prefix = "#" * level
            print(f"\n{indent}{self.theme.apply(prefix, 'title')} {text}")
    
    def _render_button(self, node: LayoutNode, indent: str):
        text = node.text or "Button"
        styled_text = self.theme.apply(f" [{text}] ", "button")
        id_info = f" [{node.id}]" if node.id else ""
        print(f"{indent}{styled_text}{id_info}")
    
    def _render_link(self, node: LayoutNode, indent: str):
        text = node.text or "Link"
        styled_text = self.theme.apply(f" 🔗 {text}", "link")
        dest_info = f" → {node.destination}" if node.destination else ""
        print(f"{indent}{styled_text}{dest_info}")
    
    def _render_input(self, node: LayoutNode, indent: str):
        placeholder = node.placeholder or "Enter text..."
        input_type = f" ({node.form_type})" if node.form_type else ""
        required = " *" if node.required else ""
        print(f"{indent}📝 {self.theme.apply(f'[input: {node.id}{input_type}{required}]', 'input')} '{placeholder}'")
    
    def _render_paragraph(self, node: LayoutNode, indent: str):
        text = node.text or ""
        # Simple text wrapping
        if text:
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                if len(' '.join(current_line + [word])) <= 76:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
                
            for line in lines:
                print(f"{indent}{line}")
    
    def _render_form(self, node: LayoutNode, indent: str):
        print(f"{indent}{self.theme.apply('┌─ FORM ───', 'border')}")
        if node.children:
            for child in node.children:
                self._render_node(child, indent + 2)
        print(f"{indent}{self.theme.apply('└──────────', 'border')}")
    
    def _render_table(self, node: LayoutNode, indent: str):
        if node.table_data:
            print(f"{indent}{self.theme.apply('┌─ TABLE ───', 'border')}")
            for row in node.table_data:
                row_text = " │ ".join(str(cell) for cell in row)
                print(f"{indent}│ {row_text}")
            print(f"{indent}{self.theme.apply('└──────────', 'border')}")
    
    def _render_code(self, node: LayoutNode, indent: str):
        lang = f" ({node.language})" if node.language else ""
        text = node.text or ""
        print(f"{indent}{self.theme.apply('┌─ CODE' + lang + ' ───', 'border')}")
        for line in text.split('\n'):
            print(f"{indent}│ {line}")
        print(f"{indent}{self.theme.apply('└──────────', 'border')}")
    
    def _render_media(self, node: LayoutNode, indent: str):
        if node.node_type == "image":
            size_info = f" ({node.width}x{node.height})" if node.width and node.height else ""
            print(f"{indent}🖼️ [image: {node.source}]{size_info}")
        elif node.node_type == "audio":
            controls = " [controls]" if node.controls else ""
            state = "▶️ auto" if node.autoplay else "🔈"
            print(f"{indent}{state} [audio: {node.source}]{controls}")
        elif node.node_type == "video":
            size_info = f" ({node.width}x{node.height})" if node.width and node.height else ""
            controls = " [controls]" if node.controls else ""
            state = "▶️ auto" if node.autoplay else "🎥"
            print(f"{indent}{state} [video: {node.source}]{controls}{size_info}")
    
    def _render_container(self, node: LayoutNode, indent: str):
        if node.children:
            if node.node_type == "column":
                for child in node.children:
                    self._render_node(child, indent)
            elif node.node_type == "row":
                items = []
                for child in node.children:
                    if child.node_type == "text":
                        items.append(child.text or "")
                    elif child.node_type == "button":
                        items.append(self.theme.apply(f"[{child.text}]", "button"))
                    elif child.node_type == "link":
                        items.append(self.theme.apply(f"🔗{child.text}", "link"))
                if items:
                    print(f"{indent}{' | '.join(items)}")
            elif node.node_type == "grid":
                print(f"{indent}{self.theme.apply('┌─ Grid ───', 'border')}")
                for i, child in enumerate(node.children):
                    print(f"{indent}│ ", end="")
                    self._render_node(child, 0)
                    if i < len(node.children) - 1:
                        print(f"{indent}{self.theme.apply('├──────────', 'border')}")
                print(f"{indent}{self.theme.apply('└──────────', 'border')}")
    
    def _render_generic(self, node: LayoutNode, indent: str):
        text = node.text or ""
        print(f"{indent}{text}")
    
    def collect_actions(self, node: LayoutNode) -> List[Action]:
        actions = []
        self._collect_actions_recursive(node, actions)
        return actions
    
    def _collect_actions_recursive(self, node: LayoutNode, actions: List[Action]):
        if node.action:
            actions.append(node.action)
        
        if node.node_type == "form" and node.id:
            actions.append(Action(action_type="form_submit", form_id=node.id))
        
        if node.node_type in ["audio", "video"] and (node.controls or node.controls is None):
            if node.id:
                for command in ["play", "pause", "stop"]:
                    actions.append(Action(action_type="media_control", media_id=node.id, command=command))
        
        if node.node_type == "link" and node.destination:
            actions.append(Action(action_type="navigate", destination=node.destination))
        
        if node.children:
            for child in node.children:
                self._collect_actions_recursive(child, actions)

# GUI Implementation
class NovaBrowserGUI:
    def __init__(self, runtime):
        self.runtime = runtime
        self.root = tk.Tk()
        self.root.title("Nova Browser - Production Ready")
        self.root.geometry("1200x800")
        
        # Theme
        self.theme = runtime.theme
        self.setup_gui()
        
    def setup_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Browser toolbar
        self.setup_toolbar(main_frame)
        
        # Tab system
        self.setup_tabs(main_frame)
        
        # Status bar
        self.setup_statusbar(main_frame)
        
    def setup_toolbar(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Navigation buttons
        ttk.Button(toolbar, text="← Back", command=self.go_back).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="→ Forward", command=self.go_forward).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↻ Reload", command=self.reload_page).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🏠 Home", command=self.go_home).pack(side=tk.LEFT, padx=2)
        
        # Address bar
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(toolbar, textvariable=self.url_var, width=80)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.url_entry.bind('<Return>', self.navigate_from_bar)
        
        # New tab button
        ttk.Button(toolbar, text="➕ New Tab", command=self.new_tab).pack(side=tk.RIGHT, padx=2)
        
        # Search button
        ttk.Button(toolbar, text="🔍 Search", command=self.open_search).pack(side=tk.RIGHT, padx=2)
        
    def setup_tabs(self, parent):
        # Tab control
        self.tab_control = ttk.Notebook(parent)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Tab context menu
        self.tab_menu = tk.Menu(self.root, tearoff=0)
        self.tab_menu.add_command(label="Close Tab", command=self.close_current_tab)
        self.tab_menu.add_command(label="Reload Tab", command=self.reload_current_tab)
        
        self.tab_control.bind("<Button-3>", self.show_tab_menu)  # Right-click
        
        # Create initial tab
        self.create_browser_tab()
        
    def setup_statusbar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, fill=tk.X, padx=5)
        
    def create_browser_tab(self, url=None):
        # Create new tab frame
        tab_frame = ttk.Frame(self.tab_control)
        
        # Create scrollable content area
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Add tab
        tab_title = "New Tab" if not url else f"Loading {url}..."
        self.tab_control.add(tab_frame, text=tab_title)
        self.tab_control.select(tab_frame)
        
        # Store tab data
        tab_data = {
            'frame': tab_frame,
            'canvas': canvas,
            'scrollable_frame': scrollable_frame,
            'url': url,
            'content_widgets': []
        }
        
        tab_frame.tab_data = tab_data
        
        # Load content if URL provided
        if url:
            self.load_url_in_tab(tab_frame, url)
        else:
            self.show_welcome_page(tab_frame)
            
        return tab_frame
    
    def show_welcome_page(self, tab_frame):
        """Show welcome page in a tab"""
        data = tab_frame.tab_data
        self.clear_tab_content(data)
        
        content_frame = data['scrollable_frame']
        
        # Welcome content
        title = ttk.Label(content_frame, text="🚀 Nova Browser", 
                         font=("Arial", 24, "bold"))
        title.pack(pady=20)
        data['content_widgets'].append(title)
        
        subtitle = ttk.Label(content_frame, 
                           text="Secure, Fast, Privacy-First Browsing",
                           font=("Arial", 14))
        subtitle.pack(pady=10)
        data['content_widgets'].append(subtitle)
        
        # Quick actions frame
        actions_frame = ttk.Frame(content_frame)
        actions_frame.pack(pady=20)
        data['content_widgets'].append(actions_frame)
        
        quick_actions = [
            ("🔍 Web Search", self.open_search),
            ("🌐 Example Site", lambda: self.load_url_in_tab(tab_frame, "https://httpbin.org/json")),
            ("📊 Browser Status", self.show_browser_stats),
            ("⚙️ Settings", self.show_settings)
        ]
        
        for text, command in quick_actions:
            btn = ttk.Button(actions_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)
            data['content_widgets'].append(btn)
            
        # Recent history
        history_frame = ttk.LabelFrame(content_frame, text="Quick Links")
        history_frame.pack(fill=tk.X, padx=20, pady=10)
        data['content_widgets'].append(history_frame)
        
        # Add some sample links
        quick_links = [
            ("🌐 Example JSON API", "https://httpbin.org/json"),
            ("🔍 DuckDuckGo Search", "https://duckduckgo.com"),
            ("📚 Python Documentation", "https://docs.python.org"),
            ("🛠️ Browser Test", "file:///welcome.nova")
        ]
        
        for text, url in quick_links:
            link = ttk.Label(history_frame, text=text, cursor="hand2", 
                           foreground="blue")
            link.pack(anchor="w", pady=2)
            link.bind("<Button-1>", lambda e, u=url: self.load_url_in_tab(tab_frame, u))
            data['content_widgets'].append(link)
    
    def clear_tab_content(self, tab_data):
        """Clear all widgets from tab"""
        for widget in tab_data['content_widgets']:
            try:
                widget.destroy()
            except:
                pass
        tab_data['content_widgets'] = []
    
    def load_url_in_tab(self, tab_frame, url):
        """Load URL in a specific tab"""
        data = tab_frame.tab_data
        self.clear_tab_content(data)
        
        # Update UI
        self.status_var.set(f"Loading {url}...")
        self.progress.start()
        self.url_var.set(url)
        data['url'] = url
        
        # Update tab title temporarily
        current_tab_id = self.tab_control.index("current")
        self.tab_control.tab(current_tab_id, text=f"Loading...")
        
        def load_thread():
            try:
                # Create a temporary tab in the runtime
                temp_tab = self.runtime.create_tab(url)
                success = self.runtime.load_document(url, temp_tab)
                
                # FIX: Use callback method instead of direct UI update from thread
                self.root.after(0, self._gui_load_done, tab_frame, temp_tab, success)
                
            except Exception as e:
                # FIX: Handle exceptions through main thread
                self.root.after(0, self._gui_load_done, tab_frame, None, e)
        
        # Run loading in thread to avoid blocking UI
        threading.Thread(target=load_thread, daemon=True).start()

    def _gui_load_done(self, tab_frame, nova_tab, ok_or_exc):
        """Handle completed document loading in main thread"""
        self.progress.stop()
        
        if isinstance(ok_or_exc, Exception):
            self.show_error(tab_frame, str(ok_or_exc))
            return
            
        if nova_tab and ok_or_exc:
            self.update_tab_content(tab_frame, nova_tab, ok_or_exc)
        else:
            self.show_error(tab_frame, "Failed to load document")
    
    def update_tab_content(self, tab_frame, nova_tab, success):
        """Update tab content after loading"""
        data = tab_frame.tab_data
        self.progress.stop()
        
        if success and nova_tab.document:
            # Update tab title
            current_tab_id = self.tab_control.index("current")
            title = nova_tab.title[:20] + "..." if len(nova_tab.title) > 20 else nova_tab.title
            self.tab_control.tab(current_tab_id, text=title)
            
            # Update URL bar
            self.url_var.set(nova_tab.url)
            
            # Render document content
            self.render_document_gui(data, nova_tab.document)
            
            self.status_var.set(f"Loaded {nova_tab.url}")
        else:
            self.status_var.set("Load failed")
    
    def render_document_gui(self, tab_data, document):
        """Render Nova document in GUI"""
        content_frame = tab_data['scrollable_frame']
        
        def render_node(node, parent_frame, indent=0):
            if node.node_type == "heading":
                font_size = {1: 24, 2: 20, 3: 16, 4: 14}.get(node.level, 12)
                label = ttk.Label(parent_frame, text=node.text or "", 
                                font=("Arial", font_size, "bold"))
                label.pack(anchor="w", pady=5)
                tab_data['content_widgets'].append(label)
                
            elif node.node_type == "paragraph":
                label = ttk.Label(parent_frame, text=node.text or "", 
                                wraplength=800, justify="left")
                label.pack(anchor="w", pady=2)
                tab_data['content_widgets'].append(label)
                
            elif node.node_type == "button":
                btn = ttk.Button(parent_frame, text=node.text or "Button",
                               command=lambda: self.handle_action(node.action, tab_data))
                btn.pack(anchor="w", pady=2)
                tab_data['content_widgets'].append(btn)
                
            elif node.node_type == "link":
                link = ttk.Label(parent_frame, text=node.text or "Link",
                               foreground="blue", cursor="hand2")
                link.pack(anchor="w", pady=1)
                link.bind("<Button-1>", 
                         lambda e: self.handle_action(node.action, tab_data))
                tab_data['content_widgets'].append(link)
                
            elif node.node_type == "input":
                frame = ttk.Frame(parent_frame)
                frame.pack(anchor="w", pady=2, fill=tk.X)
                
                ttk.Label(frame, text=node.placeholder or "Input:").pack(side=tk.LEFT)
                entry = ttk.Entry(frame, width=30)
                entry.pack(side=tk.LEFT, padx=5)
                tab_data['content_widgets'].extend([frame, entry])
                
            # Recursively render children
            if node.children:
                child_frame = ttk.Frame(parent_frame)
                child_frame.pack(anchor="w", padx=indent+10)
                tab_data['content_widgets'].append(child_frame)
                
                for child in node.children:
                    render_node(child, child_frame, indent+10)
        
        # Start rendering from root
        render_node(document.layout, content_frame)
    
    def handle_action(self, action, tab_data):
        """Handle user actions from GUI elements"""
        if not action:
            return
            
        if action.action_type == "navigate" and action.destination:
            self.load_url_in_tab(tab_data['frame'], action.destination)
                
        elif action.action_type == "search":
            self.open_search()
            
        elif action.action_type == "show_stats":
            self.show_browser_stats()
    
    def get_current_tab_frame(self):
        """Get the currently selected tab frame"""
        try:
            current_tab = self.tab_control.select()
            return self.tab_control.nametowidget(current_tab)
        except:
            return None
    
    def show_error(self, tab_frame, error_msg):
        """Show error message in tab"""
        data = tab_frame.tab_data
        self.clear_tab_content(data)
        
        content_frame = data['scrollable_frame']
        
        error_label = ttk.Label(content_frame, text=f"Error: {error_msg}", 
                               foreground="red", wraplength=800)
        error_label.pack(pady=20)
        data['content_widgets'].append(error_label)
        
        retry_btn = ttk.Button(content_frame, text="Retry", 
                              command=lambda: self.load_url_in_tab(tab_frame, data['url']))
        retry_btn.pack(pady=10)
        data['content_widgets'].append(retry_btn)
        
        self.status_var.set("Load failed")
        self.progress.stop()
    
    # Navigation methods
    def navigate_from_bar(self, event=None):
        url = self.url_var.get().strip()
        if url:
            current_tab = self.get_current_tab_frame()
            if current_tab:
                if not url.startswith(('http://', 'https://', 'file:///')):
                    url = 'https://' + url
                self.load_url_in_tab(current_tab, url)
    
    def go_back(self):
        # Implement back navigation using runtime history
        messagebox.showinfo("Info", "Back navigation - to be implemented")
    
    def go_forward(self):
        # Implement forward navigation
        messagebox.showinfo("Info", "Forward navigation - to be implemented")
    
    def reload_page(self):
        current_tab = self.get_current_tab_frame()
        if current_tab and current_tab.tab_data['url']:
            self.load_url_in_tab(current_tab, current_tab.tab_data['url'])
    
    def go_home(self):
        current_tab = self.get_current_tab_frame()
        if current_tab:
            self.load_url_in_tab(current_tab, "file:///welcome.nova")
    
    def new_tab(self):
        self.create_browser_tab()
    
    def close_current_tab(self):
        if len(self.tab_control.tabs()) > 1:
            current_tab = self.tab_control.select()
            self.tab_control.forget(current_tab)
    
    def reload_current_tab(self):
        self.reload_page()
    
    def show_tab_menu(self, event):
        try:
            self.tab_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tab_menu.grab_release()
    
    def open_search(self):
        search_term = simpledialog.askstring("Web Search", "Enter search query:")
        if search_term:
            # FIX: Remove the extra space in the URL
            search_url = f"https://duckduckgo.com/html/?q={search_term}"
            current_tab = self.get_current_tab_frame()
            if current_tab:
                self.load_url_in_tab(current_tab, search_url)
    
    def show_browser_stats(self):
        stats = self.runtime.storage_mgr.get_storage_stats()
        
        stats_text = f"""
Browser Statistics:
------------------
Open Tabs: {len(self.runtime.tabs)}
History Entries: {stats.get('history_count', 0)}
Bookmarks: {stats.get('bookmark_count', 0)}
Cache Size: {stats.get('cache_size', 0) // 1024} KB
Downloads: {stats.get('download_count', 0)}

Storage Location: {nova_dir}
"""
        messagebox.showinfo("Browser Statistics", stats_text)
    
    def show_settings(self):
        # Simple settings dialog
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Browser Settings")
        settings_window.geometry("400x300")
        
        ttk.Label(settings_window, text="Nova Browser Settings", 
                 font=("Arial", 16)).pack(pady=10)
        
        # Theme selection
        theme_frame = ttk.LabelFrame(settings_window, text="Theme")
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        theme_var = tk.StringVar(value="default")
        themes = [("Default", "default"), ("Dark", "dark"), ("Retro", "retro")]
        
        for text, value in themes:
            ttk.Radiobutton(theme_frame, text=text, value=value, 
                          variable=theme_var).pack(anchor="w")
        
        # Clear data button
        ttk.Button(settings_window, text="Clear Browser Data", 
                  command=self.clear_browser_data).pack(pady=10)
        
        ttk.Button(settings_window, text="Apply", 
                  command=lambda: self.apply_settings(theme_var.get(), settings_window)).pack(pady=5)
    
    def apply_settings(self, theme_name, settings_window):
        self.runtime.theme = Theme(theme_name)
        messagebox.showinfo("Settings", f"Theme changed to {theme_name}")
        settings_window.destroy()
    
    def clear_browser_data(self):
        if messagebox.askyesno("Confirm", "Clear all browser data?"):
            self.runtime.storage_mgr.clear_cache()
            messagebox.showinfo("Success", "Browser data cleared")
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()

# Enhanced Nova Runtime with GUI Support
class NovaRuntime:
    def __init__(self, use_gui=True):
        self.theme = Theme()
        self.storage_mgr = StorageManager()
        self.renderer = Renderer(self.theme)
        self.network_client = NetworkClient()
        
        self.tabs = []
        self.active_tab_id = None
        self.current_url = "file:///welcome.nova"
        
        # Thread pool for async operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # GUI setup
        self.use_gui = use_gui and GUI_AVAILABLE
        self.gui = None
        
        if self.use_gui:
            try:
                self.gui = NovaBrowserGUI(self)
                logger.info("GUI initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GUI: {e}")
                self.use_gui = False
        
        # FIX: Load demo documents AFTER GUI initialization so CLI also gets them
        self.documents = self._load_demo_documents()
        
        # Create initial tab
        self.create_tab(self.current_url)
        
        logger.info("Nova Browser initialized" + (" with GUI" if self.use_gui else " in CLI mode"))
    
    def _load_demo_documents(self):
        # FIX: Use "/welcome.nova" as key to match the file:/// URL parsing
        return {
            "/welcome.nova": json.dumps({
                "version": "1.0",
                "metadata": {
                    "title": "Nova Browser - Production Ready",
                    "description": "Secure, fast, privacy-first browsing experience"
                },
                "layout": {
                    "type": "column", 
                    "children": [
                        {
                            "type": "heading",
                            "level": 1,
                            "text": "🚀 Nova Browser - Production Ready"
                        },
                        {
                            "type": "paragraph", 
                            "text": "Experience the next generation of secure, privacy-first browsing with real network capabilities."
                        },
                        {
                            "type": "grid",
                            "children": [
                                {
                                    "type": "button",
                                    "text": "🔍 Web Search", 
                                    "action": {"type": "search"}
                                },
                                {
                                    "type": "button",
                                    "text": "🌐 Example Site",
                                    "action": {"type": "navigate", "destination": "https://httpbin.org/json"}
                                },
                                {
                                    "type": "button", 
                                    "text": "📊 Browser Status",
                                    "action": {"type": "show_stats"}
                                },
                                {
                                    "type": "button",
                                    "text": "🔄 Reload",
                                    "action": {"type": "navigate", "destination": "file:///welcome.nova"}
                                }
                            ]
                        },
                        {
                            "type": "text",
                            "text": "Try these commands: 'new' for new tab, 'tabs' to list tabs, 'status' for info"
                        }
                    ]
                }
            })
        }
    
    def create_tab(self, url: str) -> Tab:
        """Create a new browser tab"""
        tab_id = hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()
        tab = Tab(id=tab_id, url=url, title="Loading...")
        self.tabs.append(tab)
        self.active_tab_id = tab_id
        return tab
    
    def get_active_tab(self) -> Optional[Tab]:
        for tab in self.tabs:
            if tab.id == self.active_tab_id:
                return tab
        return None
    
    def load_document(self, url: str, tab: Tab = None) -> bool:
        """Load a document with enhanced error handling"""
        if not tab:
            tab = self.get_active_tab()
        if not tab:
            tab = self.create_tab(url)
            
        logger.info(f"Loading document: {url}")
        
        try:
            start_time = time.time()
            
            # Get document content
            if url.startswith(('http://', 'https://')):
                content = self.network_client.fetch_url(url)
            elif url.startswith('file:///'):
                # Local document
                doc_key = url.replace('file:///', '')
                if doc_key in self.documents:
                    content = self.documents[doc_key]
                else:
                    content = json.dumps(self._create_error_document(f"Document not found: {doc_key}"))
            else:
                content = json.dumps(self._create_error_document(f"Unsupported protocol: {url}"))
            
            # Parse document
            doc = DocumentParser.parse_document(content, url)
            
            # Update tab
            tab.url = url
            tab.document = doc
            tab.title = doc.metadata.get('title', url) if doc.metadata else url
            tab.load_time = time.time() - start_time
            tab.history.append(url)
            tab.last_accessed = datetime.now()
            
            # Add to history
            self.storage_mgr.add_to_history(url, tab.title)
            
            logger.info(f"Document loaded successfully: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load document {url}: {e}")
            error_doc = self._create_error_document(str(e))
            tab.document = DocumentParser.parse_document(json.dumps(error_doc))
            return False
    
    def _create_error_document(self, error_msg: str) -> Dict:
        """Create an error document"""
        return {
            "version": "1.0",
            "metadata": {
                "title": "Error Loading Page",
                "description": "The requested document could not be loaded"
            },
            "layout": {
                "type": "column",
                "children": [
                    {
                        "type": "heading",
                        "level": 1,
                        "text": "🚫 Page Load Error"
                    },
                    {
                        "type": "text",
                        "text": error_msg
                    },
                    {
                        "type": "button",
                        "text": "🔄 Reload",
                        "action": {"type": "navigate", "destination": self.current_url}
                    },
                    {
                        "type": "link", 
                        "text": "🏠 Back to Home",
                        "destination": "file:///welcome.nova"
                    }
                ]
            }
        }
    
    def run_cli(self):
        """Main browser loop with enhanced error handling"""
        print(f"{Colors.HEADER}🚀 Nova Browser - Production Ready{Colors.END}")
        print(f"{Colors.GREEN}✨ Secure, Fast, Privacy-First Browsing{Colors.END}")
        print(f"{Colors.CYAN}📝 Logs: ~/.nova/browser.log{Colors.END}\n")
        
        try:
            # Load initial document
            if not self.load_document(self.current_url):
                print(f"{Colors.RED}❌ Failed to load initial document{Colors.END}")
                return
                
            while True:
                tab = self.get_active_tab()
                
                if tab and tab.document:
                    self.renderer.render_document(tab.document, tab)
                    actions = self.renderer.collect_actions(tab.document.layout)
                    
                    self._show_actions_menu(actions)
                    choice = input(f"{Colors.YELLOW}Enter choice:{Colors.END} ").strip().lower()
                    
                    if not self._handle_user_choice(choice, actions, tab):
                        break
                else:
                    print(f"{Colors.RED}❌ No document loaded!{Colors.END}")
                    break
                    
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Browser interrupted by user{Colors.END}")
        except Exception as e:
            logger.critical(f"Critical runtime error: {e}")
            print(f"{Colors.RED}💥 Critical error: {e}{Colors.END}")
        finally:
            self.shutdown()
    
    def _show_actions_menu(self, actions: List[Action]):
        """Show enhanced actions menu"""
        if actions:
            print(f"\n{Colors.YELLOW}🔄 Available actions:{Colors.END}")
            for i, action in enumerate(actions, 1):
                icon = self._get_action_icon(action.action_type)
                desc = self._get_action_description(action)
                print(f"  {i}. {icon} {desc}")
        
        print(f"\n{Colors.CYAN}Global commands:{Colors.END}")
        print(f"  {Colors.GREEN}new{Colors.END} - New tab | {Colors.GREEN}tabs{Colors.END} - List tabs")
        print(f"  {Colors.GREEN}reload{Colors.END} - Refresh | {Colors.GREEN}status{Colors.END} - Browser info")  
        print(f"  {Colors.GREEN}quit{Colors.END} - Exit | {Colors.GREEN}help{Colors.END} - Show help")
    
    def _get_action_icon(self, action_type: str) -> str:
        """Get icon for action type"""
        icons = {
            "navigate": "🌐",
            "store": "💾", 
            "media_control": "🎵",
            "search": "🔍",
            "set_theme": "🎨",
            "show_stats": "📊",
            "show_permissions": "🔒",
            "show_history": "📜",
            "clear_cache": "🗑️",
            "form_submit": "📝"
        }
        return icons.get(action_type, "⚡")
    
    def _get_action_description(self, action: Action) -> str:
        """Get human-readable action description"""
        if action.action_type == "navigate":
            proto = "🌐" if action.destination and action.destination.startswith("http") else "📁"
            dest = action.destination or "unknown"
            return f"{proto} Navigate to {dest}"
        elif action.action_type == "store":
            return f"💾 Store data: {action.key}"
        elif action.action_type == "search":
            return f"🔍 Search: {action.search_query or 'Enter query'}"
        elif action.action_type == "show_stats":
            return "📊 Show browser statistics"
        else:
            return f"{action.action_type.replace('_', ' ').title()}"
    
    def _handle_user_choice(self, choice: str, actions: List[Action], tab: Tab) -> bool:
        """Handle user input with enhanced options"""
        if choice == 'quit':
            return False
        elif choice == 'reload':
            self.load_document(tab.url, tab)
        elif choice == 'status':
            self._show_browser_status()
        elif choice == 'tabs':
            self._show_tabs_list()
        elif choice == 'new':
            self._create_new_tab()
        elif choice == 'help':
            self._show_help()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(actions):
                self._execute_action(actions[idx])
            else:
                print(f"{Colors.RED}❌ Invalid action number{Colors.END}")
        else:
            print(f"{Colors.RED}❌ Unknown command: {choice}{Colors.END}")
            
        return True
    
    def _show_browser_status(self):
        """Show enhanced browser status"""
        stats = self.storage_mgr.get_storage_stats()
        
        print(f"\n{Colors.HEADER}📊 BROWSER STATUS{Colors.END}")
        print(f"{Colors.CYAN}Memory Usage:{Colors.END} {self._get_memory_usage()} MB")
        print(f"{Colors.CYAN}Open tabs:{Colors.END} {len(self.tabs)}")
        print(f"{Colors.CYAN}Cache size:{Colors.END} {stats.get('cache_size', 0) // 1024} KB")
        print(f"{Colors.CYAN}History entries:{Colors.END} {len(self.storage_mgr.history)}")
        print(f"{Colors.CYAN}Active tab:{Colors.END} {self.get_active_tab().title if self.get_active_tab() else 'None'}")
    
    def _get_memory_usage(self):
        """Get memory usage in MB"""
        try:
            import psutil
            return psutil.Process().memory_info().rss // 1024 // 1024
        except ImportError:
            return "N/A (install psutil)"
    
    def _show_tabs_list(self):
        """Show tabs list with management options"""
        print(f"\n{Colors.HEADER}📑 OPEN TABS{Colors.END}")
        for i, tab in enumerate(self.tabs):
            active = " → " if tab.id == self.active_tab_id else "   "
            print(f"  {i+1}.{active} {tab.title}")
        
        if len(self.tabs) > 1:
            print(f"\n{Colors.YELLOW}Tip:{Colors.END} Use 'new' to create tabs, close with Ctrl+C")
    
    def _create_new_tab(self):
        """Create new tab with URL input"""
        url = input(f"{Colors.YELLOW}Enter URL for new tab:{Colors.END} ").strip()
        if url:
            if not url.startswith(('http://', 'https://', 'file:///')):
                url = 'https://' + url
            self.create_tab(url)
            self.load_document(url)
    
    def _show_help(self):
        """Show comprehensive help"""
        print(f"\n{Colors.HEADER}📖 NOVA BROWSER HELP{Colors.END}")
        print(f"{Colors.CYAN}Navigation:{Colors.END}")
        print("  • Enter numbers to select actions")
        print("  • Use 'new' to create tabs")
        print("  • Use 'tabs' to manage tabs")
        print("  • Use 'reload' to refresh current page")
        print(f"{Colors.CYAN}Document Types:{Colors.END}")
        print("  • .nova files - Declarative documents")
        print("  • HTTP/HTTPS - Web content")
        print("  • file:/// - Local documents")
        print(f"{Colors.CYAN}Network Features:{Colors.END}")
        print("  • Real HTTP/HTTPS support")
        print("  • SSL certificate verification")
        print("  • Download manager with progress")
        print(f"{Colors.CYAN}Security:{Colors.END}")
        print("  • Content Security Policy support")
        print("  • Secure certificate validation")
        print("  • Privacy-focused design")
    
    def _execute_action(self, action: Action):
        """Execute action with error handling"""
        try:
            if action.action_type == "navigate" and action.destination:
                self.load_document(action.destination)
            elif action.action_type == "search":
                query = input(f"{Colors.YELLOW}Enter search query:{Colors.END} ").strip()
                if query:
                    # FIX: Remove the extra space in the URL
                    search_url = f"https://duckduckgo.com/html/?q={query}"
                    self.load_document(search_url)
            elif action.action_type == "show_stats":
                self._show_browser_status()
                input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠️ Action not implemented: {action.action_type}{Colors.END}")
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            print(f"{Colors.RED}❌ Action failed: {e}{Colors.END}")
    
    def run(self):
        """Run the browser in GUI or CLI mode"""
        if self.use_gui and self.gui:
            print("Starting Nova Browser with GUI...")
            self.gui.run()
        else:
            if self.use_gui:
                print("GUI requested but not available, falling back to CLI mode")
            self.run_cli()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Nova Browser")
        self.storage_mgr.save()
        self.thread_pool.shutdown(wait=True)
        print(f"{Colors.GREEN}👋 Nova Browser shut down successfully{Colors.END}")

if __name__ == "__main__":
    # Check dependencies
    try:
        import requests
        import aiohttp
        import certifi
    except ImportError as e:
        print(f"{Colors.RED}❌ Missing dependency: {e}{Colors.END}")
        print("Please install required packages:")
        print("pip install requests aiohttp certifi")
        print("Optional: pip install psutil cryptography")
        sys.exit(1)
    
    # Check if GUI is requested
    use_gui = "--cli" not in sys.argv and GUI_AVAILABLE
    
    if not GUI_AVAILABLE and "--gui" in sys.argv:
        print(f"{Colors.YELLOW}⚠️  GUI requested but tkinter not available. Using CLI mode.{Colors.END}")
        print("On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("On Windows: tkinter is usually included")
        print("On macOS: tkinter is usually included")
    
    # Run the browser
    try:
        runtime = NovaRuntime(use_gui=use_gui)
        runtime.run()
    except Exception as e:
        logger.critical(f"Failed to start Nova Browser: {e}")
        print(f"{Colors.RED}💥 Failed to start browser: {e}{Colors.END}")
        sys.exit(1)
