import streamlit as st
import json
from groq import Groq
from github import Github
from duckduckgo_search import DDGS
import re

st.set_page_config(page_title="Otonom İnternet YZ", page_icon="🧠", layout="centered")

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] 
except:
    st.error("⚠️ Streamlit Secrets ayarlarını kontrol edin.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
model_adi = "llama-3.3-70b-versatile"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# GitHub'dan mevcut hafızayı yükle
try:
    hafiza_dosyasi = repo.get_contents("hafiza.json")
    icerik_str = hafiza_dosyasi.decoded_content.decode('utf-8').strip()
    hafiza_icerik = json.loads(icerik_str) if icerik_str and icerik_str != "[]" else []
except:
    hafiza_icerik = []

st.title("🧠 Otonom İnternetten Öğrenen YZ")
st.write("Bana herhangi bir şey sor veya konu yaz; internetten kendim öğreneyim, hafızama atayım ve sana anlatayım!")

if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["role"]):
        st.markdown(mesaj["content"])

user_input = st.chat_input("Yapay zekanın öğrenmesini veya araştırmasını istediğin konuyu yaz...")

if user_input:
    st.session_state.mesajlar.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🌍 İnternette araştırılıyor, analiz ediliyor ve öğreniliyor..."):
            
            # 1. Adım: Yapay zeka internette arama yapar
            bulgular = ""
            try:
                results = DDGS().text(user_input, max_results=5)
                for r in results:
                    bulgular += f"- {r.get('title')}: {r.get('body')}\n"
            except:
                bulgular = "İnternet araması yapılamadı, genel bilgimle yanıtlıyorum."

            # 2. Adım: Bulunan bilgileri işle ve öğren
            sistem_mesaji = f"""
            Sen tamamen otonom, internetten öğrenen bir yapay zekasın. 
            Daha Önce Öğrendiklerin (Kalıcı Hafıza): {json.dumps(hafiza_icerik, ensure_ascii=False)}
            
            İnternetten anlık olarak bulduğum veriler:
            {bulgular}
            
            Kullanıcının girdisi: "{user_input}"
            
            Görevin: İnternet verilerini ve hafızanı kullanarak kullanıcıya profesyonel, net ve kapsamlı bir yanıt vermek. Ayrıca bu olaydan öğrendiğin yeni ve kalıcı bilgiyi 'yeni_bilgi' alanına özet olarak yazmak.
            
            YANITINI MUTLAKA VE SADECE GEÇERLİ BİR JSON NESNESİ OLARAK VER:
            {{
                "cevap": "Kullanıcıya vereceğin detaylı ve açıklayıcı yanıt",
                "yeni_bilgi": "Bu aramadan hafızaya kaydedilecek net özet bilgi"
            }}
            """

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
                
                yz_cevabi = sonuc.get("cevap", "Yanıt oluşturulamadı.")
                yeni_ogrenilen = sonuc.get("yeni_bilgi", "")

                st.markdown(yz_cevabi)
                st.session_state.mesajlar.append({"role": "assistant", "content": yz_cevabi})

                # 3. Adım: Öğrenilen bilgiyi GitHub hafızasına otomatik kaydet
                if yeni_ogrenilen and str(yeni_ogrenilen).strip() != "":
                    hafiza_icerik.append(yeni_ogrenilen)
                    yeni_json_veri = json.dumps(hafiza_icerik, ensure_ascii=False, indent=2)
                    
                    try:
                        guncel_dosya = repo.get_contents("hafiza.json")
                        repo.update_file(
                            guncel_dosya.path,
                            "Otonom hafıza güncellendi",
                            yeni_json_veri,
                            guncel_dosya.sha
                        )
                    except:
                        repo.create_file(
                            "hafiza.json",
                            "Otonom hafıza dosyası oluşturuldu",
                            yeni_json_veri
                        )
                    st.success(f"🧠 İnternetten öğrenilip GitHub hafızasına kaydedildi: {yeni_ogrenilen}")
            except Exception as e:
                st.error(f"Hata oluştu: {e}")
