import streamlit as st
import json
import google.generativeai as genai
from github import Github
import re

st.set_page_config(page_title="Sınırsız YZ", page_icon="🧠", layout="centered")

# Streamlit Secrets Kontrolü
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] 
except Exception as e:
    st.error("⚠️ Lütfen Streamlit Secrets ayarlarına GEMINI_API_KEY, GITHUB_TOKEN ve REPO_NAME değerlerini ekleyin.")
    st.stop()

# Gemini ve GitHub Bağlantıları
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Hafıza dosyasını GitHub'dan çekme
try:
    hafiza_dosyasi = repo.get_contents("hafiza.json")
    hafiza_icerik = json.loads(hafiza_dosyasi.decoded_content.decode('utf-8'))
except:
    hafiza_icerik = []

st.title("🧠 Sınırsız ve Öğrenen Yapay Zeka")
st.write("Bana görev ver, soru sor veya yeni bir şey öğret. Her konuşmada öğrenip kendini günceller!")

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
    Kalıcı Hafızan (Geçmişte öğrendiklerin): {json.dumps(hafiza_icerik, ensure_ascii=False)}
    
    Kullanıcının mesajına en iyi şekilde cevap ver. Eğer kullanıcı sana YENİ, KALICI bir bilgi öğretiyorsa, gelecekte hatırlaman gereken bir detay (adını, sevdiği şeyleri, projelerini vb.) söylüyorsa bunu 'yeni_bilgi' kısmına yaz. Sadece normal bir sohbet ediyorsa 'yeni_bilgi' kısmını boş bırak.
    
    YANITINI MUTLAKA VE SADECE AŞAĞIDAKİ JSON FORMATINDA VER, BAŞKA HİÇBİR AÇIKLAMA EKLEME:
    {{
        "cevap": "Kullanıcıya vereceğin samimi yanıt",
        "yeni_bilgi": "Öğrendiğin yeni bilgi cümlesi veya boş bırak"
    }}
    """

    with st.chat_message("assistant"):
        with st.spinner("Yapay zeka düşünüyor..."):
            sohbet_gecmisi = [{"role": "user", "parts": [sistem_mesaji]}]
            for m in st.session_state.mesajlar:
                role = "user" if m["role"] == "user" else "model"
                sohbet_gecmisi.append({"role": role, "parts": [m["content"]]})
                
            try:
                cevap_raw = model.generate_content(sohbet_gecmisi)
                
                metin = cevap_raw.text
                metin = re.sub(r'```json\n?', '', metin)
                metin = re.sub(r'```\n?', '', metin)
                
                sonuc = json.loads(metin.strip())
                yz_cevabi = sonuc.get("cevap", "Bir hata oluştu.")
                yeni_ogrenilen = sonuc.get("yeni_bilgi", "")

                st.markdown(yz_cevabi)
                st.session_state.mesajlar.append({"role": "assistant", "content": yz_cevabi})

                if yeni_ogrenilen and yeni_ogrenilen.strip() != "":
                    hafiza_icerik.append(yeni_ogrenilen)
                    guncel_hafiza = json.dumps(hafiza_icerik, ensure_ascii=False, indent=2)
                    
                    repo.update_file(
                        hafiza_dosyasi.path,
                        f"Otomatik Hafıza Kaydı: {yeni_ogrenilen[:20]}...",
                        guncel_hafiza,
                        hafiza_dosyasi.sha
                    )
                    st.success(f"💾 **Yeni bilgi kalıcı hafızama kaydedildi:** {yeni_ogrenilen}")
            except Exception as e:
                st.error(f"İşlem sırasında hata oluştu: {e}")
