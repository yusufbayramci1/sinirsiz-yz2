import streamlit as st
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from github import Github
import pickle
import io

st.set_page_config(page_title="Öz Otonom Kendi YZ'm", page_icon="🧠", layout="centered")

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] 
except:
    st.error("⚠️ Streamlit Secrets ayarlarına GITHUB_TOKEN ve REPO_NAME ekleyin.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

st.title("🧠 Sıfırdan Kendi Yapay Zekam")
st.write("Bu yapay zeka dışarıdan API kullanmaz; kendi verilerinle eğitilir ve modelini GitHub'da saklar!")

# GitHub'dan eğitim verilerini ve modeli yükle
def verileri_yukle():
    egitim_verileri = [("merhaba", "selam"), ("nasılsın", "iyiyim teşekkürler")]
    try:
        dosya = repo.get_contents("egitim_verisi.json")
        egitim_verileri = json.loads(dosya.decoded_content.decode('utf-8'))
    except:
        pass
    return egitim_verileri

egitim_verileri = verileri_yukle()

# Kullanıcı arayüzü
user_input = st.text_input("Yapay zekaya bir şey öğret veya soru sor:")
ogrenilecek_cevap = st.text_input("Eğer bu soruya ne cevap vermesini istiyorsan buraya yaz (Sadece öğretirken doldur):")

if st.button("Yapay Zekayı Eğit / Veri Ekle"):
    if user_input and ogrenilecek_cevap:
        egitim_verileri.append((user_input, ogrenilecek_cevap))
        
        # GitHub'a yeni eğitim verisini kaydet
        veri_json = json.dumps(egitim_verileri, ensure_ascii=False, indent=2)
        try:
            eski_dosya = repo.get_contents("egitim_verisi.json")
            repo.update_file(eski_dosya.path, "Eğitim verisi güncellendi", veri_json, eski_dosya.sha)
        except:
            repo.create_file("egitim_verisi.json", "Eğitim verisi oluşturuldu", veri_json)
            
        st.success(f"🎓 Başarıyla öğretildi ve GitHub'a kaydedildi! Veri sayısı: {len(egitim_verileri)}")
    else:
        st.warning("Lütfen hem girdiyi hem de beklenen yanıtı doldurun.")

# Modeli Eğit
if len(egitim_verileri) > 0:
    X = [item[0] for item in egitim_verileri]
    y = [item[1] for item in egitim_verileri]
    
    vectorizer = TfidfVectorizer()
    X_vec = vectorizer.fit_transform(X)
    
    model = SGDClassifier()
    model.fit(X_vec, y)

    if user_input and not ogrenilecek_cevap:
        X_test = vectorizer.transform([user_input])
        tahmin = model.predict(X_test)[0]
        st.markdown(f"**Yapay Zeka Yanıtı:** {tahmin}")

st.write("---")
st.subheader("📚 Mevcut Eğitim Veritabanı (GitHub'dan):")
st.json(egitim_verileri)
