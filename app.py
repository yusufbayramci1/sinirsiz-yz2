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

# Hafızayı GitHub'dan yükle
try:
    hafiza_dosyasi = repo.get_contents("hafiza.json")
    icerik_str = hafiza_dosyasi.decoded_content.decode('utf-8').strip()
    if icerik_str == "":
        hafiza_icerik = []
    else:
        hafiza_icerik = json.loads(icerik_str)
except:
    hafiza_icerik = []

st.title("🧠 Otonom Araştıran ve Öğrenen YZ")
st.write("Bana bir konu söyle; internetten derinlemesine araştırayım, öğreneyim ve hafızama kaydedeyim!")

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
    Sen üst düzey otonom bir araştırma ve öğrenme yapay zekasısın. 
    Mevcut Kalıcı Hafızan: {json.dumps(hafiza_icerik, ensure_ascii=False)}
    
    Kullanıcı sana bir konu veya başlık söylediğinde, o konuyu sanki internette detaylıca araştırmış gibi en güncel, kapsamlı, teknik ve profesyonel düzeyde araştırıp detaylı bir rapor/açıklama sunarsın. 
    Aynı zamanda bu araştırmadan elde ettiğin ana özeti/bilgiyi 'yeni_bilgi' alanına ekleyerek kalıcı hafızaya kaydedilmesini sağlarsın.
    
    YANITINI MUTLAKA VE SADECE GEÇERLİ BİR JSON NESNESİ OLARAK VER:
    {{
        "cevap": "Konuyla ilgili kapsamlı araştırma raporun ve açıklaman",
        "yeni_bilgi": "Bu araştırmadan hafızaya eklenmesi gereken net özet bilgi"
    }}
    """

    with st.chat_message("assistant"):
        with st.spinner("İnternette araştırılıyor ve öğreniliyor..."):
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
