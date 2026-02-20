import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import os

st.set_page_config(page_title="MarcaLens IA", page_icon="🔍", layout="wide")

st.title("🔍 MarcaLens IA")
st.subheader("Análise Profissional de Marca com IA")
st.caption("Digite QUALQUER site que você quiser analisar")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        api_key = None

modelo = st.selectbox("Modelo IA", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"], index=0)

domain = st.text_input(
    "🌐 Digite QUALQUER site que você quiser",
    placeholder="nubank.com.br ou https://www.apple.com",
    help="Domínio simples ou URL completa"
)

if st.button("🚀 Gerar Análise Completa de Marca", type="primary", use_container_width=True):
    if not domain:
        st.error("Digite o site!")
        st.stop()
    if not api_key:
        st.error("Chave API não encontrada!")
        st.info("Crie a pasta .streamlit e o arquivo secrets.toml (veja instruções abaixo)")
        st.stop()

    with st.spinner(f"Analisando {domain}..."):
        try:
            if not domain.startswith(('http://', 'https://')):
                url = 'https://' + domain.strip('/')
            else:
                url = domain

            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else ""
            meta_desc = ""
            for meta in soup.find_all("meta"):
                if meta.get("name") == "description" or meta.get("property") == "og:description":
                    meta_desc = meta.get("content", "")

            og_image = None
            og_tag = soup.find("meta", property="og:image")
            if og_tag and og_tag.get("content"):
                og_image = og_tag["content"]
                if not og_image.startswith("http"):
                    og_image = urljoin(url, og_image)

            favicon = f"https://www.google.com/s2/favicons?sz=128&domain={urlparse(url).netloc}"

            headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])[:12]]
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
            sample_text = " ".join(paragraphs[:18])[:3500]

            colors = ["#" + c for c in list(dict.fromkeys(re.findall(r'#([0-9a-fA-F]{6})', resp.text)))[:12]]

            site_data = f"URL: {url}\nTítulo: {title}\nDescrição: {meta_desc}\nCores: {', '.join(colors)}\nHeadings: {', '.join(headings[:8])}\nTexto: {sample_text}"

            client = Groq(api_key=api_key)

            stream = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Você é um consultor sênior de branding. Responda em português do Brasil de forma profissional, objetiva e muito detalhada."},
                    {"role": "user", "content": f"Analise a marca deste site de forma completa e profissional:\n\n{site_data}\n\nUse exatamente estas seções: **1. Resumo Executivo** **2. Identidade da Marca** **3. Identidade Visual** **4. Tom de Voz** **5. Público-alvo** **6. Posicionamento** **7. Análise de UX** **8. Forças e Fraquezas** **9. Matriz SWOT** **10. Recomendações Estratégicas** **11. Nota Final (0-10)**"}
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )

            full_response = ""
            placeholder = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

            if og_image:
                st.image(og_image, caption="Imagem principal da marca", use_column_width=True)

        except Exception as e:
            st.error(f"Erro ao processar: {str(e)}")
