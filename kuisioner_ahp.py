#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import json

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="Kuesioner AHP Kerawanan Banjir Morotai",
    page_icon="🌊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Parameter
P = ['Kemiringan lereng', 'Elevasi', 'Jenis tanah', 'Tutupan lahan', 'Jarak dari sungai']
D = [
    'Sudut kemiringan lahan (dari DEM). Lereng landai cenderung lebih rawan tergenang.',
    'Ketinggian lahan di atas permukaan laut (dari DEM). Elevasi rendah cenderung lebih rawan.',
    'Karakteristik tanah yang memengaruhi infiltrasi dan permeabilitas. Infiltrasi rendah cenderung lebih rawan.',
    'Jenis penutup permukaan yang memengaruhi limpasan. Permukaan terbangun atau terbuka cenderung lebih rawan dibanding vegetasi rapat.',
    'Jarak horizontal ke alur sungai. Semakin dekat sungai cenderung lebih rawan.'
]
N = len(P)
RI = 1.12  # Random Index untuk n=5

# Buat pasangan perbandingan
pairs = [(i, j) for i in range(N) for j in range(i + 1, N)]

# Label skala
def lab(k):
    labels = {
        1: 'sama penting',
        3: 'sedikit lebih penting',
        5: 'jelas lebih penting',
        7: 'sangat jelas lebih penting',
        9: 'mutlak lebih penting'
    }
    return labels.get(k, 'nilai tengah')

# ==================== FUNGSI AHP ====================
def parse_value(v):
    if v == '1':
        return 1.0
    k = int(v[1:])
    return float(k) if v[0] == 'A' else 1.0 / k

def ahp(vals):
    M = np.ones((N, N))
    for idx, (i, j) in enumerate(pairs):
        x = parse_value(vals[idx])
        M[i, j] = x
        M[j, i] = 1.0 / x

    # Eigenvector approximation (power method)
    w = np.ones(N) / N
    for _ in range(200):
        y = M @ w
        w = y / y.sum()

    # Lambda max, CI, CR
    y = M @ w
    lambda_max = np.mean(y / w)
    ci = (lambda_max - N) / (N - 1)
    cr = ci / RI
    return w, lambda_max, ci, cr

# ==================== UI ====================
st.title("Kuesioner Pakar (AHP): Pembobotan Parameter Kerawanan Banjir di Pulau Morotai")
st.caption(
    "Penelitian tugas mata kuliah Analisis Geospasial, S1 Geofisika. "
    "Penilaian Bapak/Ibu dipakai untuk menentukan bobot relatif lima parameter dalam analisis weighted overlay. "
    "Tidak ada jawaban benar atau salah. Data hanya untuk keperluan akademik."
)

# Tabel parameter
st.subheader("Parameter yang dinilai")
df_param = pd.DataFrame({
    "No": range(1, N + 1),
    "Parameter": P,
    "Penjelasan": D
})
st.dataframe(df_param, hide_index=True, use_container_width=True)

with st.expander("Cara mengisi dan skala penilaian"):
    st.markdown("""
    Untuk setiap pasangan, pilih parameter mana yang lebih berpengaruh terhadap kerawanan banjir di Pulau Morotai 
    dan seberapa besar perbedaannya, lalu tuliskan alasan singkat.

    **Skala:**
    - **1** = sama penting  
    - **3** = sedikit lebih penting  
    - **5** = jelas lebih penting  
    - **7** = sangat jelas lebih penting  
    - **9** = mutlak lebih penting  
    - **2, 4, 6, 8** = nilai tengah

    **Cakupan penelitian:** banjir akibat hujan dan luapan sungai (genangan pasang laut tidak termasuk).
    """)

# Identitas
st.subheader("Identitas responden")
nama = st.text_input("Nama dan gelar *")
institusi = st.text_input("Institusi dan jabatan")
keahlian = st.text_input("Bidang keahlian")

# Pasangan perbandingan
st.subheader("Perbandingan Berpasangan")
vals = []
alasan = []

for n, (i, j) in enumerate(pairs):
    with st.container(border=True):
        st.markdown(f"**Pasangan {n+1} dari {len(pairs)}**")
        st.markdown(f"<span style='background:#1f6f8b;color:white;padding:2px 8px;border-radius:6px;font-size:0.8rem'>A</span> **{P[i]}** &nbsp; *lawan* &nbsp; <span style='background:#1f6f8b;color:white;padding:2px 8px;border-radius:6px;font-size:0.8rem'>B</span> **{P[j]}**", unsafe_allow_html=True)

        options = ["Pilih penilaian..."]
        # A lebih penting
        for k in range(9, 1, -1):
            options.append(f"{P[i]} {lab(k)} dibanding {P[j]} ({k})")
        options.append("Kedua parameter sama penting (1)")
        # B lebih penting
        for k in range(2, 10):
            options.append(f"{P[j]} {lab(k)} dibanding {P[i]} ({k})")

        pilihan = st.selectbox(
            "Mana yang lebih berpengaruh terhadap kerawanan banjir?",
            options,
            key=f"s{n}"
        )
        alasan_text = st.text_area(
            "Alasan",
            placeholder="Dasar pertimbangan: pengalaman lapangan, teori, atau kondisi Morotai",
            key=f"r{n}",
            height=80
        )

        # Mapping pilihan ke kode
        if pilihan == "Pilih penilaian...":
            vals.append(None)
        elif "sama penting" in pilihan:
            vals.append("1")
        else:
            # ekstrak nilai dan siapa yang lebih penting
            if pilihan.startswith(P[i]):
                # A lebih penting
                angka = int(pilihan.split("(")[-1].replace(")", ""))
                vals.append(f"A{angka}")
            else:
                angka = int(pilihan.split("(")[-1].replace(")", ""))
                vals.append(f"B{angka}")

        alasan.append(alasan_text)

# Catatan tambahan
extra = st.text_area(
    "Catatan atau parameter lain yang menurut Bapak/Ibu penting (opsional)",
    height=100
)

# Tombol aksi
col1, col2 = st.columns(2)
with col1:
    check = st.button("Periksa jawaban dan konsistensi", type="primary", use_container_width=True)
with col2:
    send = st.button("Kirim / Unduh jawaban", use_container_width=True)

# Hasil perhitungan
if check or send:
    missing = []
    if not nama.strip():
        st.error("Mohon isi nama responden.")
    else:
        for n, v in enumerate(vals):
            if v is None or not alasan[n].strip():
                missing.append(n + 1)

        if missing:
            st.error(f"Pilihan dan alasan belum lengkap pada pasangan: {', '.join(map(str, missing))}.")
        else:
            # Hitung AHP
            w, lm, ci, cr = ahp(vals)
            ok = cr < 0.1

            if ok:
                st.success(f"Penilaian konsisten (CR = {cr:.3f}). Silakan unduh/kirim jawaban.")
            else:
                st.warning(
                    f"Penilaian kurang konsisten (CR = {cr:.3f}, batas 0,10). "
                    "Mohon tinjau kembali beberapa perbandingan, atau tetap kirim bila sudah yakin."
                )

            # Tampilkan bobot
            df_bobot = pd.DataFrame({
                "Parameter": P,
                "Bobot (%)": (w * 100).round(1)
            }).sort_values("Bobot (%)", ascending=False)
            st.dataframe(df_bobot, hide_index=True, use_container_width=True)

            # Siapkan data untuk unduh
            jawaban_detail = []
            for n, (i, j) in enumerate(pairs):
                v = vals[n]
                if v == "1":
                    txt = "Sama penting (1)"
                else:
                    who = P[i] if v[0] == "A" else P[j]
                    txt = f"{who} lebih penting, nilai {v[1:]}"
                jawaban_detail.append({
                    "pasangan": f"{P[i]} vs {P[j]}",
                    "pilihan": txt,
                    "nilai": parse_value(v),
                    "alasan": alasan[n]
                })

            data = {
                "nama": nama.strip(),
                "institusi": institusi.strip(),
                "keahlian": keahlian.strip(),
                "catatan": extra.strip(),
                "parameter": P,
                "jawaban": jawaban_detail,
                "bobot": {p: float(round(ww * 100, 1)) for p, ww in zip(P, w)},
                "lambda_max": float(lm),
                "CI": float(ci),
                "CR": float(cr),
                "waktu": datetime.now().isoformat()
            }

            # Ringkasan teks
            ringkasan = f"""KUESIONER AHP KERAWANAN BANJIR MOROTAI
Nama: {data['nama']}
Institusi: {data['institusi']}
Keahlian: {data['keahlian']}

"""
            for n, (i, j) in enumerate(pairs):
                v = vals[n]
                if v == "1":
                    txt = "Sama penting (1)"
                else:
                    who = P[i] if v[0] == "A" else P[j]
                    txt = f"{who} lebih penting, nilai {v[1:]}"
                ringkasan += f"{n+1}. {P[i]} vs {P[j]}: {txt}\n   Alasan: {alasan[n]}\n"

            if extra.strip():
                ringkasan += f"\nCatatan: {extra.strip()}\n"

            ringkasan += f"\nBobot: {'; '.join([f'{p} {w*100:.1f}%' for p, w in zip(P, w)])}\n"
            ringkasan += f"CR: {cr:.3f}\n"

            # Tombol unduh
            st.download_button(
                label="Unduh jawaban (JSON)",
                data=json.dumps(data, ensure_ascii=False, indent=2),
                file_name=f"AHP_Morotai_{nama.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
            st.download_button(
                label="Unduh ringkasan (TXT)",
                data=ringkasan,
                file_name=f"AHP_Morotai_{nama.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

            st.info("Anda juga bisa menyalin ringkasan di bawah ini dan mengirimkannya via email/WhatsApp.")
            st.code(ringkasan, language=None)

