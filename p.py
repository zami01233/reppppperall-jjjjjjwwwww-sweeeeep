import requests
import json
import time
import random
import secrets
from eth_account import Account
from eth_account.messages import encode_defunct
from datetime import datetime
import os

# Konfigurasi
REFERRAL_CODE = "PJAK"  # Ganti dengan kode referral Anda
API_BASE_URL = "https://api.jwswap.com"
SIGN_MESSAGE = "dlBsz2PLG8tqFt5k3S1A"  # Message yang perlu di-sign

# File untuk menyimpan data
WALLETS_JSON_FILE = "wallets_data.json"
WALLETS_TXT_FILE = "wallets_backup.txt"
LOG_FILE = "bot_activity.log"

# Headers yang diperlukan
headers = {
    'authority': 'api.jwswap.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.6',
    'content-type': 'application/json',
    'lang': 'zh_TW',
    'origin': 'https://www.jwswap.com',
    'referer': 'https://www.jwswap.com/',
    'sec-ch-ua': '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
}

class ProxyRotator:
    def __init__(self, proxy_file="proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies = []
        self.current_index = 0
        self.load_proxies()

    def load_proxies(self):
        """Load proxies dari file"""
        if os.path.exists(self.proxy_file):
            try:
                with open(self.proxy_file, 'r') as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                if self.proxies:
                    print(f"✅ Loaded {len(self.proxies)} proxies from {self.proxy_file}")
                else:
                    print(f"⚠️ No proxies found in {self.proxy_file}, running without proxy")
            except Exception as e:
                print(f"⚠️ Error loading proxies: {e}")
        else:
            print(f"ℹ️ Proxy file '{self.proxy_file}' not found, running without proxy")
            print(f"💡 To use proxies, create '{self.proxy_file}' with format:")
            print("   http://username:password@ip:port")
            print("   or")
            print("   http://ip:port")

    def get_next_proxy(self):
        """Get next proxy dari list (rotating)"""
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)

        return {
            'http': proxy,
            'https': proxy
        }

    def get_random_proxy(self):
        """Get random proxy dari list"""
        if not self.proxies:
            return None

        proxy = random.choice(self.proxies)
        return {
            'http': proxy,
            'https': proxy
        }

class JWSwapBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.wallets = []
        self.proxy_rotator = ProxyRotator()
        self.load_existing_wallets()

    def log_message(self, message, level="INFO"):
        """Log message ke file dan console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        # Print ke console
        print(message)

        # Simpan ke log file
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"⚠️ Warning: Could not write to log file: {e}")

    def load_existing_wallets(self):
        """Load wallet yang sudah ada dari file JSON"""
        if os.path.exists(WALLETS_JSON_FILE):
            try:
                with open(WALLETS_JSON_FILE, 'r') as f:
                    self.wallets = json.load(f)
                self.log_message(f"✅ Loaded {len(self.wallets)} existing wallets from {WALLETS_JSON_FILE}")
            except Exception as e:
                self.log_message(f"⚠️ Could not load existing wallets: {e}", "WARNING")
                self.wallets = []
        else:
            self.log_message(f"ℹ️ No existing wallets found, starting fresh")

    def generate_wallet(self):
        """Generate wallet Ethereum baru"""
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        account = Account.from_key(private_key)

        wallet_data = {
            'address': account.address,
            'private_key': private_key,
            'referral_code': REFERRAL_CODE,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Generated'
        }

        self.wallets.append(wallet_data)
        # Langsung simpan setelah generate
        self.save_all_wallets()

        return wallet_data

    def save_all_wallets(self):
        """Simpan semua wallet ke multiple format untuk backup"""
        try:
            # 1. Simpan ke JSON (format terstruktur) - hanya data penting
            backup_data = []
            for wallet in self.wallets:
                backup_data.append({
                    'address': wallet['address'],
                    'private_key': wallet['private_key'],
                    'referral_code': wallet.get('referral_code', REFERRAL_CODE),
                    'created_at': wallet.get('created_at', 'N/A'),
                    'status': wallet.get('status', 'Unknown'),
                    'airdrop_id': wallet.get('airdrop_id', 'N/A'),
                    'used_ip': wallet.get('used_ip', 'Unknown')
                })

            with open(WALLETS_JSON_FILE, 'w') as f:
                json.dump(backup_data, f, indent=2)

            # 2. Simpan ke TXT (format readable)
            with open(WALLETS_TXT_FILE, 'w') as f:
                f.write("="*80 + "\n")
                f.write("JWSWAP BOT - WALLET BACKUP\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Wallets: {len(self.wallets)}\n")
                f.write(f"Referral Code: {REFERRAL_CODE}\n")
                f.write("="*80 + "\n\n")

                for i, wallet in enumerate(self.wallets, 1):
                    f.write(f"{'='*80}\n")
                    f.write(f"WALLET #{i}\n")
                    f.write(f"{'='*80}\n")
                    f.write(f"Address      : {wallet['address']}\n")
                    f.write(f"Private Key  : {wallet['private_key']}\n")
                    f.write(f"Referral Code: {wallet.get('referral_code', REFERRAL_CODE)}\n")
                    f.write(f"Created At   : {wallet.get('created_at', 'N/A')}\n")
                    f.write(f"Used IP      : {wallet.get('used_ip', 'Unknown')}\n")
                    f.write(f"Status       : {wallet.get('status', 'Unknown')}\n")
                    f.write(f"Airdrop ID   : {wallet.get('airdrop_id', 'N/A')}\n")
                    f.write(f"Claim Status : {wallet.get('claim_result', {}).get('msg', 'N/A') if isinstance(wallet.get('claim_result'), dict) else 'N/A'}\n")
                    f.write(f"{'='*80}\n\n")

            # 3. Simpan ke CSV format juga
            csv_file = "wallets_export.csv"
            with open(csv_file, 'w') as f:
                f.write("No,Address,Private Key,Referral Code,Created At,Used IP,Status,Airdrop ID\n")
                for i, wallet in enumerate(self.wallets, 1):
                    f.write(f"{i},{wallet['address']},{wallet['private_key']},{wallet.get('referral_code', REFERRAL_CODE)},{wallet.get('created_at', 'N/A')},{wallet.get('used_ip', 'Unknown')},{wallet.get('status', 'Unknown')},{wallet.get('airdrop_id', 'N/A')}\n")

            self.log_message(f"✅ Wallets saved to: {WALLETS_JSON_FILE}, {WALLETS_TXT_FILE}, {csv_file}")

        except Exception as e:
            self.log_message(f"❌ Error saving wallets: {e}", "ERROR")

    def get_current_time(self):
        """Dapatkan timestamp saat ini"""
        return int(time.time())

    def create_signature(self, private_key):
        """Buat signature dari message fixed dengan private key"""
        try:
            message_encoded = encode_defunct(text=SIGN_MESSAGE)
            signed_message = Account.sign_message(message_encoded, private_key)
            return signed_message.signature.hex()
        except Exception as e:
            self.log_message(f"❌ Error creating signature: {e}", "ERROR")
            return None

    def get_current_ip(self, proxy=None):
        """Dapatkan IP yang sedang digunakan"""
        try:
            if proxy:
                response = requests.get('https://api.ipify.org?format=json', proxies=proxy, timeout=10)
            else:
                response = requests.get('https://api.ipify.org?format=json', timeout=10)

            if response.status_code == 200:
                return response.json().get('ip', 'Unknown')
        except:
            pass
        return 'Unknown'

    def make_request(self, method, url, max_retries=3, fixed_proxy=None, **kwargs):
        """Make HTTP request dengan fixed proxy untuk konsistensi IP per wallet"""
        proxy = fixed_proxy  # Gunakan proxy yang sudah ditentukan

        for attempt in range(max_retries):
            try:
                if proxy:
                    kwargs['proxies'] = proxy
                    kwargs['timeout'] = 30
                else:
                    kwargs['timeout'] = 30

                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **kwargs)

                return response

            except (requests.exceptions.ProxyError,
                    requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:

                self.log_message(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}", "WARNING")

                if attempt < max_retries - 1:
                    # Hanya retry dengan proxy yang sama untuk konsistensi
                    if proxy:
                        self.log_message(f"🔄 Retrying with same proxy for IP consistency...", "WARNING")
                    else:
                        self.log_message(f"🔄 Retrying without proxy...", "WARNING")

                    time.sleep(2)  # Delay sebelum retry
                else:
                    self.log_message(f"❌ All retry attempts failed", "ERROR")
                    raise

        return None

    def check_registration(self, wallet_address, fixed_proxy=None):
        """Cek apakah wallet sudah terdaftar"""
        url = f"{API_BASE_URL}/api/auth/isRegister"
        current_time = self.get_current_time()

        payload = {
            "wallet": wallet_address,
            "time": current_time
        }

        try:
            response = self.make_request('POST', url, json=payload, fixed_proxy=fixed_proxy)
            self.log_message(f"📋 Check registration response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log_message(f"📝 Registration data: {data}")
                return data
            return None
        except Exception as e:
            self.log_message(f"❌ Error checking registration: {e}", "ERROR")
            return None

    def register_wallet(self, wallet_address, private_key, fixed_proxy=None):
        """Registrasi wallet baru dengan REFERRAL CODE yang benar"""
        url = f"{API_BASE_URL}/api/auth/isRegister"

        current_time = self.get_current_time()

        signature = self.create_signature(private_key)
        if not signature:
            self.log_message("❌ Failed to create signature for registration", "ERROR")
            return None

        self.log_message(f"🔐 Generated signature: {signature}")
        self.log_message(f"🎟️ Using referral code: {REFERRAL_CODE}")

        # ✅ FIX: Gunakan REFERRAL_CODE, bukan top_code
        payload = {
            "wallet": wallet_address,
            "code": REFERRAL_CODE,  # ✅ FIXED: Gunakan referral code Anda!
            "time": current_time,
            "sign_message": signature
        }

        try:
            response = self.make_request('POST', url, json=payload, fixed_proxy=fixed_proxy)
            self.log_message(f"📝 Registration response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log_message(f"✅ Registration result: {data}")
                return data
            else:
                self.log_message(f"❌ Registration failed with status: {response.status_code}", "ERROR")
                self.log_message(f"Response: {response.text}", "ERROR")
            return None
        except Exception as e:
            self.log_message(f"❌ Error during registration: {e}", "ERROR")
            return None

    def login_wallet(self, wallet_address, private_key, fixed_proxy=None):
        """Login dengan wallet menggunakan REFERRAL CODE yang benar"""
        url = f"{API_BASE_URL}/api/auth/login"

        current_time = self.get_current_time()

        signature = self.create_signature(private_key)
        if not signature:
            self.log_message("❌ Failed to create signature for login", "ERROR")
            return None

        self.log_message(f"🔐 Generated signature: {signature}")
        self.log_message(f"🎟️ Using referral code: {REFERRAL_CODE}")

        # ✅ FIX: Gunakan REFERRAL_CODE, bukan top_code
        payload = {
            "wallet": wallet_address,
            "code": REFERRAL_CODE,  # ✅ FIXED: Gunakan referral code Anda!
            "time": current_time,
            "sign_message": signature
        }

        try:
            response = self.make_request('POST', url, json=payload, fixed_proxy=fixed_proxy)
            self.log_message(f"🔑 Login response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log_message(f"📄 Login response data: {data}")

                if data.get('code') == 200 and 'data' in data and 'token' in data['data']:
                    token = data['data']['token']
                    # FIX: Hapus "Bearer " jika sudah ada di token
                    if token.startswith('Bearer '):
                        token = token[7:]  # Hapus "Bearer " prefix
                    self.log_message(f"✅ Login successful! Token: {token[:50]}...")
                    return token
                else:
                    self.log_message(f"❌ Login failed: {data.get('msg', 'Unknown error')}", "ERROR")
            else:
                self.log_message(f"❌ Login failed with status: {response.status_code}", "ERROR")
                self.log_message(f"Response: {response.text}", "ERROR")
            return None
        except Exception as e:
            self.log_message(f"❌ Error during login: {e}", "ERROR")
            return None

    def get_index_data(self, token, fixed_proxy=None):
        """Dapatkan data index/user - dipanggil SETELAH claim"""
        url = f"{API_BASE_URL}/api/index/index"
        headers_with_auth = headers.copy()
        headers_with_auth['authorization'] = f'Bearer {token}'

        try:
            response = self.make_request('POST', url, headers=headers_with_auth, fixed_proxy=fixed_proxy)
            self.log_message(f"📊 Index data response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log_message(f"✅ Index data received successfully")
                return data
            else:
                self.log_message(f"❌ Failed to get index data: {response.status_code}", "ERROR")
                self.log_message(f"Response: {response.text}", "ERROR")
            return None
        except Exception as e:
            self.log_message(f"❌ Error getting index data: {e}", "ERROR")
            return None

    def get_bulletin(self, token, fixed_proxy=None):
        """Dapatkan bulletin info - dipanggil paling akhir"""
        url = f"{API_BASE_URL}/api/basic/bulletin"
        headers_with_auth = headers.copy()
        headers_with_auth['authorization'] = f'Bearer {token}'

        try:
            response = self.make_request('POST', url, headers=headers_with_auth, fixed_proxy=fixed_proxy)
            self.log_message(f"📰 Bulletin response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.log_message(f"✅ Bulletin data received")
                return data
            return None
        except Exception as e:
            self.log_message(f"❌ Error getting bulletin: {e}", "ERROR")
            return None

    def get_airdrop_info(self, token, fixed_proxy=None):
        """Dapatkan informasi airdrop SEBELUM claim"""
        url = f"{API_BASE_URL}/api/index/index"
        headers_with_auth = headers.copy()
        headers_with_auth['authorization'] = f'Bearer {token}'

        try:
            response = self.make_request('POST', url, headers=headers_with_auth, fixed_proxy=fixed_proxy)
            self.log_message(f"🔍 Getting airdrop info: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and 'data' in data:
                    # Extract airdrop ID dari airdrop_list
                    airdrop_list = data['data'].get('airdrop_list', [])
                    if airdrop_list and len(airdrop_list) > 0:
                        airdrop_id = airdrop_list[0].get('id')
                        status = airdrop_list[0].get('status')
                        total = airdrop_list[0].get('total')
                        self.log_message(f"✅ Airdrop found - ID: {airdrop_id}, Status: {status}, Total: {total}")
                        return airdrop_id
                    else:
                        self.log_message("❌ No airdrop found in list", "WARNING")
                else:
                    self.log_message(f"❌ Invalid response format: {data}", "ERROR")
            else:
                self.log_message(f"❌ Failed response: {response.text}", "ERROR")
            return None
        except Exception as e:
            self.log_message(f"❌ Error getting airdrop info: {e}", "ERROR")
            return None

    def claim_airdrop(self, token, airdrop_id, fixed_proxy=None):
        """Claim airdrop token"""
        url = f"{API_BASE_URL}/api/airdrop/draw"
        headers_with_auth = headers.copy()
        headers_with_auth['authorization'] = f'Bearer {token}'

        payload = {
            "id": airdrop_id
        }

        try:
            response = self.make_request('POST', url, json=payload, headers=headers_with_auth, fixed_proxy=fixed_proxy)
            self.log_message(f"🎁 Airdrop claim response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                self.log_message(f"📦 Airdrop claim result: {result}")
                if result.get('code') == 200:
                    self.log_message(f"✅ Airdrop claimed successfully! Message: {result.get('msg')}")
                    return True, result
                else:
                    self.log_message(f"❌ Airdrop claim failed: {result.get('msg', 'Unknown error')}", "ERROR")
                    return False, result
            else:
                self.log_message(f"❌ Airdrop claim failed with status: {response.status_code}", "ERROR")
                self.log_message(f"Response: {response.text}", "ERROR")
                return False, None
        except Exception as e:
            self.log_message(f"❌ Error claiming airdrop: {e}", "ERROR")
            return False, None

    def process_wallet(self, wallet_data, current_ip='Unknown', fixed_proxy=None):
        """Proses lengkap untuk satu wallet dengan IP tetap"""
        self.log_message(f"\n{'='*60}")
        self.log_message(f"🔧 Processing wallet: {wallet_data['address']}")
        self.log_message(f"🎟️ Using referral code: {REFERRAL_CODE}")
        self.log_message(f"🌐 Fixed IP for this wallet: {current_ip}")
        self.log_message(f"{'='*60}")

        wallet_data['used_ip'] = current_ip  # Simpan IP yang digunakan

        # Step 1: Check registration
        self.log_message("Step 1: Checking registration status...")
        reg_check = self.check_registration(wallet_data['address'], fixed_proxy=fixed_proxy)

        if not reg_check or reg_check.get('code') != 200:
            self.log_message("❌ Failed to check registration", "ERROR")
            wallet_data['status'] = 'Registration check failed'
            self.save_all_wallets()
            return False

        is_registered = reg_check['data']['is_register']
        self.log_message(f"📝 Is registered: {is_registered}")

        # Jika sudah terdaftar, langsung login
        if is_registered == 1:
            self.log_message("ℹ️ Wallet already registered, proceeding to login...")
        else:
            # Step 2: Register wallet dengan REFERRAL CODE
            self.log_message(f"Step 2: Registering wallet with referral code {REFERRAL_CODE}...")
            registration = self.register_wallet(wallet_data['address'], wallet_data['private_key'], fixed_proxy=fixed_proxy)

            if not registration or registration.get('code') != 200:
                self.log_message("❌ Registration failed", "ERROR")
                wallet_data['status'] = 'Registration failed'
                self.save_all_wallets()
                return False

            self.log_message("✅ Registration successful with referral code!")

            # Tunggu setelah registrasi
            wait_time = 3
            self.log_message(f"⏳ Waiting {wait_time} seconds after registration...")
            time.sleep(wait_time)

        # Step 3: Login dengan REFERRAL CODE
        self.log_message(f"Step 3: Logging in with referral code {REFERRAL_CODE}...")
        token = self.login_wallet(wallet_data['address'], wallet_data['private_key'], fixed_proxy=fixed_proxy)

        if token:
            self.log_message("✅ Login successful!")
            wallet_data['token'] = token
            wallet_data['status'] = 'Login successful'
            self.save_all_wallets()  # Simpan token
        else:
            self.log_message("❌ Login failed!", "ERROR")
            wallet_data['status'] = 'Login failed'
            self.save_all_wallets()
            return False

        # Tunggu sebentar
        time.sleep(2)

        # Step 4: Get airdrop info SEBELUM claim
        self.log_message("Step 4: Getting airdrop information...")
        airdrop_id = self.get_airdrop_info(token, fixed_proxy=fixed_proxy)

        if not airdrop_id:
            self.log_message("❌ Failed to get airdrop ID", "ERROR")
            wallet_data['status'] = 'Airdrop ID not found'
            self.save_all_wallets()
            return False

        wallet_data['airdrop_id'] = airdrop_id
        self.save_all_wallets()  # Simpan airdrop ID

        # Tunggu sebentar
        time.sleep(2)

        # Step 5: Claim airdrop
        self.log_message("Step 5: Claiming airdrop...")
        airdrop_success, claim_result = self.claim_airdrop(token, airdrop_id, fixed_proxy=fixed_proxy)

        if airdrop_success:
            self.log_message("🎉 ✅ Airdrop claimed successfully!")
            wallet_data['status'] = 'Airdrop claimed successfully'
            wallet_data['claim_result'] = claim_result
            self.save_all_wallets()
        else:
            self.log_message("❌ Airdrop claim failed!", "ERROR")
            wallet_data['status'] = 'Airdrop claim failed'
            wallet_data['claim_result'] = claim_result
            self.save_all_wallets()
            return False

        # Tunggu sebentar
        time.sleep(2)

        # Step 6: Get index data (untuk update status)
        self.log_message("Step 6: Getting updated index data...")
        index_data = self.get_index_data(token, fixed_proxy=fixed_proxy)
        if index_data and index_data.get('code') == 200:
            self.log_message("✅ Index data updated successfully")

        # Tunggu sebentar
        time.sleep(2)

        # Step 7: Get bulletin (terakhir)
        self.log_message("Step 7: Getting bulletin...")
        bulletin = self.get_bulletin(token, fixed_proxy=fixed_proxy)
        if bulletin and bulletin.get('code') == 200:
            self.log_message("✅ Bulletin access successful!")

        return True

    def run_multiple_accounts(self, count=5, min_delay=25, max_delay=40):
        """Jalankan bot untuk multiple accounts"""
        self.log_message(f"🚀 Starting JWSwap Bot for {count} accounts...")
        self.log_message(f"🎟️ Using referral code: {REFERRAL_CODE}")
        self.log_message(f"📝 Using sign message: {SIGN_MESSAGE}")
        self.log_message(f"⏱️ Delay between accounts: {min_delay}-{max_delay} seconds")

        successful_accounts = 0

        for i in range(count):
            self.log_message(f"\n{'#'*60}")
            self.log_message(f"💰 Processing Account {i+1}/{count}")
            self.log_message(f"{'#'*60}")

            # Generate wallet baru
            wallet = self.generate_wallet()
            self.log_message(f"📬 Generated wallet: {wallet['address']}")

            # Get IP yang akan digunakan (sebelum proses)
            proxy = self.proxy_rotator.get_next_proxy()
            current_ip = self.get_current_ip(proxy)

            # Process wallet
            if self.process_wallet(wallet, current_ip, proxy):
                successful_accounts += 1
                self.log_message(f"✅ Account {i+1} completed successfully!")
            else:
                self.log_message(f"❌ Account {i+1} failed!", "ERROR")

            # Delay antara akun untuk menghindari rate limiting
            if i < count - 1:
                delay = random.randint(min_delay, max_delay)
                self.log_message(f"⏳ Waiting {delay} seconds before next account...")
                time.sleep(delay)

        self.log_message(f"\n{'='*60}")
        self.log_message(f"🎉 COMPLETED: Successful accounts: {successful_accounts}/{count}")
        self.log_message(f"💾 All data saved to multiple files")
        self.log_message(f"{'='*60}")

        return successful_accounts

# Fungsi utama
def main():
    print("=" * 80)
    print("🤖 JWSwap Auto Referral Bot with Proxy Support")
    print("=" * 80)
    print()

    # Info tentang files
    print("📁 Files that will be created/updated:")
    print(f"   - {WALLETS_JSON_FILE} (JSON format - for bot)")
    print(f"   - {WALLETS_TXT_FILE} (TXT format - human readable)")
    print(f"   - wallets_export.csv (CSV format - for Excel)")
    print(f"   - {LOG_FILE} (Activity log)")
    print()

    # Info tentang proxy
    print("🔄 Proxy Support:")
    print("   To use proxies, create 'proxies.txt' file with format:")
    print("   http://username:password@ip:port")
    print("   or")
    print("   http://ip:port")
    print()

    bot = JWSwapBot()

    print("=" * 80)
    print("⚙️ BOT CONFIGURATION")
    print("=" * 80)
    print(f"🎟️ Referral Code: {REFERRAL_CODE}")
    print()

    try:
        # Tanya jumlah akun
        count = int(input("📊 How many accounts do you want to generate? ").strip())

        if count <= 0:
            print("❌ Invalid number. Must be greater than 0")
            return

        print()

        # Tanya delay minimum
        min_delay = int(input("⏱️ Minimum delay between accounts (seconds, recommended 20-30): ").strip())

        if min_delay < 5:
            print("⚠️ Warning: Delay too short, using minimum 5 seconds")
            min_delay = 5

        # Tanya delay maximum
        max_delay = int(input("⏱️ Maximum delay between accounts (seconds, recommended 30-50): ").strip())

        if max_delay < min_delay:
            print(f"⚠️ Warning: Max delay must be >= min delay, setting to {min_delay + 10}")
            max_delay = min_delay + 10

        print()
        print("=" * 80)
        print("📋 CONFIGURATION SUMMARY")
        print("=" * 80)
        print(f"   Referral Code        : {REFERRAL_CODE}")
        print(f"   Accounts to generate : {count}")
        print(f"   Delay range          : {min_delay}-{max_delay} seconds")
        print(f"   Estimated time       : ~{((min_delay + max_delay) / 2 * (count - 1) / 60):.1f} minutes")
        print("=" * 80)
        print()

        confirm = input(f"⚠️ Start processing {count} accounts with referral code {REFERRAL_CODE}? (yes/no): ").strip().lower()

        if confirm not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return

        print()
        print("=" * 80)
        print(f"🚀 Starting bot for {count} accounts...")
        print(f"🎟️ All accounts will use referral code: {REFERRAL_CODE}")
        print("=" * 80)
        print()

        successful = bot.run_multiple_accounts(count, min_delay, max_delay)

        print()
        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"🎟️ Referral Code: {REFERRAL_CODE}")
        print(f"✅ Successful: {successful}/{count}")
        print(f"❌ Failed: {count - successful}/{count}")
        print(f"📁 Data saved to:")
        print(f"   - {WALLETS_JSON_FILE}")
        print(f"   - {WALLETS_TXT_FILE}")
        print(f"   - wallets_export.csv")
        print(f"   - {LOG_FILE}")
        print()
        print("🔐 IMPORTANT: Keep your private keys safe!")
        print("   Tokens are NOT saved in backup files for security")
        print()
        print(f"💡 TIP: Check your referral dashboard to verify {successful} new referrals!")
        print("=" * 80)

    except ValueError:
        print("❌ Invalid input. Please enter a number.")
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        print("💾 All generated wallets have been saved")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💾 All generated wallets have been saved")

if __name__ == "__main__":
    main()
