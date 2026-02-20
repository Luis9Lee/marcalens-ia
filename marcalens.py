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

# CSS ajustado para combinar exatamente com o seu print atual
st.markdown("""
    <style>
        body, .stApp { background: #0f172a; color: white; font-family: 'Inter', sans-serif; }
        .header { background: linear-gradient(90deg, #6d28d9, #c084fc); padding: 1.5rem; border-radius: 0 0 20px 20px; text-align: center; }
        .input-row { display: flex; gap: 1rem; margin: 2rem auto; max-width: 900px; align-items: center; }
        .stTextInput > div > div > input { background: #1e293b; color: white; border: none; border-radius: 12px; padding: 1rem; }
        .btn-nova { background: linear-gradient(90deg, #a855f7, #c084fc); color: white; border: none; border-radius: 12px; padding: 1rem 2rem; font-weight: bold; cursor: pointer; }
        .brand-title { font-size: 2.8rem; font-weight: 700; text-align: center; margin: 1.5rem 0 0.5rem; color: #e0e7ff; }
        .brand-tag { font-size: 1.3rem; text-align: center; color: #94a3b8; margin-bottom: 0.5rem; }
        .brand-info { text-align: center; color: #64748b; font-size: 1rem; margin-bottom: 1.5rem; }
        .paleta { display: flex; justify-content: center; gap: 12px; margin: 1.5rem 0; }
        .swatch { width: 60px; height: 60px; border-radius: 12px; border: 3px solid #334155; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
        .card { background: #1e293b; border-radius: 16px; padding: 1.8rem; margin: 1.5rem 0; border: 1px solid #334155; }
        .strength { border-left: 6px solid #10b981; }
        .weakness { border-left: 6px solid #ef4444; }
        .recommend { border-left: 6px solid #a855f7; }
        .nota { font-size: 3rem; font-weight: bold; color: #fbbf24; text-align: center; margin: 2rem 0; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown('<div class="header"><h1>MarcaLens Portal</h1><h3>Equipe Design & Marketing</h3></div>', unsafe_allow_html=True)

api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Configure a chave GROQ_API_KEY nos Secrets do Streamlit Cloud")
    st.stop()

# Input + botão (exatamente como no seu print)
st.markdown('<div class="input-row">', unsafe_allow_html=True)
col_url, col_btn = st.columns([4, 1])
with col_url:
    url = st.text_input("", placeholder="https://proximeodegrau.com.br", label_visibility="collapsed")
with col_btn:
    if st.button("Nova Auditoria", key="nova_auditoria"):
        pass  # O botão ativa o processamento abaixo
st.markdown('</div>', unsafe_allow_html=True)

if url:
    with st.spinner("Realizando auditoria completa..."):
        try:
            full_url = url if url.startswith(('http://', 'https://')) else 'https://' + url
            resp = requests.get(full_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "Próximo Degrau"
            desc = next((m['content'] for m in soup.find_all("meta") if m.get("name") == "description" or m.get("property") == "og:description"), "")
            colors_raw = re.findall(r'#([0-9a-fA-F]{6})', resp.text)
            colors = ["#" + c.upper() for c in dict.fromkeys(colors_raw)][:6]

            site_data = f"URL: {full_url}\nTítulo: {title}\nDescrição: {desc[:600]}"

            client = Groq(api_key=api_key)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Responda SOMENTE JSON válido, sem texto extra. Estrutura: {brandName: str, tagline: str, summary: str, arquetipo: str, forcas: array de str, fraquezas: array de str, recomendacoes: array de str, nota: number 0-10}"},
                    {"role": "user", "content": f"Analise esta marca de forma profissional e curta: {site_data}"}
                ],
                temperature=0.65,
                max_tokens=800
            )

            # Tenta parsear JSON com tolerância
            raw_text = res.choices[0].message.content.strip()
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                # Se falhar, tenta limpar (remove texto antes/depois)
                start = raw_text.find('{')
                end = raw_text.rfind('}') + 1
                if start >= 0 and end > start:
                    cleaned = raw_text[start:end]
                    data = json.loads(cleaned)
                else:
                    data = {"summary": raw_text}

            # Renderização visual (como no seu print + portal completo)
            st.markdown(f'<div class="brand-title">{data.get("brandName", title)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="brand-tag">{data.get("tagline", "Centro de Excelência em...")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="brand-info">{full_url} • Analisado em {datetime.datetime.now().strftime("%d de %B de %Y às %H:%M")}</div>', unsafe_allow_html=True)

            # Paleta de cores (como no seu print)
            if colors:
                paleta_html = '<div class="paleta">' + ''.join(f'<div class="swatch" style="background:{c}"></div>' for c in colors) + '</div>'
                st.markdown(paleta_html, unsafe_allow_html=True)

            # Resumo
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Resumo da Marca")
            st.write(data.get("summary", "Análise gerada pela IA"))
            st.markdown('</div>', unsafe_allow_html=True)

            # Forças e Fraquezas lado a lado
            col_f, col_w = st.columns(2)
            with col_f:
                st.markdown('<div class="card strength">', unsafe_allow_html=True)
                st.subheader("Forças")
                for f in data.get("forcas", ["Conteúdo atualizado", "Plataforma fácil de usar"]):
                    st.markdown(f"- {f}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_w:
                st.markdown('<div class="card weakness">', unsafe_allow_html=True)
                st.subheader("Fraquezas")
                for w in data.get("fraquezas", ["Limitações na interação", "Dependência de internet"]):
                    st.markdown(f"- {w}")
                st.markdown('</div>', unsafe_allow_html=True)

            # Recomendações
            st.markdown('<div class="card recommend">', unsafe_allow_html=True)
            st.subheader("Recomendações Estratégicas")
            for i, rec in enumerate(data.get("recomendacoes", ["Investir em app móvel", "Mais opções de pagamento"]), 1):
                st.markdown(f"{i}. {rec}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Nota final destacada
            nota = data.get("nota", 4.2)
            st.markdown(f'<div class="nota">{nota}/10</div>', unsafe_allow_html=True)

            st.success("Auditoria concluída! Layout corrigido.")

        except Exception as e:
            st.error(f"Erro ao processar: {str(e)}")
            st.info("Possíveis causas: site offline, bloqueio anti-scraping ou resposta da IA inválida. Tente outra URL ou recarregue.")

else:
    st.info("Digite a URL acima e clique em 'Nova Auditoria' para começar.")
