# Community OSINT & Multi-Community Intelligence (`community_osint.py`)

Tools otomatisasi investigasi OSINT (*Open Source Intelligence*) berbasis Python yang dioptimalkan khusus untuk **Pemetaan Ekosistem Komunitas, Multi-Komunitas PIC, Penetrasi Chapter Regional, dan Prospek Komunitas Sejenis di Daerah** berdasarkan data Excel/CSV.

---

## 🎯 Fitur & Alur Utama (Outreach & Insurance B2B Focused)

1. **Pemisahan Kolom Excel Terstruktur**:
   - Hasil investigasi dipecah menjadi kolom-kolom rapi terpisah yang mudah di-*filter*, di-*sort*, dan dianalisis oleh tim *sales/outreach*.
2. **Penelusuran Media Sosial Resmi Komunitas (Fokus Outreach)**:
   - Mencari akun Instagram resmi, Facebook Page/Profil resmi, TikTok, Threads, Linktree, dan Website resmi komunitas.
3. **Deteksi Wilayah Terstruktur (`Kota & Provinsi`)**:
   - Menggunakan database hierarki geografis 500+ Kota/Kabupaten ke 38 Provinsi di Indonesia untuk menetapkan domisili komunitas secara presisi.
4. **Multi-Community Portfolio PIC**:
   - Melacak inisiatif, project sosial, yayasan, atau komunitas lain yang dikelola oleh PIC yang sama untuk peluang *cross-selling*.
5. **Pemetaan Induk Organisasi & Chapter Regional (*Federation / Chapter Mapping*)**:
   - Mendeteksi afiliasi induk paguyuban (misal: Paguyuban Honda Jawa Barat, Ikatan Motor Indonesia) dan chapter kota tetangga.
6. **Pelacakan Agenda & Event Terdekat (*Outreach Timing Trigger*)**:
   - Memindai agenda aktif komunitas (seperti *Anniversary, Touring, Gathering, Turnamen, Fun Run, Baksos, Expo*) agar penawaran asuransi event masuk tepat waktu.
7. **Pencarian Komunitas Sejenis di Daerah (*Lookalike Peer Communities*)**:
   - Menghasilkan 3–6 nama komunitas serupa di kota yang sama **wajib lengkap dengan akun Instagram (`@handle`) dan kontak bio**.
8. **Validasi Email PIC Cepat (*Fast Async Socials Only*)**:
   - Mengecek ketersediaan email PIC di platform sosial media utama (Twitter/X, Instagram, Discord, Pinterest, Strava) dalam waktu ~1–2 detik.

---

## 📋 Format File Input

File input dapat berupa `.xlsx` atau `.csv`. Header kolom otomatis terdeteksi (case-insensitive):
- **Nama Komunitas**: `Nama Komunitas`, `Komunitas`, `Community`
- **Deskripsi Komunitas**: `Deskripsi Komunitas`, `Deskripsi`, `Kegiatan`, `About`
- **Nama PIC**: `Nama PIC Komunitas`, `PIC`, `Ketua`, `Founder`, `Leader`
- **Email PIC**: `Email PIC`, `Email`, `Mail`
- **Nomor HP PIC**: `Nomor HP PIC`, `No HP`, `Telepon`, `WhatsApp`

Contoh:

| Nama Komunitas | Deskripsi Komunitas | Nama PIC Komunitas | Email PIC | Nomor HP PIC |
| :--- | :--- | :--- | :--- | :--- |
| Example Riders Club | Komunitas Motor dan Touring Regional | PIC Example A | pic_a@example.com | 081200000001 |
| Example Tennis Community | Komunitas Tenis dan Sparring Mingguan | PIC Example B | pic_b@example.com | 085700000002 |
| Example Creative EO | Event Organizer dan Festival Musik | PIC Example C | pic_c@example.com | 081300000003 |

---

## 📊 Format Kolom Output Excel (`*_result.xlsx`)

Hasil disimpan otomatis ke `<input>_result.xlsx` dengan kolom terpisah:

| Kolom Hasil | Penjelasan Isi |
| :--- | :--- |
| **Wilayah Terdeteksi** | Kota/Kabupaten dan Provinsi (contoh: *Kuningan, Jawa Barat*) |
| **Sosmed Resmi Komunitas** | Akun resmi IG, FB Page/Profil, Linktree, Web |
| **Komunitas Lain Milik PIC** | Daftar komunitas/yayasan lain yang dikelola PIC yang sama |
| **Jejaring Chapter & Induk** | Induk paguyuban atau chapter regional terhubung |
| **Agenda / Event Terdekat** | Pemicu waktu kontak (contoh: *Anniversary ke-5, Touring Gabungan, Fun Run 2026*) |
| **Komunitas Sejenis di Daerah** | 3–6 komunitas serupa di daerah tersebut beserta akun IG (`@handle`) & WA |

---

## 🛠️ Cara Penggunaan

Pastikan menggunakan Python 3.10+ (disarankan Python 3.12).

### 1. Instalasi
```bash
git clone https://github.com/temonwkwk/community-osint-lookup.git
cd community-osint-lookup
pip install -r requirements.txt
```

---

### 2. Mode Eksekusi Langsung
```bash
python community_osint.py data_komunitas.xlsx
```

---

### 3. Mode 2-Pass Cache (Direkomendasikan untuk Data Ratusan Baris)

**Langkah 1 — Ambil Daftar Query:**
```bash
python community_osint.py data_komunitas.xlsx --search-cache cache.json --dump-queries queries.json --no-live-search --skip-holehe
```

**Langkah 2 — Isi Cache (`cache.json`):**
Ambil hasil pencarian untuk `queries.json` ke dalam `cache.json`.

**Langkah 3 — Eksekusi Analisis Lengkap:**
```bash
python community_osint.py data_komunitas.xlsx --search-cache cache.json
```

---

## 🔒 Privasi & Keamanan Data

- Seluruh data pribadi, nomor kontak, dan file target diamankan otomatis oleh `.gitignore`.
- Tidak ada data yang diunggah ke server pihak ketiga.

---

## 📄 Lisensi

Didistribusikan di bawah Lisensi [MIT](LICENSE).
