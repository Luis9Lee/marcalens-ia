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

# CSS inspirado no seu app React (glassmorphism + Inter font + gradientes)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        .stApp {
            font-family: 'Inter', sans-serif;
            background: #f8fafc;
        }
        .header-gradient {
            background: linear-gradient(135deg, #4e54c8, #8f94fb);
            color: white;
            padding: 2.5rem 2rem;
            border-radius: 0 0 24px 24px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(78,84,200,0.2);
        }
        .glass {
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 20px;
            padding: 1.8rem;
            box-shadow: 0 8px 32px rgba(31,38,135,0.15);
            margin-bottom: 1.5rem;
        }
        .strength { border-left: 5px solid #10b981; background: rgba(16,185,129,0.08); }
        .weakness { border-left: 5px solid #ef4444; background: rgba(239,68,68,0.08); }
        .recommend { border-left: 5px solid #6366f1; background: rgba(99,102,241,0.08); }
        .color-box {
            width: 50px; height: 50px; border-radius: 10px; border: 2px solid white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin: 0 8px 8px 0; display: inline-block;
        }
        .stButton > button {
            background: linear-gradient(90deg, #6366f1, #a855f7) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.8rem 1.6rem !important;
            font-weight: 600 !important;
        }
        h1, h2, h3 { color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho estilo portal
st.markdown("""
    <div class="header-gradient">
        <h1 style="margin:0; font-size:3.2rem;">BrandLens Portal</h1>
        <h3 style="margin:0.5rem 0 0; opacity:0.95;">Equipe Design & Marketing • Auditoria de Marca com IA</h3>
    </div>
""", unsafe_allow_html=True)

# Chave API (use secrets.toml ou Streamlit Cloud Secrets)
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Configure GROQ_API_KEY em .streamlit/secrets.toml ou no painel do Streamlit Cloud")
    st.stop()

# Input simples (sem sidebar por enquanto, como no seu portal)
col_input, col_btn = st.columns([5, 2])
with col_input:
    url = st.text_input("URL do site para auditoria", placeholder="https://proxmodegrau.com.br", key="url")
with col_btn:
    analisar = st.button("Nova Auditoria", type="primary", use_container_width=True, key="analisar")

if analisar and url:
    with st.spinner("Acessando site • Extraindo identidade • Gerando análise..."):
        try:
            full_url = url if url.startswith(('http://', 'https://')) else 'https://' + url
            resp = requests.get(full_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=18)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "Marca sem título detectado"
            desc = next((m['content'] for m in soup.find_all("meta") if m.get("name") == "description" or m.get("property") == "og:description"), "")
            og_img = next((m['content'] for m in soup.find_all("meta", property="og:image") if m.get("content")), None)
            if og_img and not og_img.startswith("http"):
                og_img = urljoin(full_url, og_img)

            colors = ["#" + c.upper() for c in dict.fromkeys(re.findall(r'#([0-9a-fA-F]{6})', resp.text))][:6]

            site_info = f"URL: {full_url}\nTítulo: {title}\nDescrição: {desc[:500]}\nCores principais: {', '.join(colors)}"

            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Você é especialista em branding. Responda em português do Brasil, formato JSON curto e estruturado para dashboard: {brandName, tagline, summary, arquetipo, visual: {cores: [{name, hex}], tipografia}, forcas: [array], fraquezas: [array], oportunidades: [array], ameacas: [array], recomendacoes: [array 1-4 itens], nota: numero 0-10, personalidade: {Sinceridade: int, Excitacao: int, Competencia: int, Sofisticacao: int, Robustez: int}}"},
                    {"role": "user", "content": f"Faça análise de marca profissional e concisa baseada neste site: {site_info}"}
                ],
                temperature=0.7,
                max_tokens=1400
            )

            try:
                data = json.loads(completion.choices[0].message.content)
            except:
                data = {"summary": completion.choices[0].message.content, "nota": "N/A"}

            # Layout do portal (muito próximo do seu React)
            st.markdown(f"<h2 style='text-align:center; margin:2.5rem 0 1rem;'>{data.get('brandName', title)}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:#64748b; font-size:1.1rem;'>{data.get('tagline', 'Centro de Excelência em...')}</p>", unsafe_allow_html=True)

            # Info principal
            st.markdown(f"<p style='text-align:center; color:#64748b;'>{full_url} • Analisado em {datetime.datetime.now().strftime('%d de %B de %Y às %H:%M')}</p>", unsafe_allow_html=True)

            # Imagem + paleta
            cols = st.columns([1, 4])
            with cols[0]:
                if og_img:
                    st.image(og_img, use_column_width=True)
            with cols[1]:
                if colors:
                    st.markdown("**Paleta detectada**")
                    st.markdown("".join(f'<div class="color-box" style="background:{c}"></div>' for c in colors), unsafe_allow_html=True)

            # Métricas rápidas
            mcols = st.columns(4)
            mcols[0].metric("Nota Final", f"{data.get('nota', 'N/A')}/10")
            mcols[1].metric("Arquétipo", data.get('arquetipo', 'N/D'))
            mcols[2].metric("Tipografia", data.get('visual', {}).get('tipografia', 'N/D'))
            mcols[3].metric("Público", "Pais e Responsáveis" if "autismo" in desc.lower() else "N/D")

            # Cards Forças x Fraquezas
            fc, wc = st.columns(2)
            with fc:
                st.markdown('<div class="glass strength">', unsafe_allow_html=True)
                st.subheader("Forças")
                for item in data.get("forcas", []):
                    st.markdown(f"- {item}")
                st.markdown('</div>', unsafe_allow_html=True)

            with wc:
                st.markdown('<div class="glass weakness">', unsafe_allow_html=True)
                st.subheader("Fraquezas")
                for item in data.get("fraquezas", []):
                    st.markdown(f"- {item}")
                st.markdown('</div>', unsafe_allow_html=True)

            # Recomendações
            st.markdown('<div class="glass recommend">', unsafe_allow_html=True)
            st.subheader("Recomendações Estratégicas")
            for i, rec in enumerate(data.get("recomendacoes", []), 1):
                st.markdown(f"**{i}.** {rec}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Radar de personalidade (Chart.js simples)
            personality = data.get("personalidade", {"Sinceridade": 80, "Excitação": 70, "Competência": 85, "Sofisticação": 60, "Robustez": 50})
            labels = list(personality.keys())
            values = list(personality.values())

            radar_js = f"""
            <div class="glass">
                <h3>Personalidade da Marca</h3>
                <canvas id="radar" height="300"></canvas>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                const ctx = document.getElementById('radar').getContext('2d');
                new Chart(ctx, {{
                    type: 'radar',
                    data: {{
                        labels: {json.dumps(labels)},
                        datasets: [{{
                            label: 'Marca',
                            data: {json.dumps(values)},
                            backgroundColor: 'rgba(99, 102, 241, 0.2)',
                            borderColor: '#6366f1',
                            pointBackgroundColor: '#6366f1',
                            borderWidth: 2
                        }}]
                    }},
                    options: {{ scale: {{ ticks: {{ beginAtZero: true, max: 100 }} }} }}
                }});
            </script>
            """
            st.markdown(radar_js, unsafe_allow_html=True)

            st.success("Auditoria concluída • Estilo Portal BrandLens")

        except Exception as e:
            st.error(f"Problema na análise: {str(e)}")
            st.info("Tente outra URL ou verifique se o site está online.")
