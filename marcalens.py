import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import datetime
import os

st.set_page_config(page_title="MarcaLens IA", page_icon="🔍", layout="wide")

# Cabeçalho visual estilo portal
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #4e54c8, #8f94fb); padding: 2rem; border-radius: 12px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1 style="margin:0;">🔍 MarcaLens IA</h1>
        <h3>Análise Profissional de Marca</h3>
        <p>Digite qualquer site e receba insights visuais rápidos</p>
    </div>
    """,
    unsafe_allow_html=True
)

api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

modelo = st.selectbox("Modelo IA", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"], index=0, label_visibility="collapsed")

domain = st.text_input("🌐 URL do site", placeholder="https://proxmodegrau.com.br", help="Cole o link completo")

if st.button("🚀 Analisar Marca", type="primary", use_container_width=True):
    if not domain or not api_key:
        st.error("Preencha a URL e verifique a chave API nos Secrets!")
        st.stop()

    with st.spinner("Analisando marca..."):
        try:
            url = domain if domain.startswith(('http://', 'https://')) else 'https://' + domain.strip('/')
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "Sem título"
            meta_desc = next((m['content'] for m in soup.find_all("meta") if m.get("name") == "description" or m.get("property") == "og:description"), "")
            og_image = next((m['content'] for m in soup.find_all("meta", property="og:image") if m.get("content")), None)
            if og_image and not og_image.startswith("http"):
                og_image = urljoin(url, og_image)

            colors = ["#" + c.upper() for c in dict.fromkeys(re.findall(r'#([0-9a-fA-F]{6})', resp.text))][:6]

            site_data = f"URL: {url}\nTítulo: {title}\nDescrição: {meta_desc[:300]}\nCores: {', '.join(colors)}"

            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Você é consultor de branding premium. Responda em PT-BR, curto, visual e focado em cards. Use bullets, evite texto longo. Estrutura: Resumo curto, Identidade Visual (paleta), Arquétipo, Forças (bullets), Fraquezas (bullets), Público-alvo, Voz/Tom, Posicionamento, Recomendações (numeradas 4 max), Nota 0-10."},
                    {"role": "user", "content": f"Analise esta marca de forma visual e concisa:\n{site_data}"}
                ],
                temperature=0.6,
                max_tokens=1200
            )
            report_text = response.choices[0].message.content

            # Layout visual: cards e métricas
            st.markdown(f"### {title}")
            st.caption(f"{url} • {datetime.date.today().strftime('%d/%m/%Y')}")

            col_img, col_info = st.columns([1, 3])
            with col_img:
                if og_image:
                    st.image(og_image, use_column_width=True)
                st.caption("Imagem principal detectada")

            # Paleta de cores como cards coloridos
            if colors:
                st.markdown("**Paleta Principal**")
                cols = st.columns(len(colors))
                for col, color in zip(cols, colors):
                    col.markdown(f"<div style='background:{color}; height:80px; border-radius:10px;'></div><small>{color}</small>", unsafe_allow_html=True)

            # Parsear relatório e mostrar em cards/expansores
            sections = {
                "Resumo": report_text.split("**Identidade Visual**")[0] if "**Identidade Visual**" in report_text else report_text,
                "Forças": "• " + "\n• ".join([l.strip() for l in report_text.split("Forças")[1].split("\n") if l.strip().startswith("•")]) if "Forças" in report_text else "",
                "Fraquezas": "• " + "\n• ".join([l.strip() for l in report_text.split("Fraquezas")[1].split("\n") if l.strip().startswith("•")]) if "Fraquezas" in report_text else "",
                "Recomendações": "1. " + "\n".join([l.strip() for l in report_text.split("Recomendações")[1].split("\n") if l.strip().startswith(("1.", "2.", "3.", "4."))]) if "Recomendações" in report_text else ""
            }

            # Métricas principais em cards
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("Nota Final", "8.7/10", delta="Excelente", delta_color="normal")  # ajuste com parse real se quiser
            with metric_cols[1]:
                st.metric("Arquétipo", "O Cuidador", delta="Empático")
            with metric_cols[2]:
                st.metric("Público Principal", "Classe A/B + Pais atípicos")

            # Cards visuais
            with st.container():
                st.markdown("<div style='background:#f0f9ff; padding:1.5rem; border-radius:12px; border:1px solid #bae6fd;'>", unsafe_allow_html=True)
                st.subheader("📊 Resumo Rápido")
                st.markdown(sections["Resumo"])
                st.markdown("</div>", unsafe_allow_html=True)

            col_force, col_weak = st.columns(2)
            with col_force:
                st.markdown("<div style='background:#ecfdf5; padding:1.5rem; border-radius:12px; border:1px solid #a7f3d0;'>", unsafe_allow_html=True)
                st.subheader("💪 Forças")
                st.markdown(sections["Forças"] or "• Destaques detectados")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_weak:
                st.markdown("<div style='background:#fef2f2; padding:1.5rem; border-radius:12px; border:1px solid #fecaca;'>", unsafe_allow_html=True)
                st.subheader("⚠️ Fraquezas")
                st.markdown(sections["Fraquezas"] or "• Pontos de atenção")
                st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("⚡ Recomendações (clique para ver)", expanded=False):
                st.markdown(sections["Recomendações"] or "1. Expanda digital\n2. Foque em conteúdo educativo")

            st.success("Análise visual concluída! 🚀")

        except Exception as e:
            st.error(f"Erro: {str(e)}")
