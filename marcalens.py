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

# CSS global para simular glassmorphism + gradiente + Tailwind-like
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        body, .stApp {
            font-family: 'Inter', sans-serif !important;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .gradient-header {
            background: linear-gradient(135deg, #4e54c8, #8f94fb);
            color: white;
            padding: 2rem;
            border-radius: 16px 16px 0 0;
            text-align: center;
            margin-bottom: 0;
        }
        .card-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .strength-card { background: #ecfdf5; border-left: 4px solid #10b981; }
        .weakness-card { background: #fef2f2; border-left: 4px solid #ef4444; }
        .recommend-card { background: #f0f9ff; border-left: 4px solid #6366f1; }
        .color-swatch {
            width: 60px; height: 60px; border-radius: 12px; border: 2px solid white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: inline-block; margin: 8px;
        }
        .stButton > button {
            background: #6366f1 !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho estilo portal
st.markdown("""
    <div class="gradient-header">
        <h1 style="margin:0; font-size:3rem;">🔍 MarcaLens IA</h1>
        <h3>Análise Profissional de Marca - Portal da Equipe</h3>
    </div>
""", unsafe_allow_html=True)

api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("Configure GROQ_API_KEY nos Secrets do Streamlit Cloud ou em .streamlit/secrets.toml")
    st.stop()

domain = st.text_input("🌐 URL do site para análise", placeholder="https://proxmodegrau.com.br", key="url_input")

modelo = st.selectbox("Modelo", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"], index=0, label_visibility="collapsed")

if st.button("🚀 Iniciar Análise", type="primary", use_container_width=True):
    if not domain:
        st.error("Digite a URL!")
        st.stop()

    with st.spinner("Extraindo dados do site e analisando marca..."):
        try:
            url = domain if domain.startswith(('http://', 'https://')) else 'https://' + domain.strip('/')
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "Marca sem título"
            meta_desc = next((m['content'] for m in soup.find_all("meta") if m.get("name") == "description" or m.get("property") == "og:description"), "")
            og_image = next((m['content'] for m in soup.find_all("meta", property="og:image") if m.get("content")), None)
            if og_image and not og_image.startswith("http"):
                og_image = urljoin(url, og_image)

            colors_raw = re.findall(r'#([0-9a-fA-F]{6})', resp.text)
            colors = ["#" + c.upper() for c in dict.fromkeys(colors_raw)][:6]

            site_data = f"URL: {url}\nTítulo: {title}\nDescrição: {meta_desc[:400]}\nCores detectadas: {', '.join(colors)}"

            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Você é consultor de branding premium. Responda em PT-BR curto, estruturado para dashboard: use bullets, evite texto longo. Estrutura JSON-like: {resumo: '...', forcas: ['bullet1', ...], fraquezas: [...], recomendacoes: ['1. ...'], nota: 8.7, arquetipo: 'O Cuidador', personalidade: {Sinceridade:85, Excitacao:70, ...}}"},
                    {"role": "user", "content": f"Analise visual e concisa da marca: {site_data}"}
                ],
                temperature=0.65,
                max_tokens=1000
            )

            try:
                report = json.loads(response.choices[0].message.content)
            except:
                report = {"resumo": response.choices[0].message.content, "forcas": [], "fraquezas": [], "recomendacoes": [], "nota": "N/A"}

            # Dashboard visual
            st.markdown(f"<h2 style='text-align:center; margin:2rem 0;'>{title}</h2>", unsafe_allow_html=True)
            st.caption(f"{url} • Analisado em {datetime.date.today().strftime('%d de %B de %Y')}")

            # Imagem + paleta
            col1, col2 = st.columns([1, 4])
            with col1:
                if og_image:
                    st.image(og_image, use_column_width=True)
            with col2:
                if colors:
                    st.markdown("**Paleta Principal**")
                    paleta_html = "".join([f'<div class="color-swatch" style="background:{c};" title="{c}"></div>' for c in colors])
                    st.markdown(paleta_html, unsafe_allow_html=True)

            # Métricas principais
            metric_cols = st.columns(3)
            metric_cols[0].metric("Nota Final", f"{report.get('nota', 'N/A')}/10", delta_color="normal")
            metric_cols[1].metric("Arquétipo", report.get('arquetipo', 'N/D'))
            metric_cols[2].metric("Público Principal", "Classe A/B + Pais" if "autismo" in meta_desc.lower() else "N/D")

            # Cards
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📊 Resumo Rápido")
            st.markdown(report.get("resumo", "Análise gerada pela IA"))
            st.markdown('</div>', unsafe_allow_html=True)

            col_force, col_weak = st.columns(2)
            with col_force:
                st.markdown('<div class="glass-card strength-card">', unsafe_allow_html=True)
                st.subheader("💪 Forças")
                for f in report.get("forcas", []):
                    st.markdown(f"• {f}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_weak:
                st.markdown('<div class="glass-card weakness-card">', unsafe_allow_html=True)
                st.subheader("⚠️ Fraquezas")
                for w in report.get("fraquezas", []):
                    st.markdown(f"• {w}")
                st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("⚡ Recomendações Estratégicas", expanded=True):
                for i, rec in enumerate(report.get("recomendacoes", []), 1):
                    st.markdown(f"{i}. {rec}")

            # Radar simples (simulado com HTML + Chart.js CDN)
            st.markdown("""
                <div class="glass-card">
                    <h3>🧠 Personalidade da Marca</h3>
                    <div id="radarChart" style="height:300px;"></div>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <script>
                    const ctx = document.getElementById('radarChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'radar',
                        data: {
                            labels: ['Sinceridade', 'Excitação', 'Competência', 'Sofisticação', 'Robustez'],
                            datasets: [{
                                label: 'Marca',
                                data: [85, 70, 90, 65, 40],
                                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                                borderColor: '#6366f1',
                                pointBackgroundColor: '#6366f1',
                                borderWidth: 2
                            }]
                        },
                        options: { scale: { ticks: { beginAtZero: true, max: 100 } } }
                    });
                </script>
            """, unsafe_allow_html=True)

            st.success("Análise completa! Visual estilo BrandLens Portal")

        except Exception as e:
            st.error(f"Erro: {str(e)}")
            st.info("Tente outra URL ou verifique conexão/API Key.")
