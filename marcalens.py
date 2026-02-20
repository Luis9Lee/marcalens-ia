import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import os
import datetime

st.set_page_config(page_title="MarcaLens IA", page_icon="🔍", layout="wide")

# Cabeçalho estilo portal
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #6a11cb, #2575fc); padding: 20px; border-radius: 10px; color: white; text-align: center;">
        <h1>🔍 MarcaLens IA</h1>
        <h3>Análise Profissional de Marca com IA</h3>
        <p>Digite QUALQUER site que você quiser analisar</p>
    </div>
    """,
    unsafe_allow_html=True
)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        api_key = None

modelo = st.selectbox("Modelo IA", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"], index=0)

domain = st.text_input(
    "🌐 URL do site para análise",
    placeholder="https://proxmodegrau.com.br ou nubank.com.br",
    help="Domínio simples ou URL completa"
)

if st.button("🚀 Gerar Análise Completa de Marca", type="primary", use_container_width=True):
    if not domain:
        st.error("Digite o site!")
        st.stop()
    if not api_key:
        st.error("Chave API não encontrada! Configure em Settings → Secrets no Streamlit Cloud.")
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

            title = soup.title.string.strip() if soup.title else "Título não encontrado"
            meta_desc = ""
            for meta in soup.find_all("meta"):
                if meta.get("name") == "description" or meta.get("property") == "og:description":
                    meta_desc = meta.get("content", meta_desc)

            og_image = None
            og_tag = soup.find("meta", property="og:image")
            if og_tag and og_tag.get("content"):
                og_image = og_tag["content"]
                if not og_image.startswith("http"):
                    og_image = urljoin(url, og_image)

            favicon = f"https://www.google.com/s2/favicons?sz=128&domain={urlparse(url).netloc}"

            headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])[:12] if h.get_text(strip=True)]
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
            sample_text = " ".join(paragraphs[:18])[:3500]

            colors_raw = re.findall(r'#([0-9a-fA-F]{6})', resp.text)
            colors = ["#" + c.upper() for c in list(dict.fromkeys(colors_raw))][:8]

            site_data = f"URL: {url}\nTítulo: {title}\nDescrição: {meta_desc}\nCores detectadas: {', '.join(colors)}\nHeadings principais: {', '.join(headings[:8])}\nAmostra de texto: {sample_text}"

            client = Groq(api_key=api_key)

            stream = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Você é um consultor sênior de branding. Responda em português do Brasil, profissional, detalhado e estruturado. Use linguagem empática quando o tema for saúde/terapias."},
                    {"role": "user", "content": f"Analise a marca deste site de forma completa e profissional, inspirado em relatórios premium de branding:\n\n{site_data}\n\nEstrutura EXATA com estes títulos em negrito:\n**Resumo da Marca**\n**Identidade Visual** (inclua paleta de cores detectadas)\n**Personalidade da Marca** (descreva como um radar ou traços)\n**Público-alvo**\n**Voz e Tom**\n**Posicionamento**\n**Forças**\n**Fraquezas**\n**Oportunidades**\n**Ameaças**\n**Recomendações Estratégicas** (liste numeradas 4-6 ações)\n**Nota Final da Marca (0-10)** + justificativa\nSeja objetivo, use exemplos do site e sugira arquétipo (ex: O Cuidador)."}
                ],
                temperature=0.75,
                max_tokens=2200,
                stream=True
            )

            full_response = ""
            placeholder = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

            # Layout visual do relatório (estilo portal)
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{title.upper()}**")
                st.caption(f"{url} • Analisado em {datetime.date.today().strftime('%d de %B de %Y')}")
            with col2:
                if og_image:
                    st.image(og_image, caption="Imagem principal / Logo", use_column_width=True)
                else:
                    st.image(favicon, width=128)

            # Paleta de cores detectadas
            if colors:
                st.markdown("**Paleta de Cores Detectada**")
                color_cols = st.columns(len(colors))
                for i, col in enumerate(color_cols):
                    col.markdown(f"<div style='background-color:{colors[i]}; height:60px; border-radius:8px;'></div>", unsafe_allow_html=True)
                    col.caption(colors[i])

            # Seções em expansores para melhor organização
            with st.expander("📊 Resumo da Marca & Identidade Visual", expanded=True):
                st.markdown(full_response.split("**Identidade Visual**")[0] if "**Identidade Visual**" in full_response else full_response)

            with st.expander("🧠 Personalidade, Público-alvo, Voz e Posicionamento", expanded=True):
                pass  # O markdown completo já está acima; pode fatiar se quiser seções separadas

            with st.expander("💪 Forças & Fraquezas + Oportunidades & Ameaças", expanded=True):
                pass

            with st.expander("⚡ Recomendações Estratégicas", expanded=True):
                pass

            st.success("Análise concluída! Compartilhe ou exporte se precisar.")

        except Exception as e:
            st.error(f"Erro ao processar: {str(e)}")
            st.info("Dica: Verifique se o site está acessível e tente outro domínio.")
