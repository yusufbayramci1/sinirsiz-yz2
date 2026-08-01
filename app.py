import streamlit as st
import json
from groq import Groq
from github import Github
import re

st.set_page_config(page_title="Sınırsız YZ", page_icon="🧠", layout="centered")

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

try:
    hafiza_dosyasi = repo.get_contents("hafiza.json")
    icerik_str = hafiza_dosyasi.decoded_content.decode('utf-8').strip()
    if icerik_str == "":
        hafiza_icerik = []
    else:
        hafiza_icerik = json.loads(icerik_str)
except:
    hafiza_icerik = []

st.title("🧠 Sınırsız ve Hızlı Yapay Zeka")
st.write("Sistem Groq altyapısıyla aktif ve hafıza modülü devrede!")

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
    
    Kullanıcının mesajına cevap ver. Eğer kullanıcı sana kalıcı bir kişisel bilgi, tercih veya proje öğretiyorsa 'yeni_bilgi' kısmına kaydet, yoksa boş bırak.
    YANITINI MUTLAKA VE SADECE GEÇERLİ BİR JSON NESNESİ OLARAK VER:
    {{
        "cevap": "Kullanıcıya vereceğin yanıt",
        "yeni_bilgi": "Öğrenilen yeni bilgi veya boş bırak"
    }}
    """

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor ve öğreniyor..."):
            try:
                # Kesin JSON çıktısı zorunluluğu
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
                    try:
                        repo.update_file(
                            hafiza_dosyasi.path,
                            "Hafıza güncellendi",
                            json.dumps(hafiza_icerik, ensure_ascii=False, indent=2),
                            hafiza_dosyasi.sha
                        )
                    except:
                        repo.create_file(
                            "hafiza.json",
                            "Hafıza dosyası oluşturuldu",
                            json.dumps(hafiza_icerik, ensure_ascii=False, indent=2)
                        )
                    st.success(f"💾 Hafızaya kaydedildi: {yeni_ogrenilen}")
            except Exception as e:
                st.error(f"Hata: {e}")
