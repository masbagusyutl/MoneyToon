from urllib.parse import parse_qs
import requests
import json
import time
from datetime import datetime, timedelta
from colorama import Fore, Style, init

# Inisialisasi Colorama
init(autoreset=True)

# Konstanta
BASE_URL = "https://mt.promptale.io"
HEADERS_TEMPLATE = {
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}
GAMES = {
    "NAMES": ["MahJong", "Matching", "Sliding"],
    "LEVELS": ["easy", "medium", "hard"],
    "REQUIREMENTS": {
        "medium": 1,  # Jumlah teman yang dibutuhkan
        "hard": 3
    }
}

# Fungsi untuk mencetak pesan selamat datang
def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop  Money Toon")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop\n")

# Fungsi untuk memuat data akun dari file data.txt
def load_accounts():
    try:
        with open('data.txt', 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + "❌ File data.txt tidak ditemukan! Harap tambahkan file.")
        return []

# Fungsi untuk mengonversi data dari data.txt ke JSON payload
def convert_to_payload(account_line):
    try:
        # Parse URL-encoded data menjadi dictionary
        parsed_data = parse_qs(account_line)
        init_data = account_line  # Data asli tetap digunakan
        init_data_unsafe = {
            "authDate": datetime.utcfromtimestamp(int(parsed_data.get("auth_date", [0])[0])).isoformat() + "Z",
            "chatInstance": parsed_data.get("chat_instance", [""])[0],
            "chatType": parsed_data.get("chat_type", [""])[0],
            "hash": parsed_data.get("hash", [""])[0],
            "startParam": parsed_data.get("start_param", [""])[0],
            "user": json.loads(parsed_data.get("user", ["{}"])[0])
        }
        return {"initData": init_data, "initDataUnsafe": init_data_unsafe}
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat mengonversi payload: {e}")
        return None

# Fungsi untuk login dan mendapatkan accessToken
def login_and_get_token(account_line):
    print(Fore.YELLOW + "🔄 Melakukan login...")
    try:
        payload = convert_to_payload(account_line)
        if not payload:
            print(Fore.RED + "❌ Gagal mengonversi data akun. Melewati akun ini.")
            return None

        response = requests.post(f"{BASE_URL}/auth/loginTg", headers=HEADERS_TEMPLATE, json=payload)
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                access_token = data["data"]["accessToken"]
                user_name = data["data"]["user"]["userName"]  # Ambil nama pengguna
                print(Fore.GREEN + f"✅ Login berhasil! Nama Pengguna: {user_name}")
                return access_token
            else:
                print(Fore.RED + "❌ Login gagal! Periksa data akun.")
        else:
            print(Fore.RED + f"❌ Gagal login. Status: {response.status_code}")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat login: {e}")
    return None

# Fungsi untuk menerjemahkan pesan
def translate_message(message, target_language="id"):
    from deep_translator import GoogleTranslator
    try:
        if not message:
            return "Pesan tidak tersedia untuk diterjemahkan."
        
        # Bersihkan spasi ganda pada pesan
        message = " ".join(message.split())
        print(Fore.CYAN + f"Pesan asli: {message}")  # Log untuk debug

        return GoogleTranslator(source="auto", target=target_language).translate(message)
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat menerjemahkan pesan: {e}")
        return message  # Jika gagal menerjemahkan, kembalikan pesan asli

def retry_request(func, retries=2, delay=2):
    """Retry request untuk menangani kegagalan sementara."""
    for attempt in range(retries):
        try:
            return func()
        except requests.RequestException as e:
            print(Fore.RED + f"❌ Kesalahan: {e}. Percobaan ulang ({attempt + 1}/{retries})...")
            time.sleep(delay)
    return None

def check_and_attend(access_token):
    """Memeriksa dan melakukan absensi jika belum dilakukan."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    try:
        print(Fore.YELLOW + "🔄 Memeriksa status absensi...")
        response = retry_request(lambda: requests.get(f"{BASE_URL}/tasks/isAttendanceToday", headers=headers))
        if response and response.status_code == 200:
            message = response.json().get("message", "Tidak ada pesan.")
            print(Fore.GREEN + f"Pesan: {translate_message(message)}")

            if not response.json().get("data", True):
                print(Fore.BLUE + "✅ Belum absensi. Melakukan absensi...")
                attend_response = retry_request(lambda: requests.post(f"{BASE_URL}/tasks/attend", headers=headers))
                if attend_response and attend_response.status_code == 201:
                    print(Fore.GREEN + "✅ Absensi berhasil!")
                    response_message = attend_response.json().get("message", "Tidak ada pesan.")
                    print(Fore.CYAN + f"Pesan: {translate_message(response_message)}")
                else:
                    print(Fore.RED + f"❌ Gagal melakukan absensi. Status: {attend_response.status_code if attend_response else 'Tidak ada respon'}")
            else:
                print(Fore.YELLOW + "✅ Sudah absensi hari ini.")
        else:
            print(Fore.RED + f"❌ Gagal memeriksa status absensi. Status: {response.status_code if response else 'Tidak ada respon'}")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat memeriksa absensi: {e}")

# Fungsi fitur utama
def check_points_and_eggs(access_token):
    """Memeriksa poin dan telur pengguna."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    try:
        print(Fore.YELLOW + "🔄 Memeriksa poin dan jumlah telur...")
        response = retry_request(lambda: requests.get(f"{BASE_URL}/main/mypoint", headers=headers))
        if response and response.status_code == 200:
            data = response.json().get("data", {})
            print(Fore.GREEN + f"✅ Poin: {data.get('point', 0)}, Telur: {data.get('egg', 0)}")
            if data.get("egg", 0) > 0:
                open_eggs(access_token, data["egg"])
        else:
            print(Fore.RED + f"❌ Gagal memeriksa poin. Status: {response.status_code if response else 'Tidak ada respon'}")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat memeriksa poin: {e}")

def open_eggs(access_token, egg_count):
    """Membuka telur berdasarkan jumlah yang tersedia."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    print(Fore.YELLOW + f"🔄 Membuka {egg_count} telur...")
    for i in range(egg_count):
        try:
            response = retry_request(lambda: requests.post(f"{BASE_URL}/rewards/myEggOpen", headers=headers))
            if response and response.status_code == 201:
                data = response.json().get("data", {})
                message = response.json().get("message", "Tidak ada pesan.")
                print(Fore.GREEN + f"✅ Telur ke-{i + 1} dibuka! {translate_message(message)}")
                print(Fore.CYAN + f"Hasil: {data.get('codeDesc')} ({data.get('getPoint')} poin)")
            else:
                print(Fore.RED + f"❌ Gagal membuka telur ke-{i + 1}. Status: {response.status_code if response else 'Tidak ada respon'}")
        except Exception as e:
            print(Fore.RED + f"❌ Kesalahan saat membuka telur: {e}")

def fetch_and_process_tasks(access_token):
    """Mengambil dan memproses daftar tugas."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    try:
        print(Fore.YELLOW + "🔄 Mengambil daftar tugas...")
        response = retry_request(lambda: requests.get(f"{BASE_URL}/tasks", headers=headers))
        if response and response.status_code == 200:
            tasks = response.json().get("data", [])
            print(Fore.GREEN + f"✅ Ditemukan {len(tasks)} tugas.")
            
            for task in tasks:
                task_title = task.get("taskMainTitle", "Tanpa judul")
                task_idx = task.get("taskIdx")
                run_status = task.get("runStatus")
                complete_count = task.get("completeCount", 0)

                # Melewati tugas jika sudah selesai
                if complete_count > 0:
                    print(Fore.GREEN + f"✅ Tugas {task_title} sudah selesai. Melewati...")
                    continue

                # Jika tugas sudah dijalankan, selesaikan
                if run_status == "S":
                    print(Fore.BLUE + f"🔄 Menyelesaikan tugas: {task_title} (taskIdx: {task_idx})")
                    complete_task(access_token, task_idx)
                else:
                    print(Fore.YELLOW + f"🔄 Menjalankan tugas baru: {task_title} (taskIdx: {task_idx})")
                    run_task(access_token, task_idx)
                time.sleep(2)  # Jeda untuk menghindari spam API
        else:
            print(Fore.RED + f"❌ Gagal mengambil daftar tugas. Status: {response.status_code if response else 'Tidak ada respon'}")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat mengambil daftar tugas: {e}")

def run_task(access_token, task_idx):
    """Menjalankan tugas berdasarkan taskIdx."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    payload = {"taskIdx": task_idx}
    try:
        response = retry_request(lambda: requests.post(f"{BASE_URL}/tasks/taskRun", json=payload, headers=headers))
        if response and response.status_code == 201:
            print(Fore.GREEN + f"✅ Tugas berhasil dijalankan. Pesan: {translate_message(response.json().get('message', ''))}")
        else:
            print(Fore.RED + f"❌ Gagal menjalankan tugas. Status: {response.status_code if response else 'Tidak ada respon'}")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat menjalankan tugas: {e}")

def complete_task(access_token, task_idx):
    """Menyelesaikan tugas berdasarkan taskIdx."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    payload = {"taskIdx": task_idx}
    try:
        response = retry_request(lambda: requests.post(f"{BASE_URL}/tasks/taskComplete", json=payload, headers=headers))
        if response and response.status_code == 201:
            data = response.json().get("data", {})
            print(Fore.GREEN + f"✅ Tugas selesai! Poin: {data.get('point')}")
        else:
            print(Fore.RED + f"❌ Gagal menyelesaikan tugas. Status: {response.status_code if response else 'Tidak ada respon'}")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat menyelesaikan tugas: {e}")

# Fitur baru: Cek dan Klaim SL Pass Rewards
def check_and_claim_sl_pass(access_token):
    """Memeriksa dan mengklaim hadiah SL Pass gratis."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    try:
        print(Fore.YELLOW + "🔄 Memeriksa hadiah SL Pass gratis...")
        response = retry_request(lambda: requests.get(f"{BASE_URL}/rewards/mySlPassList", headers=headers))
        if response and response.status_code == 200:
            rewards = response.json().get("data", [])
            has_unclaimed_rewards = False
            for reward in rewards:
                if not reward.get("slPassId", "").startswith("free"):
                    continue
                step = reward.get("step", "Tidak diketahui")
                is_claimed = reward.get("isClaim", False)
                items = ", ".join(
                    f"{Fore.CYAN}{item['count']} {item['item']}{Style.RESET_ALL}"
                    for item in reward.get("getItems", [])
                )

                if is_claimed:
                    print(Fore.YELLOW + f"✅ Hadiah SL Pass langkah {step} sudah diklaim: {items}")
                else:
                    print(Fore.BLUE + f"🔄 Mengklaim hadiah langkah {step}: {items}")
                    claim_response = retry_request(lambda: requests.post(
                        f"{BASE_URL}/rewards/slPassClaim", 
                        json={"slPassId": reward["slPassId"]}, 
                        headers=headers
                    ))
                    if claim_response and claim_response.status_code == 201:
                        print(Fore.GREEN + f"✅ Hadiah langkah {step} berhasil diklaim!")
                        has_unclaimed_rewards = True
                    else:
                        print(Fore.RED + f"❌ Gagal mengklaim hadiah langkah {step}")
            
            if not has_unclaimed_rewards:
                print(Fore.YELLOW + "✅ Semua hadiah SL Pass gratis sudah diklaim.")
        else:
            print(Fore.RED + f"❌ Gagal memeriksa hadiah SL Pass. Status: {response.status_code if response else 'Tidak ada respon'}")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat memproses SL Pass: {e}")

# Fitur baru: Bermain Game
def play_games(access_token):
    """Memeriksa mode permainan yang tersedia dan memainkan permainan."""
    headers = {**HEADERS_TEMPLATE, "authorization": f"Bearer {access_token}"}
    try:
        print(Fore.YELLOW + "🔄 Memeriksa status permainan...")
        friends_response = retry_request(lambda: requests.get(f"{BASE_URL}/user/friendsCount", headers=headers))
        if not friends_response or friends_response.status_code != 200:
            print(Fore.RED + "❌ Gagal memeriksa jumlah teman.")
            return
        friends_count = friends_response.json().get("data", 0)
        print(Fore.CYAN + f"✅ Jumlah teman: {friends_count}")

        available_levels = [
            level for level in GAMES["LEVELS"]
            if level == "easy" or friends_count >= GAMES["REQUIREMENTS"].get(level, 0)
        ]

        for game in GAMES["NAMES"]:
            print(Fore.YELLOW + f"🔄 Memeriksa status permainan {game}...")
            game_status_response = retry_request(lambda: requests.get(
                f"{BASE_URL}/games/status?gameCode={game}", headers=headers
            ))
            if not game_status_response or game_status_response.status_code != 200:
                print(Fore.RED + f"❌ Gagal memeriksa status permainan {game}.")
                continue

            game_data = game_status_response.json().get("data", [])
            for level in GAMES["LEVELS"]:
                level_data = next((d for d in game_data if d["level"] == level), {})
                remaining_times = level_data.get("dailyTimes", 0) - level_data.get("times", 0)
                if level in available_levels:
                    print(Fore.BLUE + f"🔄 Bermain {game} ({level}): {remaining_times} peluang tersisa...")
                    for i in range(remaining_times):
                        try:
                            game_run_response = retry_request(lambda: requests.post(
                                f"{BASE_URL}/games/gameRun", 
                                json={"gameId": game, "level": level, "logStatus": "S"}, 
                                headers=headers
                            ))
                            if game_run_response and game_run_response.status_code == 201:
                                run_idx = game_run_response.json().get("data", "")
                                game_complete_response = retry_request(lambda: requests.post(
                                    f"{BASE_URL}/games/gameComplete", 
                                    json={"gameId": game, "level": level, "runIdx": run_idx}, 
                                    headers=headers
                                ))
                                if game_complete_response and game_complete_response.status_code == 201:
                                    points = game_complete_response.json().get("data", {}).get("point", 0)
                                    print(Fore.GREEN + f"✅ Permainan selesai, poin didapat: {points}")
                            else:
                                print(Fore.RED + f"❌ Gagal memulai permainan {game} ({level}).")
                        except Exception as e:
                            print(Fore.RED + f"❌ Kesalahan saat bermain {game} ({level}): {e}")
                        time.sleep(2)
                else:
                    print(Fore.YELLOW + f"🚫 Level {level} terkunci untuk {game}.")
    except Exception as e:
        print(Fore.RED + f"❌ Kesalahan saat memproses permainan: {e}")

# Fungsi hitung mundur 1 hari
def countdown_timer():
    end_time = datetime.now() + timedelta(days=1)
    print(Fore.BLUE + "🔄 Hitung mundur 1 hari dimulai...")
    while datetime.now() < end_time:
        remaining = end_time - datetime.now()
        print(Fore.YELLOW + f"Sisa waktu: {remaining}", end="\r")
        time.sleep(1)
    print(Fore.GREEN + "\n🔄 Mengulang proses...")

# Fungsi utama
def main():
    print_welcome_message()
    accounts = load_accounts()
    if not accounts:
        print(Fore.RED + "❌ Tidak ada akun ditemukan di data.txt!")
        return

    print(Fore.CYAN + f"🔄 Memulai proses untuk {len(accounts)} akun...\n")
    for idx, account in enumerate(accounts, start=1):
        print(Fore.BLUE + f"\n🔄 Memproses akun {idx}/{len(accounts)}...")
        access_token = login_and_get_token(account)
        if access_token:
            check_and_attend(access_token)
            check_points_and_eggs(access_token)
            fetch_and_process_tasks(access_token)
            check_and_claim_sl_pass(access_token)
            play_games(access_token)
        time.sleep(5)

    print(Fore.GREEN + "✅ Semua akun selesai diproses. Mengulang dalam 24 jam...")
    countdown_timer()

if __name__ == "__main__":
    main()
