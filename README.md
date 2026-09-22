# Community OSINT & Intelligence Engine (`community_osint.py`)

Alat investigasi OSINT (*Open Source Intelligence*) otomatis berbasis Python + **Gemini AI Reasoning Engine** yang dioptimalkan khusus untuk **Pemetaan Ekosistem B2B, Sosmed Multi-Handle, Proyek PIC, Agenda Event Mendatang, dan Komunitas Sejenis di Daerah** dari file Excel/CSV.

---

## 🎯 Fitur & Alur Kerja Utama

1. **Hybrid Architecture (Web Scraping + Gemini AI Reasoning Engine):**
   - Mengumpulkan data web & media sosial mentah dari Google Search.
   - Menggunakan **Gemini Flash (Free Tier)** untuk memilah konteks, menyaring *noise* (seperti Paguyuban beasiswa kampus, artikel kadaluarsa, atau direktori palsu) sehingga output 100% kontekstual dan akurat.
2. **Format Numbering Standar (`1., 2., 3.`):**
   - Seluruh nilai multi-item dalam satu kolom otomatis diformat dalam daftar bernomor rapi per baris (bukan koma panjang).
3. **Multi-Handle Social Media Extraction:**
   - Menangkap seluruh kanal resmi yang relevan (akun tim utama, divisi balap/rebranding, sub-brand, website, dan LinkedIn) lengkap dengan kutipan *bio quote*.
4. **Verifikasi Tanggal Event Mendatang (2026/2027):**
   - Dilengkapi validasi *timestamp* URL ketat untuk mencegah manipulasi artikel lampau (2015–2025). Hanya menampilkan agenda aktif dengan tanggal spesifik dan tautan sumber valid.
5. **Multi-Project & Inisiatif PIC:**
   - Melacak portofolio komunitas/bisnis lain yang dikelola PIC yang sama lengkap dengan kategori dan tautan/@handle.
6. **Peer / Lookalike Communities Selevel di Wilayah:**
   - Menyajikan 3–5 kompetitor/mitra sejenis di kota terkait dengan `@handle` Instagram atau tautan resmi.
7. **Pembersihan Otomatis Data Internal:**
   - Deskripsi bertipe *"Group Order"* atau *"Group Order Pekerja"* otomatis diabaikan dari pencarian deskripsi agar tidak mengotori kueri intelijen.

---

## 📊 Struktur Kolom Output Excel (`*_result.xlsx`)

File output mempertahankan **seluruh kolom input asli di bagian depan** dan menambahkan 5 kolom intelijen dengan *styling* header Navy (`#1F4E78`):

| Kolom Intelijen | Format Output & Penjelasan |
| :--- | :--- |
| **Wilayah Terdeteksi** | Kota/Kabupaten dan Provinsi (contoh: *Jakarta Selatan, DKI Jakarta*) |
| **Sosmed Resmi Komunitas** | `1. IG: https://... ("bio quote")` <br> `2. Web Resmi: https://...` |
| **Komunitas Lain Kelolaan PIC** | `1. Nama Inisiatif (https://link/@handle) (Kategori/Niche)` |
| **Agenda / Event Terdekat** | `1. Nama Event 2026 (Bulan/Tanggal 2026) - Sumber: https://...` |
| **Komunitas Sejenis di Daerah** | `1. Nama Brand/Komunitas (@handle_ig atau URL)` |

---

## 🛠️ Cara Penggunaan

### 1. Persyaratan Sistem & Instalasi
* Python 3.10+ (disarankan 3.11 / 3.12)
* Google Gemini API Key (Gratis di Google AI Studio)

```bash
git clone https://github.com/temonwkwk/community-osint-lookup.git
cd community-osint-lookup
pip install -r requirements.txt
```

Setel API Key di environment atau di file `~/.hermes/.env`:
```bash
export GOOGLE_API_KEY="AIzaSy..."
```

---

### 2. Eksekusi CLI

**Mode Standar (Pencarian Langsung):**
```bash
python community_osint.py data_komunitas.xlsx
```

**Mode Cache (Sangat Cepat untuk Batch Ratusan Data):**
```bash
# 1. Dump seluruh kueri yang dibutuhkan
python community_osint.py data_komunitas.xlsx --search-cache cache.json --dump-queries queries.json --no-live-search

# 2. Jalankan analisis dengan cache
python community_osint.py data_komunitas.xlsx --search-cache cache.json
```

---

## 🔒 Keamanan & Privasi
- Seluruh data pribadi, nomor kontak, dan file target diamankan otomatis oleh `.gitignore`.
- API Key tersimpan secara lokal dan aman.

---

## 📄 Lisensi
Didistribusikan di bawah Lisensi [MIT](LICENSE).
