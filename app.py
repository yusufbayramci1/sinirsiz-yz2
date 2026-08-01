import streamlit as st
import json
import google.generativeai as genai
from github import Github
import re

st.set_page_config(page_title="Sınırsız YZ", page_icon="🧠", layout="centered")

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] 
except:
    st.error("⚠️ Streamlit Secrets ayarlarını kontrol edin.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# Güncel ve garanti çalışan model doğrudan tanımlandı
model = genai.GenerativeModel('gemini-1.5-flash')

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

try:
    hafiza_dosyasi = repo.get_contents("hafiza.json")
    hafiza_icerik = json.loads(hafiza_dosyasi.decoded_content.decode('utf-8'))
except:
    hafiza_icerik = []

st.title("🧠 Sınırsız ve Öğrenen Yapay Zeka")
st.write("Sistem aktif ve çalışıyor!")

if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["role"]):
        st.markdown(mesaj["content"])

user_input = st.chat_input("Mesajınızı buraya yazın...")

if user_input:
    st.session_state.mesajlar.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    sistem_mesaji = f"""
    Sen her şeyi yapabilen, öğrenebilen otonom bir yapay zekasın. 
    Kalıcı Hafızan: {json.dumps(hafiza_icerik, ensure_ascii=False)}
    
    Kullanıcının mesajına cevap ver. Eğer yeni ve kalıcı bir bilgi öğreniyorsan 'yeni_bilgi' kısmına yaz, yoksa boş bırak.
    YANITINI MUTLAKA VE SADECE ŞU JSON FORMATINDA VER:
    {{
        "cevap": "Yanıtın",
        "yeni_bilgi": "Yeni öğrenilen bilgi veya boş"
    }}
    """

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                cevap_raw = model.generate_content(sistem_mesaji + f"\nKullanıcı: {user_input}")
                metin = cevap_raw.text
                metin = re.sub(r'```json\n?', '', metin)
                metin = re.sub(r'```\n?', '', metin)
                
                sonuc = json.loads(metin.strip())
                yz_cevabi = sonuc.get("cevap", "Yanıt alınamadı.")
                yeni_ogrenilen = sonuc.get("yeni_bilgi", "")

                st.markdown(yz_cevabi)
                st.session_state.mesajlar.append({"role": "assistant", "content": yz_cevabi})

                if yeni_ogrenilen and yeni_ogrenilen.strip() != "":
                    hafiza_icerik.append(yeni_ogrenilen)
                    repo.update_file(
                        hafiza_dosyasi.path,
                        "Hafıza güncellendi",
                        json.dumps(hafiza_icerik, ensure_ascii=False, indent=2),
                        hafiza_dosyasi.sha
                    )
                    st.success(f"💾 Hafızaya kaydedildi: {yeni_ogrenilen}")
            except Exception as e:
                st.error(f"Hata: {e}")
