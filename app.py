import streamlit as st
import json
from groq import Groq
from github import Github
import re

st.set_page_config(page_title="Otonom Araştırma YZ", page_icon="🧠", layout="centered")

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] 
except:
    st.error("⚠️ Streamlit Secrets ayarlarına GROQ_API_KEY ekleyin.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
model_adi = "llama-3.3-70b-versatile"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Hafızayı GitHub'dan güvenli bir şekilde yükle
try:
    hafiza_dosyasi = repo.get_contents("hafiza.json")
    icerik_str = hafiza_dosyasi.decoded_content.decode('utf-8').strip()
    if icerik_str == "" or icerik_str == "[]":
        hafiza_icerik = []
    else:
        hafiza_icerik = json.loads(icerik_str)
except:
    hafiza_icerik = []

st.title("🧠 Otonom Araştıran ve Öğrenen YZ")
st.write("Konuyu araştırır, hafızaya alır ve doğrudan GitHub'a kaydeder!")

if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["role"]):
        st.markdown(mesaj["content"])

user_input = st.chat_input("Araştırmamı istediğin konuyu yaz...")

if user_input:
    st.session_state.mesajlar.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    sistem_mesaji = f"""
    Sen üst düzey otonom bir araştırma ve öğrenme yapay zekasın. 
    Mevcut Kalıcı Hafızan: {json.dumps(hafiza_icerik, ensure_ascii=False)}
    
    Kullanıcı sana bir konu söylediğinde o konuyu internette araştırmış gibi derinlemesine açıkla.
    Yeni öğrendiğin net bilgiyi 'yeni_bilgi' alanına ekle.
    
    YANITINI MUTLAKA VE SADECE GEÇERLİ BİR JSON NESNESİ OLARAK VER:
    {{
        "cevap": "Araştırma raporun ve açıklaman",
        "yeni_bilgi": "Hafızaya eklenecek yeni bilgi"
    }}
    """

    with st.chat_message("assistant"):
        with st.spinner("Araştırılıyor ve GitHub'a kaydediliyor..."):
            try:
                completion = client.chat.completions.create(
                    model=model_adi,
                    messages=[
                        {"role": "system", "content": sistem_mesaji},
                        {"role": "user", "content": user_input}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )
                
                metin = completion.choices[0].message.content.strip()
                sonuc = json.loads(metin)
                
                yz_cevabi = sonuc.get("cevap", "Yanıt alınamadı.")
                yeni_ogrenilen = sonuc.get("yeni_bilgi", "")

                st.markdown(yz_cevabi)
                st.session_state.mesajlar.append({"role": "assistant", "content": yz_cevabi})

                if yeni_ogrenilen and str(yeni_ogrenilen).strip() != "":
                    hafiza_icerik.append(yeni_ogrenilen)
                    yeni_json_veri = json.dumps(hafiza_icerik, ensure_ascii=False, indent=2)
                    
                    # GitHub'a kesin ve hatasız yazma garantisi
                    try:
                        guncel_dosya = repo.get_contents("hafiza.json")
                        repo.update_file(
                            guncel_dosya.path,
                            "Hafıza güncellendi",
                            yeni_json_veri,
                            guncel_dosya.sha
                        )
                        st.success(f"💾 GitHub hafızasına başarıyla kaydedildi: {yeni_ogrenilen}")
                    except:
                        repo.create_file(
                            "hafiza.json",
                            "Hafıza dosyası oluşturuldu",
                            yeni_json_veri
                        )
                        st.success(f"💾 GitHub hafızası oluşturuldu ve kaydedildi: {yeni_ogrenilen}")
            except Exception as e:
                st.error(f"Hata: {e}")
