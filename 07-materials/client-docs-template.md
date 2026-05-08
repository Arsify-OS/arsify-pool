# Dokumentasi Layanan AI — [NAMA KLIEN]

Selamat datang di sistem AI Assistant untuk [NAMA KLIEN]. Dokumen ini menjelaskan cara menggunakan layanan yang telah kami siapkan.

---

## 1. Cara Akses Workspace

Workspace Anda berada di: **[URL_WORKSPACE_KLIEN]**

Akses menggunakan browser (Chrome/Firefox/Edge) dan login dengan kredensial yang diberikan saat handover:
- Username: [USERNAME]
- Password: [PASSWORD] (segera ganti setelah login pertama)

---

## 2. Cara Berkomunikasi dengan AI

Anda dapat berkomunikasi dengan AI melalui:
1. **Telegram Bot**: @[BOT_USERNAME] — kirim pesan langsung, AI akan merespons
2. **Workspace Chat**: Buka menu "Chat" di workspace
3. **CLI** (untuk tim teknis): SSH ke VPS dan jalankan `hermes -z "pesan Anda"`

**Tips**: 
- Gunakan bahasa Indonesia yang jelas
- Sertakan konteks jika diperlukan (contoh: "Tolong riset pasar *kopi* di Jakarta")
- AI akan selalu lapor sebelum melakukan tindakan berisiko tinggi

---

## 3. Cara Membaca Daily Brief

Daily brief dikirim otomatis setiap hari pukul 08:00 WIB ke Telegram group klien.

Isi daily brief:
- Ringkasan aktivitas AI hari sebelumnya
- Task yang selesai
- Insight pasar terbaru (jika paket Standard/Enterprise)
- Rekomendasi tindakan untuk tim klien

---

## 4. Cara Request Task ke AI

Format request yang baik:
```
[HARI/TANGGAL]
[TARGET/AREA] — contoh: "Riset Pasar", "Analisa Kompetitor"
[DETAIL] — jelaskan apa yang Anda butuhkan
[DEADLINE] — opsional, format: "sebelum Jumat 15:00"
```

Contoh:
```
Senin, 12 Mei 2026
Riset Pasar
Tolong cari tren konsumsi kopi di Jakarta Selatan 2025-2026
Deadline: Rabu 14 Mei 2026
```

---

## 5. Troubleshooting Umum

| Masalah | Solusi |
|---------|--------|
| Telegram bot tidak merespons | Cek koneksi internet, kirim `/start` ke bot |
| Tidak bisa login workspace | Reset password via menu "Lupa Password" atau hubungi support |
| AI memberikan jawaban tidak relevan | Tambahkan konteks lebih lengkap di request |
| Daily brief tidak masuk | Cek apakah bot sudah di-add ke group Telegram klien |

---

## 6. Kontak Support

Jika mengalami masalah yang tidak terselesaikan di atas:
- **Telegram**: @upshalter_support
- **Email**: support@upshalter.com
- **Response Time**: 
  - Paket Starter: 1x24 jam
  - Paket Standard: 12 jam
  - Paket Enterprise: 4 jam (SLA 99.9%)

---

*Dokumen ini dibuat otomatis oleh sistem Upshalter AI Setup.*  
*Tanggal: [TANGGAL_HANDOVER]*
