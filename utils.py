import random, string, socket, ssl, time
import urllib3
from colorama import Fore

urllib3.disable_warnings()

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_ssl_socket(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    ssl_sock = context.wrap_socket(sock, server_hostname=host)
    ssl_sock.connect((host, port))
    return ssl_sock

def get_random_user_agent():
    from config import USER_AGENTS
    return random.choice(USER_AGENTS)

def print_status(message, color=Fore.GREEN):
    timestamp = time.strftime("%H:%M:%S")
    print(f"{Fore.YELLOW}[{timestamp}]{color} {message}{Fore.RESET}")
