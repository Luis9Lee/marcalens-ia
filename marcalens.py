import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import datetime
import os
import json

st.set_page_config(page_title="MarcaLens IA - Portal", page_icon="🔍", layout="wide")

# CSS refinado para seu estilo atual (fundo escuro + roxo + cards destacados)
st.markdown("""
    <style>
        .stApp { background: #0f172a; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .header { background: linear-gradient(90deg, #6d28d9, #c084fc); padding: 1.8rem; text-align: center; border-radius: 0 0 24px 24px; box-shadow: 0 8px 32px rgba(109,40,217,0.3); }
        .input-group { display: flex; gap: 1rem; max-width: 900px; margin: 2rem auto; align-items: stretch; }
        .stTextInput > div > div > input { background: #1e293b; color: white; border: none; border-radius: 12px; padding: 1.2rem; font-size: 1.1rem; }
        button[kind="primary"] { background: linear-gradient(to right, #a855f7, #c084fc) !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 1rem 2rem !important; font-weight: bold !important; }
        .brand-title { font-size: 3rem; font-weight: 700; text-align: center; margin: 2rem 0 0.5rem; color: #f3e8ff; }
        .brand-tag { font-size: 1.4rem; text-align: center; color: #cbd5e1; margin-bottom: 0.5rem; }
        .brand-info { text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }
        .paleta { display: flex; justify-content: center; gap: 14px; margin: 1.5rem 0; flex-wrap: wrap; }
        .swatch { width: 60px; height: 60px; border-radius: 12px; border: 3px solid #334155; box-shadow: 0 6px 20px rgba(0,0,0,0.5); transition: transform 0.2s; }
        .swatch:hover { transform: scale(1.15); }
        .card { background: #1e293b; border-radius: 16px; padding: 1.8rem; margin: 1.5rem 0; border: 1px solid #334155; box-shadow: 0 6px 24px rgba(0,0,0,0.3); }
        .strength-card { border-left: 6px solid #10b981; }
        .weakness-card { border-left: 6px solid #ef4444; }
        .recommend-card { border-left: 6px solid #a855f7; }
        .nota-box { font-size: 4rem; font-weight: bold; text-align: center; margin: 2rem 0; padding: 1rem; border-radius: 16px; background: #1e293b; border: 2px solid #fbbf24; color: #fbbf24; }
        .section-title { font-size: 1.8rem; margin: 2rem 0 1rem; color: #e0e7ff; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho roxo como no seu print
st.markdown("""
    <div class="header">
        <h1>MarcaLens Portal</h1>
        <h3>Equipe Design & Marketing</h3>
    </div>
""", unsafe_allow_html=True)

api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Configure GROQ_API_KEY nos Secrets do Streamlit Cloud")
    st.stop()

# Input + botão (estilo seu print)
st.markdown('<div class="input-group">', unsafe_allow_html=True)
url = st.text_input("", placeholder="https://proximeodegrau.com.br", label_visibility="collapsed")
if st.button("Nova Auditoria", type="primary"):
    pass
st.markdown('</div>', unsafe_allow_html=True)

if url:
    with st.spinner("Auditoria em andamento..."):
        try:
            full_url = url if url.startswith(('http://', 'https://')) else 'https://' + url.strip('/')
            resp = requests.get(full_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "Próximo Degrau"
            desc = next((m['content'] for m in soup.find_all("meta") if m.get("name") == "description" or m.get("property") == "og:description"), "")
            colors_raw = re.findall(r'#([0-9a-fA-F]{6})', resp.text)
            colors = ["#" + c.upper() for c in dict.fromkeys(colors_raw)][:6]

            site_data = f"URL: {full_url}\nTítulo: {title}\nDescrição/meta: {desc[:800]}\nConteúdo principal: {soup.get_text()[:2000]}"

            client = Groq(api_key=api_key)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Responda **somente** JSON válido, sem texto antes ou depois. Estrutura obrigatória: {\"brandName\": str, \"tagline\": str, \"summary\": str, \"arquetipo\": str, \"forcas\": [str], \"fraquezas\": [str], \"recomendacoes\": [str], \"nota\": float 0-10}. Baseie-se **apenas** no conteúdo real do site fornecido, sem inventar informações. Seja preciso e objetivo."},
                    {"role": "user", "content": f"Analise esta marca com precisão baseada no conteúdo do site: {site_data}"}
                ],
                temperature=0.6,
                max_tokens=900
            )

            raw = res.choices[0].message.content.strip()
            try:
                data = json.loads(raw)
            except:
                # Limpeza extrema
                start = raw.find('{')
                end = raw.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(raw[start:end])
                else:
                    data = {"summary": raw, "nota": 5.0}

            # Visualização precisa e bonita
            st.markdown(f'<div class="brand-title">{data.get("brandName", title)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="brand-tag">{data.get("tagline", "Centro de Excelência em...")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="brand-info">{full_url} • Analisado em {datetime.datetime.now().strftime("%d de %B de %Y às %H:%M")}</div>', unsafe_allow_html=True)

            if colors:
                st.markdown('<div class="paleta">' + ''.join(f'<div class="swatch" style="background:{c}"></div>' for c in colors) + '</div>', unsafe_allow_html=True)

            # Resumo
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Resumo da Marca")
            st.write(data.get("summary", "Informações extraídas do site."))
            st.markdown('</div>', unsafe_allow_html=True)

            # Forças e Fraquezas
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="card strength">', unsafe_allow_html=True)
                st.subheader("Forças")
                for item in data.get("forcas", []):
                    st.markdown(f"• {item}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="card weakness">', unsafe_allow_html=True)
                st.subheader("Fraquezas")
                for item in data.get("fraquezas", []):
                    st.markdown(f"• {item}")
                st.markdown('</div>', unsafe_allow_html=True)

            # Recomendações
            st.markdown('<div class="card recommend">', unsafe_allow_html=True)
            st.subheader("Recomendações Estratégicas")
            for i, rec in enumerate(data.get("recomendacoes", []), 1):
                st.markdown(f"{i}. {rec}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Nota destacada
            nota = data.get("nota", 7.0)
            cor_nota = "#10b981" if nota >= 7 else "#fbbf24" if nota >= 5 else "#ef4444"
            st.markdown(f'<div class="nota-box" style="border-color:{cor_nota}; color:{cor_nota};">{nota}/10</div>', unsafe_allow_html=True)

            st.success("Auditoria precisa concluída! Visual ajustado.")

        except Exception as e:
            st.error(f"Erro: {str(e)}")
            st.info("Site pode estar instável. Tente novamente ou use outra URL.")
    st.info("Digite a URL acima e clique em 'Nova Auditoria' para começar.")
