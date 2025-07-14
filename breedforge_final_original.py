
import streamlit as st
import os
from openai import OpenAI
import re
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# ----------------------
# 📄 PDF Generator
# ----------------------
def generate_pdf(mare_desc, sire_trait, traits, foal_name=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "BreedForge Foal Prediction Report")

    y -= 40
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Mare Description: {mare_desc}")
    y -= 20
    c.drawString(50, y, f"Sire Dominant Trait: {sire_trait}")

    if foal_name:
        y -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"✨ Suggested Foal Name: {foal_name}")

    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Predicted Foal Traits:")

    c.setFont("Helvetica", 12)
    for trait, values in traits.items():
        y -= 20
        label = f"{trait}: {values['rating']}"
        if values["score"]:
            label += f" ({values['score']}%)"
        c.drawString(60, y, label)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ----------------------
# 🔓 OpenAI Setup
# ----------------------
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ----------------------
# 🧠 Trait Extraction
# ----------------------
def extract_traits(text):
    traits = {}
    for line in text.split("\n"):
        match = re.search(r"(\w+)\s*[:\-]?\s*(Very High|High|Moderate|Medium|Low|Calm|Hot|Large|Small|[A-Za-z\s]+)?\s*\(?(\d{1,3})?%?\)?", line, re.IGNORECASE)
        if match:
            trait = match.group(1).capitalize()
            rating = match.group(2).strip() if match.group(2) else None
            score = int(match.group(3)) if match.group(3) else None
            traits[trait] = {"rating": rating, "score": score}
    return traits

# ----------------------
# 🖼 Logo Loading
# ----------------------
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_path = "breedforge_logo.png"
logo_base64 = get_base64_image(logo_path)

# ----------------------
# 🧱 Streamlit UI Setup
# ----------------------
st.set_page_config(page_title="BreedForge", page_icon="🐴")

st.markdown(
    f"""
    <div style='text-align: center; margin-bottom: 1rem;'>
        <img src="data:image/png;base64,{logo_base64}" width="160"/>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>
    .main {
        background-color: #f9f5ee;
        color: #2c2c2c;
    }
    .stButton>button {
        background-color: #8B4513;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("BreedForge: Foal Trait Predictor")
st.markdown("""
Welcome to the BreedForge prototype — an AI-powered genetics predictor that simulates likely traits in foals based on the mare’s description and sire’s dominant trait.
""")

# ----------------------
# 🐎 Mare Templates
# ----------------------
st.subheader("💡 Try a Prebuilt Mare Template")
col1, col2 = st.columns(2)

with col1:
    if st.button("🏇 Quarter Horse Sprinter"):
        st.session_state["mare_description"] = "Stocky, muscular build, calm under pressure, with powerful hindquarters and explosive speed"
    if st.button("🏜️ Arabian Endurance Mare"):
        st.session_state["mare_description"] = "Arabian mare with long stride, high endurance, intelligent temperament, and great stamina"

with col2:
    if st.button("🎯 Precision Cutting Mare"):
        st.session_state["mare_description"] = "Sharp reflexes, agile movement, responsive to cues, bred for cattle cutting and high-pressure scenarios"
    if st.button("🌾 Calm Ranch Broodmare"):
        st.session_state["mare_description"] = "Gentle temperament, reliable and calm, strong maternal instincts, excels in low-stress ranch environments"

# ----------------------
# 📥 Inputs
# ----------------------
mare_description = st.text_area("📝 Describe the Mare", value=st.session_state.get("mare_description", ""), placeholder="e.g. Calm temperament, strong legs, high endurance")
sire_trait = st.selectbox("🧬 Select Sire’s Dominant Trait", ["Speed", "Temperament", "Size", "Stamina", "Agility"])

# ----------------------
# Prediction & Output
# ----------------------
parsed_traits = None
output = None
foal_name = None
explanation = None

if st.button("🔮 Predict Foal Traits"):
    if not mare_description.strip():
        st.warning("Please enter a mare description before predicting.")
    else:
        with st.spinner("Simulating breeding outcomes..."):
            prompt = f"""
            You are an AI simulating horse genetics for breeding optimization.
            Based on this mare description: "{mare_description}"
            and a sire with dominant trait: "{sire_trait}",
            predict the likely traits of their foal in terms of temperament, physical build, and athletic potential.
            Keep it plausible and specific. List each trait with a rating and percentage where possible, like: Speed: High (85%).
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    max_tokens=300
                )
                output = response.choices[0].message.content.strip()
                st.success("Predicted Foal Traits:")
                parsed_traits = extract_traits(output)

                if parsed_traits:
                    st.subheader("🧬 Trait Scorecard")
                    for trait, values in parsed_traits.items():
                        label = f"{trait}: {values['rating']}"
                        if values["score"]:
                            st.progress(values["score"] / 100.0, text=label)
                        else:
                            st.write(f"- {label}")

                    # Optional: tag CRISPR-ready traits
                    crispr_targets = ["Speed", "Size", "Temperament"]
                    for trait in parsed_traits:
                        if trait in crispr_targets:
                            st.markdown(f"🧬 **{trait}** is flagged as CRISPR-editable in Phase II.")

                else:
                    st.markdown(output)

                st.markdown("""
                <div style="color: gray; font-size: 0.85em; margin-top: 1rem;">
                🔍 <i>This is a conceptual simulation powered by a large language model. Predictions are plausible, not biologically verified. Phase II will integrate real genomic data and CRISPR targeting.</i>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"OpenAI request failed: {e}")

# ----------------------
# 🐴 Foal Name Generator
# ----------------------
if st.button("🐴 Suggest Foal Name"):
    if not mare_description.strip():
        st.warning("Please enter the mare description first.")
    else:
        name_prompt = f"Suggest a strong, noble, or elegant name for a foal born from a mare like '{mare_description}' and a sire known for '{sire_trait}'."
        try:
            name_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": name_prompt}],
                temperature=0.7,
                max_tokens=50
            )
            foal_name = name_response.choices[0].message.content.strip()
            st.info(f"✨ Suggested Foal Name: **{foal_name}**")
        except Exception as e:
            st.error(f"Foal name generation failed: {e}")

# ----------------------
# 📄 PDF Download Option
# ----------------------
if parsed_traits:
    # Regenerate buffer on the spot — no session_state lag
    pdf_buffer = generate_pdf(
        mare_desc=mare_description,
        sire_trait=sire_trait,
        traits=parsed_traits,
        foal_name=foal_name
    )

    st.download_button(
        label="📥 Download Foal Report (PDF)",
        data=pdf_buffer.getvalue(),
        file_name="breedforge_foal_report.pdf",
        mime="application/pdf"
    )


# ----------------------
# 📊 Sidebar Roadmap
# ----------------------
st.sidebar.title("📍 BreedForge Roadmap")
st.sidebar.markdown("""
- ✅ Trait prediction via LLM (you’re here)
- 🧬 Genetic marker ingestion engine
- 🧪 AI + CRISPR editing strategy (Phase II)
- 📊 Foal trait outcome optimization (ML)
- 🐎 Global breeder marketplace integration
""")

with st.sidebar.expander("🧠 How This Works"):
    st.markdown("""
    BreedForge is currently powered by OpenAI's GPT-3.5-turbo model.  
    It uses natural language input to simulate expert reasoning about breeding outcomes.

    - Inputs: Mare description + Sire trait  
    - Logic: Prompt-based trait synthesis using LLM  
    - Output: Plausible foal characteristics based on genetic influence

    ⚠️ This is a prototype. No real genomic data or biological modeling is being used yet.
    """)

st.sidebar.markdown("""
**🚀 BreedForge Phase II**
- 🧬 Trait → Gene correlation mapping
- 📊 Data ingestion from breeding records
- ⚙️ Predictive modeling (ML + real phenotype/genotype pairs)
- 🧪 CRISPR editing simulation
- 🌐 Trait marketplace integration
""")
