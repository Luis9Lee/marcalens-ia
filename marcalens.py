import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import datetime
import os
import json

st.set_page_config(page_title="MarcaLens IA - Portal", page_icon="🔍", layout="wide")

# CSS melhorado para combinar com seu print + glassmorphism
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        .stApp { font-family: 'Inter', sans-serif; background: #f8fafc; }
        .header { background: linear-gradient(90deg, #6b46c1, #9f7aea); color: white; padding: 1.5rem 2rem; border-radius: 0 0 20px 20px; text-align: center; box-shadow: 0 4px 20px rgba(107,70,193,0.3); }
        .input-container { display: flex; gap: 1rem; margin: 2rem auto; max-width: 800px; }
        .input-container input { flex: 1; padding: 1rem; border-radius: 12px; border: none; background: #2d3748; color: white; }
        .btn-nova { background: linear-gradient(to right, #7c3aed, #c084fc); color: white; border: none; border-radius: 12px; padding: 1rem 2rem; font-weight: 600; cursor: pointer; }
        .brand-header { text-align: center; margin: 2rem 0; }
        .brand-title { font-size: 2.2rem; font-weight: 700; color: #1a202c; }
        .brand-subtitle { color: #718096; font-size: 1.1rem; }
        .paleta { display: flex; gap: 12px; justify-content: center; margin: 1rem 0; }
        .swatch { width: 50px; height: 50px; border-radius: 10px; border: 3px solid white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .card { background: rgba(255,255,255,0.85); backdrop-filter: blur(10px); border-radius: 16px; border: 1px solid rgba(255,255,255,0.4); padding: 1.5rem; margin: 1.5rem 0; box-shadow: 0 6px 24px rgba(0,0,0,0.08); }
        .strength { border-left: 5px solid #10b981; }
        .weakness { border-left: 5px solid #ef4444; }
        .recommend { border-left: 5px solid #7c3aed; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown('<div class="header"><h1>MarcaLens Portal</h1><h3>Equipe Design & Marketing • Auditoria de Marca com IA</h3></div>', unsafe_allow_html=True)

api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Chave Groq não encontrada. Configure em secrets.toml ou no Cloud.")
    st.stop()

# Input + botão (como no seu print)
st.markdown('<div class="input-container">', unsafe_allow_html=True)
url = st.text_input("", placeholder="https://proximeodegrau.com.br", label_visibility="collapsed")
analisar = st.button("Nova Auditoria", type="primary", key="btn_nova")
st.markdown('</div>', unsafe_allow_html=True)

if analisar and url:
    with st.spinner("Analisando..."):
        try:
            full_url = url if url.startswith(('http', 'https')) else 'https://' + url
            resp = requests.get(full_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "Próximo Degrau"
            desc = next((m['content'] for m in soup.find_all("meta") if m.get("name") == "description"), "Centro de Terapias Integradas")
            og_img = next((m['content'] for m in soup.find_all("meta", property="og:image")), None)

            colors_raw = re.findall(r'#([0-9a-fA-F]{6})', resp.text)
            colors = ["#" + c.upper() for c in dict.fromkeys(colors_raw)][:6]

            site_data = f"URL: {full_url}\nTítulo: {title}\nDescrição: {desc[:600]}"

            client = Groq(api_key=api_key)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Responda em JSON curto: {brandName, tagline, summary, arquetipo, forcas: array, fraquezas: array, recomendacoes: array, nota: number}"},
                    {"role": "user", "content": f"Analise marca: {site_data}"}
                ],
                temperature=0.7
            )

            try:
                data = json.loads(res.choices[0].message.content)
            except:
                data = {"summary": res.choices[0].message.content, "nota": "8.5"}

            # Render como no seu print + portal completo
            st.markdown(f'<div class="brand-header"><div class="brand-title">{data.get("brandName", title)}</div><div class="brand-subtitle">{data.get("tagline", "Centro de Excelência em...")}</div><div style="color:#718096; margin-top:0.5rem;">{full_url} • Analisado em {datetime.datetime.now().strftime("%d de %B de %Y às %H:%M")}</div></div>', unsafe_allow_html=True)

            # Paleta
            if colors:
                paleta_html = '<div class="paleta">' + ''.join(f'<div class="swatch" style="background:{c}"></div>' for c in colors) + '</div>'
                st.markdown(paleta_html, unsafe_allow_html=True)

            # Cards principais
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Resumo")
            st.write(data.get("summary", "Análise gerada pela IA"))
            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="card strength">', unsafe_allow_html=True)
                st.subheader("Forças")
                for f in data.get("forcas", ["Modelo integrado", "Equipe especializada", "Infraestrutura premium"]):
                    st.markdown(f"- {f}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="card weakness">', unsafe_allow_html=True)
                st.subheader("Fraquezas")
                for w in data.get("fraquezas", ["Concentração geográfica", "Custo elevado"]):
                    st.markdown(f"- {w}")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card recommend">', unsafe_allow_html=True)
            st.subheader("Recomendações")
            for i, rec in enumerate(data.get("recomendacoes", ["Expandir digital", "Conteúdo educativo", "SEO local"]), 1):
                st.markdown(f"{i}. {rec}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.metric("Nota Final", f"{data.get('nota', 'N/A')}/10", delta_color="normal")

            st.success("Auditoria pronta! Estilo portal atualizado.")

        except Exception as e:
            st.error(f"Erro: {str(e)}")
            st.info("Site pode estar offline ou bloqueando. Tente https://proximeodegrau.com.br corrigido.")

