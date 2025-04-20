import streamlit as st
import pandas as pd
from itertools import count
from collections import defaultdict, deque

# Sayfa yapılandırması
st.set_page_config(page_title="Mükerrerlik Tespiti", layout="wide")

# Başlık
st.title("📊 Kesinti Verisi Mükerrerlik Tespiti")
st.markdown("Excel dosyasını yükleyin. Şebeke Unsuru bazlı zaman çakışmaları tespit edilecektir.")

# 🔽 Şablon indirilebilir bağlantı
try:
    with open("Mükerrerlik Kontrol Şablonu.xlsx", "rb") as f:
        bytes_data = f.read()
        st.download_button(
            label="📥 Mükerrerlik Kontrol Şablonu (Excel)",
            data=bytes_data,
            file_name="Mükerrerlik Kontrol Şablonu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
except FileNotFoundError:
    st.info("📎 Şablon dosyası klasörde bulunamadı. Lütfen geliştiriciye bildirin.")

# 🔹 Excel yükleyici
uploaded_file = st.file_uploader("Excel dosyasını seçin (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Excel'den veri oku
        df = pd.read_excel(uploaded_file, engine="openpyxl", header=2)
        df.columns = df.columns.str.strip().str.replace('"', '')

        # Tarih dönüşümleri
        df["KESINTI BASLANGIC SAATI"] = pd.to_datetime(df["KESINTI BASLANGIC SAATI"], dayfirst=True, errors="coerce")
        df["KESINTI BITIS SAATI"] = pd.to_datetime(df["KESINTI BITIS SAATI"], dayfirst=True, errors="coerce")

        # Şebeke Unsuru bazlı sırala
        df.sort_values(by=["SEBEKE UNSURU", "KESINTI BASLANGIC SAATI"], inplace=True)

        # Mükerrerlik tespiti
        df["DURUM"] = ""
        df["GÜNCELLENMİŞ BİTİŞ"] = pd.NaT

        for unsur, grup in df.groupby("SEBEKE UNSURU"):
            grup = grup.sort_values(by="KESINTI BASLANGIC SAATI")
            indeksler = grup.index.tolist()
            aktif_grup = []

            for idx in indeksler:
                basla = df.loc[idx, "KESINTI BASLANGIC SAATI"]
                bitis = df.loc[idx, "KESINTI BITIS SAATI"]

                if not aktif_grup:
                    aktif_grup = [idx]
                    onceki_bitis = bitis
                else:
                    if pd.notnull(basla) and basla < onceki_bitis:
                        aktif_grup.append(idx)
                        onceki_bitis = max(onceki_bitis, bitis)
                    else:
                        if len(aktif_grup) > 1:
                            ilk = aktif_grup[0]
                            df.loc[ilk, "DURUM"] = "MEVCUT"
                            df.loc[ilk, "GÜNCELLENMİŞ BİTİŞ"] = max(df.loc[aktif_grup, "KESINTI BITIS SAATI"])
                            for diger in aktif_grup[1:]:
                                df.loc[diger, "DURUM"] = "İPTAL"
                        aktif_grup = [idx]
                        onceki_bitis = bitis

            if len(aktif_grup) > 1:
                ilk = aktif_grup[0]
                df.loc[ilk, "DURUM"] = "MEVCUT"
                df.loc[ilk, "GÜNCELLENMİŞ BİTİŞ"] = max(df.loc[aktif_grup, "KESINTI BITIS SAATI"])
                for diger in aktif_grup[1:]:
                    df.loc[diger, "DURUM"] = "İPTAL"

        # Sonuç gösterimi
        sonuc_df = df[df["DURUM"].isin(["MEVCUT", "İPTAL"])].copy()
        if not sonuc_df.empty:
            st.warning(f"{len(sonuc_df)} mükerrerlik ilişkili kayıt bulundu.")
            st.dataframe(sonuc_df, use_container_width=True)
        else:
            st.success("✅ Mükerrerlik içeren grup bulunamadı.")

    except Exception as e:
        st.exception(f"Hata oluştu: {str(e)}")
