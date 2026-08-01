from collections import Counter
import json
import re
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from github import Github
import requests
import streamlit as st

st.set_page_config(
    page_title="Otonom Analiz ve Öğrenme Sistemi", page_icon="🧠", layout="centered"
)

try:
  GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
  REPO_NAME = st.secrets["REPO_NAME"]
except:
  st.error("⚠️ Streamlit Secrets ayarlarına GITHUB_TOKEN ve REPO_NAME ekleyin.")
  st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# GitHub'dan mevcut hafızayı güvenli bir şekilde yükle
try:
  hafiza_dosyasi = repo.get_contents("hafiza.json")
  icerik_str = hafiza_dosyasi.decoded_content.decode("utf-8").strip()
  hafiza_icerik = (
      json.loads(icerik_str) if icerik_str and icerik_str != "[]" else []
  )
except:
  hafiza_icerik = []

st.title("🧠 Otonom Analiz ve Öğrenme Sistemi")
st.write(
    "Bir konu veya URL yazın; sistem her şeyi derinlemesine incelesin, analiz"
    " etsin ve GitHub hafızasına kaydetsin."
)

if "mesajlar" not in st.session_state:
  st.session_state.mesajlar = []

for mesaj in st.session_state.mesajlar:
  with st.chat_message(mesaj["role"]):
    st.markdown(mesaj["content"])

user_input = st.chat_input("İncelenmesini ve öğrenilmesini istediğiniz konu...")

if user_input:
  st.session_state.mesajlar.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.markdown(user_input)

  with st.chat_message("assistant"):
    with st.spinner(
        "🔍 Veriler taranıyor, metinler çözümleniyor ve analiz ediliyor..."
    ):

      toplanan_metinler = ""
      analiz_kaynaklari = []

      # 1. Adım: İnternet Taraması ve Veri Toplama
      try:
        with DDGS() as ddgs:
          results = [r for r in ddgs.text(user_input, max_results=6)]
          for r in results:
            baslik = r.get("title", "")
            govde = r.get("body", "")
            link = r.get("href", "")
            toplanan_metinler += f"{baslik} {govde} "
            analiz_kaynaklari.append(
                {"baslik": baslik, "url": link, "ozet": govde}
            )
      except Exception as e:
        st.error(f"Arama sırasında hata oluştu: {e}")

      # 2. Adım: Derin Metin Analizi ve Önemli Bilgi Çıkarımı
      if toplanan_metinler.strip():
        # Kelime frekans analizi ile anahtar kavramları bulma
        temiz_kelimeler = re.findall(r"\b[a-zA-ZçğİıÖöŞşÜü]{4,}\b", toplanan_metinler.lower())
        durdurma_kelimeleri = {
            "için",
            "bir",
            "ile",
            "bu",
            "da",
            "de",
            "veya",
            "ama",
            "gibi",
            "olarak",
            "en",
            "daha",
            "çok",
            "ne",
            "nasıl",
        }
        filtrelenmis = [
            k for k in temiz_kelimeler if k not in durdurma_kelimeleri
        ]
        en_sik_kelimeler = [
            kelime for kelime, sayi in Counter(filtrelenmis).most_common(7)
        ]

        # Yapılandırılmış analiz paketi oluşturma
        analiz_sonucu = {
            "hedef_konu": user_input,
            "tespit_edilen_anahtar_kavramlar": en_sik_kelimeler,
            "incelenen_kaynak_sayisi": len(analiz_kaynaklari),
            "kaynaklar": analiz_kaynaklari,
        }

        hafiza_icerik.append(analiz_sonucu)
        yeni_json_veri = json.dumps(hafiza_icerik, ensure_ascii=False, indent=2)

        # 3. Adım: GitHub Hafızasına Kaydetme
        try:
          guncel_dosya = repo.get_contents("hafiza.json")
          repo.update_file(
              guncel_dosya.path,
              f"Analiz eklendi: {user_input}",
              yeni_json_veri,
              guncel_dosya.sha,
          )
          basari_metni = (
              f"✅ **'{user_input}'** başarıyla incelendi ve analiz sonuçları"
              f" GitHub hafızasına işlendi.\n\n"
              f"🔑 **Tespit Edilen Önemli Kavramlar:**"
              f" {', '.join(en_sik_kelimeler)}"
          )
          st.markdown(basari_metni)
          st.session_state.mesajlar.append(
              {"role": "assistant", "content": basari_metni}
          )
        except Exception:
          try:
            repo.create_file(
                "hafiza.json", "Hafıza dosyası oluşturuldu", yeni_json_veri
            )
            basari_metni = (
                f"✅ Hafıza dosyası oluşturuldu ve **'{user_input}'** analizi"
                f" kaydedildi.\n\n"
                f"🔑 **Tespit Edilen Önemli Kavramlar:**"
                f" {', '.join(en_sik_kelimeler)}"
            )
            st.markdown(basari_metni)
            st.session_state.mesajlar.append(
                {"role": "assistant", "content": basari_metni}
            )
          except Exception as err:
            st.error(f"GitHub'a yazma hatası: {err}")
      else:
        st.warning("Yeterli veri bulunamadı.")
