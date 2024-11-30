import time
import requests
from colorama import Fore, Style, init
from datetime import datetime, timedelta

# Inisialisasi Colorama
init(autoreset=True)

# Fungsi untuk mencetak pesan selamat datang
def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop  Money Toon")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop\n")

# Fungsi untuk memuat akun dari file data.txt
def load_accounts():
    try:
        with open('data.txt', 'r') as file:
            lines = [line.strip() for line in file if line.strip()]
            # Mengelompokkan setiap dua baris sebagai pasangan auth dan cookie
            if len(lines) % 2 != 0:
                print(Fore.RED + "❌ Format file data.txt tidak valid! Pastikan setiap akun terdiri dari dua baris (auth dan cookie).")
                return []
            return [(lines[i], lines[i + 1]) for i in range(0, len(lines), 2)]
    except FileNotFoundError:
        print(Fore.RED + "File data.txt tidak ditemukan!")
        return []

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

# Fungsi untuk mengambil daftar tugas
def fetch_tasks(authorization, cookie):
    """Mengambil daftar tugas untuk akun tertentu."""
    headers = {
        "authorization": authorization,
        "cookie": cookie,
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    try:
        print(Fore.YELLOW + "🔄 Mengambil daftar tugas...")
        response = requests.get("https://mt.promptale.io/tasks", headers=headers)
        if response.status_code == 200:
            tasks = response.json().get("data", [])
            print(Fore.CYAN + f"✅ {len(tasks)} tugas ditemukan.")
            
            # Proses setiap tugas
            for task in tasks:
                task_idx = task.get("taskIdx")
                task_title = task.get("taskMainTitle")
                run_status = task.get("runStatus")
                complete_count = task.get("completeCount", 0)
                
                # Log informasi tugas
                print(Fore.MAGENTA + f"Tugas: {task_title}, Status: {run_status}, Penyelesaian: {complete_count}")

                # Melewati tugas yang sudah selesai
                if complete_count > 0:
                    print(Fore.GREEN + f"✅ Tugas {task_title} sudah selesai. Melewati...")
                    continue

                # Jika tugas sudah dijalankan (runStatus: "S"), selesaikan tugas
                if run_status == "S":
                    print(Fore.BLUE + f"🔄 Menyelesaikan tugas: {task_title} (taskIdx: {task_idx})")
                    complete_task(authorization, cookie, task_idx)
                else:
                    print(Fore.YELLOW + f"🔄 Menjalankan tugas baru: {task_title} (taskIdx: {task_idx})")
                    run_task(authorization, cookie, task_idx)
                time.sleep(2)  # Jeda 2 detik antara tugas
        else:
            print(Fore.RED + f"❌ Gagal mengambil daftar tugas. Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(Fore.RED + f"❌ Kesalahan saat mengambil daftar tugas: {e}")

# Fungsi untuk menjalankan tugas berdasarkan taskIdx
def run_task(authorization, cookie, task_idx):
    """Menjalankan tugas berdasarkan taskIdx."""
    headers = {
        "authorization": authorization,
        "cookie": cookie,
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "content-type": "application/json"
    }

    payload = {"taskIdx": task_idx}
    try:
        print(Fore.YELLOW + f"🔄 Menjalankan tugas dengan taskIdx: {task_idx}...")
        response = requests.post("https://mt.promptale.io/tasks/taskRun", json=payload, headers=headers)
        if response.status_code == 201:
            message = response.json().get("message", "Tidak ada pesan.")
            print(Fore.GREEN + f"✅ Tugas berhasil dijalankan. Pesan: {translate_message(message)}")
        else:
            print(Fore.RED + f"❌ Gagal menjalankan tugas. Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(Fore.RED + f"❌ Kesalahan saat menjalankan tugas: {e}")

# Fungsi untuk menyelesaikan tugas yang sudah dijalankan
def complete_task(authorization, cookie, task_idx):
    """Menandai tugas sebagai selesai jika sudah dijalankan (runStatus: 'S')."""
    headers = {
        "authorization": authorization,
        "cookie": cookie,
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "content-type": "application/json"
    }

    payload = {"taskIdx": task_idx}
    try:
        print(Fore.YELLOW + f"🔄 Menyelesaikan tugas dengan taskIdx: {task_idx}...")
        response = requests.post("https://mt.promptale.io/tasks/taskComplete", json=payload, headers=headers)
        if response.status_code == 201:
            data = response.json().get("data", {})
            message = response.json().get("message", "Tidak ada pesan.")
            translated_message = translate_message(message)
            print(Fore.GREEN + f"✅ Tugas selesai! Pesan: {translated_message}")
            print(Fore.CYAN + f"Point: {data.get('point')}, Boost Point: {data.get('boostPoint')}, APY Point: {data.get('apyPoint')}")
        else:
            print(Fore.RED + f"❌ Gagal menyelesaikan tugas. Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(Fore.RED + f"❌ Kesalahan saat menyelesaikan tugas: {e}")

# Fungsi untuk cek dan buka telur
def check_and_open_eggs(authorization, cookie):
    """Cek jumlah telur dan buka semua telur yang tersedia."""
    headers = {
        "authorization": authorization,
        "cookie": cookie,
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    try:
        # Cek jumlah telur
        print(Fore.YELLOW + "🔄 Memeriksa jumlah telur...")
        response = requests.get("https://mt.promptale.io/rewards/myEggCount", headers=headers)
        if response.status_code == 200:
            egg_count = response.json().get("data", 0)
            message = response.json().get("message", "Tidak ada pesan.")
            print(Fore.CYAN + f"Pesan: {translate_message(message)}")
            print(Fore.GREEN + f"✅ Telur ditemukan: {egg_count}")

            # Buka semua telur yang tersedia
            for i in range(egg_count):
                print(Fore.YELLOW + f"🔄 Membuka telur ke-{i + 1}...")
                open_response = requests.post("https://mt.promptale.io/rewards/myEggOpen", headers=headers)
                if open_response.status_code == 201:
                    data = open_response.json().get("data", {})
                    message = open_response.json().get("message", "Tidak ada pesan.")
                    translated_message = translate_message(message)
                    print(Fore.GREEN + f"✅ Telur dibuka! Pesan: {translated_message}")
                    print(Fore.CYAN + f"Hasil: {data.get('codeDesc')} ({data.get('getPoint')} Poin)")
                else:
                    print(Fore.RED + f"❌ Gagal membuka telur ke-{i + 1}. Status Code: {open_response.status_code}")
        else:
            print(Fore.RED + f"❌ Gagal memeriksa jumlah telur. Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(Fore.RED + f"❌ Terjadi kesalahan saat memproses telur: {e}")

# Fungsi utama untuk memproses absensi, data poin, dan tugas
def perform_task(authorization, cookie):
    """Mengelola absensi, mengambil poin, menjalankan tugas, dan membuka telur."""
    headers = {
        "authorization": authorization,
        "cookie": cookie,
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    try:
        # Cek apakah sudah absensi hari ini
        print(Fore.YELLOW + "🔄 Memeriksa status absensi...")
        response = requests.get("https://mt.promptale.io/tasks/isAttendanceToday", headers=headers)
        if response.status_code == 200:
            message = response.json().get("message", "Tidak ada pesan.")
            print(Fore.GREEN + f"Pesan: {translate_message(message)}")

            if response.json().get("data") is False:
                # Lakukan absensi
                print(Fore.GREEN + "✅ Belum absensi. Melakukan absensi...")
                attend_response = requests.post("https://mt.promptale.io/tasks/attend", headers=headers)
                if attend_response.status_code == 201:
                    print(Fore.GREEN + "✅ Absensi berhasil!")
                    response_message = attend_response.json().get("message", "Tidak ada pesan.")
                    print(Fore.CYAN + f"Pesan: {translate_message(response_message)}")
                else:
                    print(Fore.RED + "❌ Gagal melakukan absensi!")
        else:
            print(Fore.RED + "❌ Gagal memeriksa status absensi.")

        # Ambil data poin pengguna
        print(Fore.YELLOW + "🔄 Mengambil data poin pengguna...")
        point_response = requests.get("https://mt.promptale.io/main/mypoint", headers=headers)
        if point_response.status_code == 200:
            user_data = point_response.json().get("data", {})
            print(Fore.CYAN + f"Poin: {user_data.get('point')}, Telur: {user_data.get('egg')}")

            # Jika ada telur, buka semua telur
            if user_data.get('egg', 0) > 0:
                check_and_open_eggs(authorization, cookie)

        # Ambil daftar tugas dan jalankan/selesaikan tugas
        fetch_tasks(authorization, cookie)

    except requests.RequestException as e:
        print(Fore.RED + f"❌ Terjadi kesalahan saat mengakses API: {e}")

# Fungsi hitung mundur 1 hari
def countdown_timer():
    end_time = datetime.now() + timedelta(days=1)
    print(Fore.BLUE + "🔄 Hitung mundur 1 hari dimulai...")
    while datetime.now() < end_time:
        remaining = end_time - datetime.now()
        print(Fore.YELLOW + f"Sisa waktu: {remaining}", end="\r")
        time.sleep(1)
    print(Fore.GREEN + "\n🔄 Mengulang proses...")

# Fungsi utama untuk menjalankan semua akun
def main():
    print_welcome_message()
    accounts = load_accounts()
    if not accounts:
        print(Fore.RED + "Tidak ada akun yang ditemukan di data.txt!")
        return

    print(Fore.BLUE + f"🔄 Total Akun: {len(accounts)}")

    for idx, (auth, cookie) in enumerate(accounts, start=1):
        print(Fore.BLUE + f"\n🔄 Memproses akun {idx}/{len(accounts)}...")
        try:
            # Gunakan langsung auth dan cookie
            perform_task(auth, cookie)
        except Exception as e:
            print(Fore.RED + f"❌ Kesalahan saat memproses akun {idx}: {e}")

        print(Fore.YELLOW + "⏳ Menunggu 5 detik sebelum akun berikutnya...\n")
        time.sleep(5)

    countdown_timer()
    main()  # Mulai ulang proses setelah 1 hari

if __name__ == "__main__":
    main()
