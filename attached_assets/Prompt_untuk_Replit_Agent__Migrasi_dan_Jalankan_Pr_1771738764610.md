# Prompt untuk Replit Agent: Migrasi dan Jalankan Proyek ai-manus

**Tujuan Utama:** Migrasikan dan jalankan proyek `ai-manus` dari GitHub ([https://github.com/Simpleyyt/ai-manus](https://github.com/Simpleyyt/ai-manus)) di lingkungan Replit. Perhatikan bahwa fungsionalitas sandbox berbasis Docker perlu disesuaikan karena keterbatasan Replit.

## Langkah-langkah Migrasi dan Deployment:

### 1. Kloning Repositori

Kloning repositori `ai-manus` ke lingkungan Replit Anda:

```bash
git clone https://github.com/Simpleyyt/ai-manus
cd ai-manus
```

### 2. Konfigurasi Lingkungan (.env)

Buat file `.env` di direktori root proyek (`ai-manus/`) dengan menyalin dari `.env.example`. Sesuaikan nilai-nilai berikut:

```bash
cp .env.example .env
```

Edit file `.env` dan isi variabel-variabel penting:

*   **API_KEY**: Kunci API untuk layanan LLM Anda (misalnya, OpenAI). Ganti `sk-xxxx` dengan kunci API Anda yang sebenarnya.
*   **API_BASE**: Jika Anda menggunakan LLM lokal atau proxy, sesuaikan. Untuk OpenAI, biarkan default atau sesuaikan jika perlu.
*   **MODEL_NAME**: Model LLM yang ingin Anda gunakan (misalnya, `gpt-4o`, `gemini-pro`).
*   **MONGODB_URI**: Ganti dengan URI koneksi MongoDB Anda. Replit tidak menyediakan MongoDB bawaan, jadi Anda perlu menggunakan layanan eksternal seperti MongoDB Atlas (tersedia tingkat gratis). Contoh: `mongodb+srv://<username>:<password>@<cluster-url>/manus?retryWrites=true&w=majority`
*   **REDIS_HOST**: Ganti dengan host Redis Anda. Replit tidak menyediakan Redis bawaan, jadi Anda perlu menggunakan layanan eksternal seperti Redis Labs (tersedia tingkat gratis). Contoh: `your-redis-host.replit.app` atau dari penyedia eksternal.
*   **REDIS_PORT**: Port Redis Anda.
*   **REDIS_PASSWORD**: Kata sandi Redis Anda.
*   **SANDBOX_ADDRESS**: Karena sandbox akan berjalan di lingkungan Replit yang sama dengan backend, atur ini ke alamat backend Anda. Jika backend berjalan di `localhost:8000`, maka `http://localhost:8000`.
*   **JWT_SECRET_KEY**: Ganti dengan string acak yang kuat untuk keamanan.
*   Variabel lain dapat disesuaikan sesuai kebutuhan Anda.

### 3. Modifikasi Implementasi Sandbox (Backend)

Karena Replit tidak mendukung Docker-in-Docker, kita perlu memodifikasi cara backend berinteraksi dengan sandbox. Kita akan mengganti panggilan Docker SDK dengan eksekusi perintah shell langsung menggunakan modul `subprocess` Python. **Perlu diingat bahwa ini akan menghilangkan isolasi Docker dan fitur-fitur canggih seperti VNC/Chrome DevTools Protocol yang disediakan oleh sandbox asli.**

Navigasi ke direktori `backend/app/infrastructure/external/sandbox/`.

Edit file `docker_sandbox.py` (`ai-manus/backend/app/infrastructure/external/sandbox/docker_sandbox.py`) dan lakukan perubahan berikut:

1.  **Hapus atau komentari impor dan inisialisasi Docker SDK.**
    Cari baris seperti `import docker` dan `docker_client = docker.from_env()`. Ganti dengan inisialisasi `subprocess` atau sesuaikan kelas `DockerSandbox` agar tidak menggunakan Docker.

2.  **Ganti `client.containers.run()` dengan `subprocess.Popen` atau `subprocess.run`:**
    Fungsi `_create_task` dan metode lain yang membuat atau menjalankan kontainer Docker perlu diubah untuk langsung menjalankan perintah di shell Replit. Anda mungkin perlu membuat kelas `Sandbox` baru atau memodifikasi `DockerSandbox` agar metode seperti `exec_shell_command`, `read_file`, `write_file`, dll., menggunakan `subprocess` untuk berinteraksi dengan sistem file dan shell Replit.

    **Contoh modifikasi untuk `exec_shell_command` (ini adalah contoh sederhana dan mungkin memerlukan penyesuaian lebih lanjut):**

    ```python
    import subprocess
    import os
    import asyncio

    # ... (bagian lain dari file)

    class DockerSandbox:
        def __init__(self, container_name: str = None):
            self.container_name = container_name if container_name else f"replit-sandbox-{os.urandom(4).hex()}"
            self.process = None # Untuk menyimpan proses shell yang sedang berjalan
            self.base_url = "http://localhost:8000" # Sesuaikan jika backend berjalan di port lain

        async def _run_command(self, command: str, exec_dir: str = None):
            # Ini adalah implementasi yang sangat disederhanakan.
            # Anda mungkin perlu mengelola stdin/stdout/stderr secara lebih canggih
            # untuk mendukung interaksi real-time seperti di sandbox asli.
            try:
                if exec_dir and not os.path.exists(exec_dir):
                    os.makedirs(exec_dir)
                
                # Jalankan perintah di shell Replit
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=exec_dir if exec_dir else os.getcwd()
                )
                stdout, stderr = await process.communicate()
                
                return {
                    "returncode": process.returncode,
                    "stdout": stdout.decode().strip(),
                    "stderr": stderr.decode().strip()
                }
            except Exception as e:
                return {"returncode": 1, "stdout": "", "stderr": str(e)}

        async def exec_shell_command(self, command: str, exec_dir: str = None) -> Dict[str, Any]:
            result = await self._run_command(command, exec_dir)
            return {
                "success": result["returncode"] == 0,
                "message": "Command executed",
                "data": {
                    "session_id": self.container_name,
                    "command": command,
                    "output": result["stdout"] + result["stderr"],
                    "status": "completed" if result["returncode"] == 0 else "failed",
                    "returncode": result["returncode"]
                }
            }

        async def read_file(self, file_path: str, sudo: bool = False) -> Dict[str, Any]:
            command = f"cat {file_path}"
            if sudo: command = f"sudo {command}"
            result = await self._run_command(command)
            return {
                "success": result["returncode"] == 0,
                "message": "File read successfully",
                "data": {"content": result["stdout"], "file": file_path}
            }

        async def write_file(self, file_path: str, content: str, append: bool = False, sudo: bool = False) -> Dict[str, Any]:
            mode = ">>" if append else ">"
            command = f"echo -e '{content}' {mode} {file_path}"
            if sudo: command = f"sudo {command}"
            result = await self._run_command(command)
            return {
                "success": result["returncode"] == 0,
                "message": "File written successfully",
                "data": {"file": file_path}
            }

        # Implementasikan metode lain seperti `view_shell_session`, `wait_for_process`, `write_input`, `terminate_process`
        # dan fungsionalitas browser/VNC menggunakan `subprocess` atau dengan menonaktifkannya jika tidak penting.
        # Untuk browser, Anda mungkin perlu menginstal Chromium di Replit dan menjalankannya sebagai proses terpisah
        # atau menggunakan Playwright secara langsung jika Replit mendukungnya.

        # Metode lain yang terkait dengan Docker (seperti get_container_ip, dll.) perlu dihapus atau disesuaikan.
    ```

### 4. Instalasi Dependensi

#### Backend (Python)

Navigasi ke direktori `ai-manus/backend`:

```bash
cd backend
```

Buat virtual environment dan instal dependensi:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Sandbox (Python)

Navigasi ke direktori `ai-manus/sandbox`:

```bash
cd ../sandbox
```

Buat virtual environment dan instal dependensi:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Frontend (Node.js)

Navigasi ke direktori `ai-manus/frontend`:

```bash
cd ../frontend
```

Instal dependensi Node.js:

```bash
npm install
```

### 5. Jalankan Aplikasi

#### Backend (Python)

Kembali ke direktori `ai-manus/backend` dan jalankan server FastAPI:

```bash
cd ../backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Sandbox (Python)

Jika Anda telah memodifikasi `docker_sandbox.py` untuk berjalan sebagai proses terpisah atau sebagai bagian dari backend, pastikan ia berjalan. Dalam skenario Replit, idealnya fungsionalitas sandbox akan diintegrasikan langsung ke dalam backend atau dijalankan sebagai proses Python terpisah yang diakses oleh backend.

#### Frontend (Node.js)

Kembali ke direktori `ai-manus/frontend` dan jalankan server pengembangan Vite:

```bash
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Pastikan port 8000 (backend) dan 5173 (frontend) terekspos di Replit Anda.

### Catatan Penting:

*   **Keamanan Sandbox:** Mengganti Docker dengan `subprocess` akan mengurangi isolasi keamanan. Berhati-hatilah saat menjalankan kode yang tidak tepercaya.
*   **Fungsionalitas Browser:** Fungsionalitas browser yang mengandalkan Chrome DevTools Protocol atau VNC mungkin tidak berfungsi sepenuhnya tanpa lingkungan Docker yang tepat. Anda mungkin perlu menginstal Chromium di Replit dan mengkonfigurasi Playwright secara manual jika fitur ini penting.
*   **Replit DB:** Jika Anda ingin menggunakan Replit DB, Anda perlu mengintegrasikan SDK Replit DB ke dalam kode backend untuk menggantikan MongoDB atau Redis untuk sesi dan data lainnya. Ini akan memerlukan perubahan kode yang signifikan.

Dengan prompt ini, Replit Agent harus memiliki panduan yang cukup jelas untuk memulai migrasi dan menjalankan proyek `ai-manus` di Replit, dengan pemahaman tentang batasan dan penyesuaian yang diperlukan.
