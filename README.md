# Community OSINT & Multi-Community Intelligence (`community_osint.py`)

Tools otomatisasi investigasi OSINT (*Open Source Intelligence*) untuk memetakan **ekosistem komunitas, jangkauan daerah/wilayah, profil PIC, serta melacak komunitas lain yang dikelola oleh PIC yang sama** berdasarkan data nama komunitas, deskripsi, dan kontak PIC dalam jumlah banyak (*bulk processing* via file Excel/CSV).

---

## 🚀 Fitur Utama

1. **Penelusuran Media Sosial & Web Resmi Komunitas**:
   - Mencari akun resmi Instagram, Facebook Group/Page, TikTok, Threads, Linktree, dan Website resmi komunitas (beserta jumlah pengikut / anggota).
2. **Deteksi Otomatis Daerah / Wilayah Komunitas**:
   - Mengekstrak kota/wilayah cakupan komunitas (contoh: *Jakarta, Bandung, Yogyakarta, Surabaya, Denpasar, Medan, dll.* atau *Cakupan Nasional*) dari bio profil dan deskripsi.
3. **Multi-Community Mapping (Komunitas Lain Milik PIC)**:
   - Mengidentifikasi inisiatif, project sosial, yayasan, atau komunitas lain yang didirikan, dipimpin, atau diinisiasi oleh PIC yang sama.
4. **Pemetaan Komunitas Sejenis di Daerah Tersebut (*Peer Communities*)**:
   - Mencari 3–5 komunitas serupa di kota yang sama berdasarkan topik/niche komunitas (misal: *lingkungan, kopi, lari, otomotif, tech, parenting*) untuk kebutuhan kolaborasi atau ekspansi.
5. **Verifikasi Kontak PIC**:
   - Menyatukan nomor HP/WhatsApp dan status email terdaftar via Holehe (Office365, Spotify, Twitter/X, dll).
6. **Output Terstruktur Tanpa Merusak Kolom Asli**:
   - Menghasilkan file baru `<input>_result.xlsx` dengan satu kolom ringkasan `Community Intelligence`.

---

## 📋 Format File Input

File input dapat berupa `.xlsx` atau `.csv`. Header kolom akan dideteksi secara otomatis (case-insensitive):
- **Nama Komunitas**: `Nama Komunitas`, `Komunitas`, `Community`
- **Deskripsi Komunitas**: `Deskripsi Komunitas`, `Deskripsi`, `Kegiatan`, `About`
- **Nama PIC**: `Nama PIC Komunitas`, `PIC`, `Ketua`, `Founder`, `Leader`
- **Email PIC**: `Email PIC`, `Email`, `Mail`
- **Nomor HP PIC**: `Nomor HP PIC`, `No HP`, `Telepon`, `WhatsApp`

Contoh:

| Nama Komunitas | Deskripsi Komunitas | Nama PIC Komunitas | Email PIC | Nomor HP PIC |
| :--- | :--- | :--- | :--- | :--- |
| Example Tech Community | Komunitas praktisi teknologi dan arsitektur cloud di Jakarta | PIC Example A | pic_a@example.com | 081200000001 |
| Example Green Movement | Gerakan relawan bank sampah dan aksi bersih lingkungan di Bandung | PIC Example B | pic_b@example.com | 085700000002 |
| Example Runners Club | Komunitas lari sehat dan gathering pelari se-Yogyakarta | PIC Example C | pic_c@example.com | 081300000003 |

---

## 🛠️ Cara Penggunaan

Pastikan menggunakan Python 3.10+ (disarankan Python 3.12).

### 1. Instalasi
```bash
# Clone repository
git clone https://github.com/temonwkwk/community-osint-lookup.git
cd community-osint-lookup

# Install dependency
pip install -r requirements.txt
```

---

### 2. Mode Standar (Live Search)
```bash
python community_osint.py input.xlsx
```
Hasil akan disimpan otomatis ke `input_result.xlsx`.

---

### 3. Mode 2-Pass Cache (Direkomendasikan untuk Data Besar)

Untuk menghindari rate-limit mesin pencari saat memproses ratusan komunitas:

**Langkah 1 — Dump Daftar Query:**
```bash
python community_osint.py input.xlsx --search-cache cache.json --dump-queries queries.json --no-live-search --skip-holehe
```

**Langkah 2 — Isi Cache (`cache.json`):**
Ambil data hasil pencarian ke `cache.json` menggunakan search engine / API.

**Langkah 3 — Eksekusi Analisis Lengkap:**
```bash
python community_osint.py input.xlsx --search-cache cache.json
```

---

## 📊 Format Output Kolom `Community Intelligence`

```text
Sosmed Komunitas: IG: https://www.instagram.com/example_community/ (5.2k followers); FB Group: https://facebook.com/groups/example_comm; Linktree: https://linktr.ee/example_community
Daerah / Wilayah: Jakarta Pusat, DKI Jakarta
Komunitas Lain Kelolaan PIC: Example Developer Forum, Yayasan Inovasi Digital
Komunitas Sejenis di Jakarta Pusat: Jakarta Tech Group, Python Developers Forum, Cloud & Code Community
Profil PIC: Nama: PIC Example A | No HP/WA: 081200000001 | Email: pic_a@example.com | Platform Aktif: office365, spotify, twitter
```

---

## ⚙️ Opsi Command Line

```text
usage: community_osint.py [-h] [--sheet SHEET] [--search-cache SEARCH_CACHE]
                          [--dump-queries DUMP_QUERIES] [--no-live-search]
                          [--skip-holehe] [--delay DELAY] [--limit LIMIT]
                          input

positional arguments:
  input                 File input (.xlsx atau .csv)

options:
  -h, --help            Tampilkan bantuan
  --sheet SHEET         Nama sheet pada file Excel
  --search-cache PATH   Gunakan cache file JSON untuk hasil pencarian
  --dump-queries PATH   Simpan query pencarian ke file JSON
  --no-live-search      Nonaktifkan live HTTP search
  --skip-holehe         Lewati pengecekan email PIC dengan Holehe
  --delay DELAY         Delay jeda antar request (detik)
  --limit LIMIT         Batasi jumlah baris yang diproses
```

---

## 🔒 Privasi & Keamanan Data

- Repository ini **tidak menyimpan data pribadi atau hasil investigasi nyata**.
- Seluruh file data (`target*.xlsx`, `cache.json`, `queries.json`) otomatis diabaikan oleh `.gitignore`.

---

## 📄 Lisensi

Didistribusikan di bawah Lisensi [MIT](LICENSE).
