

import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
import requests
st.set_page_config(page_title="EcoLens", page_icon="🌱", layout="wide")
st.markdown("""
<style>
.block-container { padding-top: 1rem !important; }

/* Sticky header box */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 999;
  background: #0e1117;   /* dark theme background */
  padding: 0.5rem 0 0.75rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)

GREENER_ALTERNATIVES = {
    "Cream": [
        {
            "name": "Minimalist Marula Oil Moisturizer",
            "reason": "Uses an aluminum tube instead of a plastic jar, reducing total plastic waste."
        },
        {
            "name": "Earth Rhythm Phyto Clear Moisturizer",
            "reason": "Packaged in a reusable glass jar with lower waste impact than PET."
        },
        {
            "name": "Plum Green Tea Moisturizer",
            "reason": "Smaller packaging size means less total material used."
        }
    ],
    "Body Wash": [
        {
            "name": "Ethique Solid Body Wash Bar",
            "reason": "Eliminates plastic bottles entirely by using a solid bar format."
        },
        {
            "name": "Earth Rhythm Body Wash Bar",
            "reason": "Zero plastic packaging results in near-zero packaging emissions."
        }
    ],
    "Sunscreen": [
        {
            "name": "Raw Beauty Wellness Sunscreen Stick",
            "reason": "Paper-based packaging avoids high-energy aluminum and plastic bottles."
        },
        {
            "name": "Dot & Key Sunscreen Stick",
            "reason": "Compact solid format reduces packaging weight significantly."
        },
        {
            "name": "Minimalist SPF 50 (50g)",
            "reason": "Smaller tube uses far less material than large sunscreen bottles."
        }
    ],
    "Shampoo": [
        {
            "name": "Ethique Shampoo Bar",
            "reason": "Solid shampoo bar completely removes the need for plastic bottles."
        },
        {
            "name": "Earth Rhythm Shampoo Bar",
            "reason": "Lower water and carbon footprint due to zero liquid packaging."
        },
        {
            "name": "Bare Anatomy Concentrated Shampoo",
            "reason": "Concentrated formula requires a smaller bottle."
        }
    ]
}


# -----------------------------
# Step 0: Define file paths
# -----------------------------
PRODUCT_CSV = "product.csv"
MATERIAL_CSV = "material.csv"

# -----------------------------
# Step 1: Read CSV files
# -----------------------------
products_df = pd.read_csv(PRODUCT_CSV)
materials_df = pd.read_csv(MATERIAL_CSV)

# Convert material impact dataframe to dictionary
material_impact_dict = {}
for _, row in materials_df.iterrows():
    material_impact_dict[row['material']] = {
        'carbon': row['carbon_kg_per_kg'],
        'water': row['water_L_per_kg'],
        'energy': row['energy_MJ_per_kg'],
        'waste': row['waste_score']
    }

# =============================
# MATERIAL IMPACT DICTIONARY
# =============================
material_impact_dict = {}
for _, row in materials_df.iterrows():
    material_impact_dict[row['material']] = {
        'carbon': row['carbon_kg_per_kg'],
        'water': row['water_L_per_kg'],
        'energy': row['energy_MJ_per_kg'],
        'waste': row['waste_score']  # 1–5 (higher = worse)
    }

# =============================
# INITIALIZE RESULT COLUMNS
# =============================
products_df['total_carbon_kg'] = 0.0
products_df['total_water_L'] = 0.0
products_df['total_energy_MJ'] = 0.0
products_df['total_waste_score'] = 0.0

# =============================
# COMPUTE ENVIRONMENTAL IMPACT
# =============================
for i, product in products_df.iterrows():
    total_carbon = 0.0
    total_water = 0.0
    total_energy = 0.0
    waste_scores = []

    for j in range(1, 4):
        material = product.get(f'material_{j}')
        weight_g = product.get(f'weight_{j}_g')

        if pd.isna(material) or pd.isna(weight_g):
            continue

        impact = material_impact_dict.get(material)
        if not impact:
            continue

        weight_kg = weight_g / 1000

        total_carbon += weight_kg * impact['carbon']
        total_water += weight_kg * impact['water']
        total_energy += weight_kg * impact['energy']

        # Waste is a material-type penalty (not mass-scaled)
        waste_scores.append(impact['waste'])

    products_df.at[i, 'total_carbon_kg'] = total_carbon
    products_df.at[i, 'total_water_L'] = total_water
    products_df.at[i, 'total_energy_MJ'] = total_energy
    products_df.at[i, 'total_waste_score'] = np.mean(waste_scores) if waste_scores else 0

# =============================
# NORMALIZATION CAPS (FIXED)
# =============================
CARBON_CAP = 0.5   # kg CO₂e
WATER_CAP = 10.0   # liters
ENERGY_CAP = 20.0  # MJ
WASTE_CAP = 5.0    # max material waste score

products_df['carbon_norm'] = (products_df['total_carbon_kg'] / CARBON_CAP).clip(0, 1)
products_df['water_norm'] = (products_df['total_water_L'] / WATER_CAP).clip(0, 1)
products_df['energy_norm'] = (products_df['total_energy_MJ'] / ENERGY_CAP).clip(0, 1)
products_df['waste_norm'] = (products_df['total_waste_score'] / WASTE_CAP).clip(0, 1)

# =============================
# FINAL ECOSCORE (0–100)
# =============================
products_df['eco_score'] = (
    (1 - products_df['carbon_norm']) * 0.35 +
    (1 - products_df['water_norm']) * 0.25 +
    (1 - products_df['energy_norm']) * 0.25 +
    (1 - products_df['waste_norm']) * 0.15
) * 100

products_df['eco_score'] = products_df['eco_score'].round(1)

# =============================
# FINAL SUMMARY TABLE (REQUIRED FOR GREEN SCORE PAGE)
# =============================
summary_df = products_df[[
    'name',
    'category',
    'total_carbon_kg',
    'total_water_L',
    'total_energy_MJ',
    'total_waste_score',
    'eco_score'
]].copy()


# -------------------------
# Navigation state
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def go(page_name: str):
    st.session_state.page = page_name

# -------------------------
# Sticky header (always visible)
# -------------------------
st.markdown('<div class="sticky-header">', unsafe_allow_html=True)

st.markdown(
    """
    <h1 style="text-align:center; font-size:72px; margin:0;">
        🌱 EcoLens
    </h1>
    <p style="text-align:center; font-size:18px; opacity:0.85; margin-top:6px; margin-bottom:14px;">
        Make smarter, sustainable buying decisions
    </p>
    """,
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    st.button("🌿 GreenScore", use_container_width=True, on_click=go, args=("GreenScore",))
with c2:
    st.button("🤖 AI Chatbot", use_container_width=True, on_click=go, args=("Chatbot",))
with c3:
    st.button("🌏Impact Dashboard", use_container_width=True, on_click=go, args=("Impact Dashboard",))
with c4:
    st.button("ℹ️ About", use_container_width=True, on_click=go, args=("About",))

st.markdown("</div>", unsafe_allow_html=True)
st.write("")  # spacer

# -------------------------
# HOME
# -------------------------
if st.session_state.page == "Home":

    left, right = st.columns([1.2, 1.8], gap="large")

    with left:
        st.markdown("""
            <div style="height:420px; overflow:hidden; border-radius:12px;">
                <img src="https://images.openai.com/static-rsc-3/L_9-L2VXhvFW5NZZvI6VLjA1QxHDiDeV5vyXsgKqM2ycJVtMFds_HEsJfhXYdziNs9fdDa4f0k4koZsaN3gehTxDddohscLt0wYAfwvMxRE?purpose=fullsize"
                     style="width:100%; height:100%; object-fit:cover;">
            </div>
        """, unsafe_allow_html=True)
    
    with right:
        st.markdown(
            """<div style="height:420px; display:flex; flex-direction:column; justify-content:center;">
    <h2 style="font-size:42px; margin-bottom:18px;">What is EcoLens?</h2>
    <p style="font-size:20px; line-height:1.7; max-width:680px;">
    EcoLens helps eco-conscious shoppers identify truly sustainable products by providing clear insights into a product’s sustainability impact.
    Scan a product, detect greenwashing, and get a clear <b>Green Score</b> with reasons.
    </p>
    </div>""",
            unsafe_allow_html=True
        )

    st.header("🚨 The Problem")
    st.write("Sustainability labels are vague and poorly regulated, so consumers often rely on marketing language instead of real data. Many of these claims are misleading, allowing greenwashing to go unnoticed. Because people lack the time and expertise to properly assess environmental impact, they make well-intentioned but poor choices. Additionally, there is no standardized way to verify eco-claims, and most existing apps reduce sustainability to simple green or red labels, hiding the real environmental costs of everyday products. As a result, people want to buy more environmentally friendly products but struggle to know which ones truly are.")
    

    st.header("✨ Key Features")

    components.html("""
<div style="
    background:#3f5a4d;
    border-radius:18px;
    padding:44px 38px;
    margin-top:18px;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
">
  <div style="display:flex; gap:34px; align-items:center;">

    <div style="flex:1.2;">
      <h2 style="margin:0 0 14px 0; font-size:38px; color:white;">
        🌿 GreenScore Tracker
      </h2>

      <p style="margin:0 0 14px 0; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
        Scan personal-care products and get a transparent sustainability score with clear reasons.
      </p>

      <ul style="margin:0; padding-left:20px; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
        <li>Barcode scan / product lookup</li>
        <li>Score breakdown (ingredients, packaging, claims)</li>
        <li>Greenwashing flags + simple explanations</li>
        <li>Better alternatives for your purpose</li>
      </ul>
    </div>

    <div style="flex:1; display:flex; justify-content:flex-end;">
      <div style="
          width:520px;
          height:320px;
          border-radius:16px;
          overflow:hidden;
          box-shadow: 0 10px 30px rgba(0,0,0,0.25);
          background: rgba(255,255,255,0.06);
      ">
        <img src="https://www.iberdrola.com/documents/20125/40513/huella-de-carbono-746x419.jpg/f61f98a2-7c51-27f9-31d2-41b1dafe6bf7?t=1738248418273"
             style="width:100%; height:100%; object-fit:cover;">
      </div>
    </div>

  </div>
</div>
""", height=420)


    
    #-------------------------
    # AI Chatbot
    #-------------------------

    components.html("""
    <div style="
        background:#15597e;   /* blueish */
        border-radius:18px;
        padding:44px 38px;
        margin-top:22px;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
    ">
      <div style="display:flex; gap:34px; align-items:center;">
    
        <!-- LEFT IMAGE -->
        <div style="flex:1; display:flex; justify-content:flex-start;">
          <div style="
              width:520px;
              height:320px;
              border-radius:16px;
              overflow:hidden;
              box-shadow: 0 10px 30px rgba(0,0,0,0.30);
              background: rgba(255,255,255,0.06);
          ">
            <img src="https://beetroot.co/wp-content/uploads/sites/2/2024/12/Cover_AI-chatbots-in-GreenTech.png"
                 style="width:100%; height:100%; object-fit:cover;">
          </div>
        </div>
    
        <!-- RIGHT TEXT -->
        <div style="flex:1.2;">
          <h2 style="margin:0 0 14px 0; font-size:38px; color:white;">
            🤖 AI Chatbot
          </h2>
    
          <p style="margin:0 0 14px 0; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            Ask questions in plain English and get smart, personalized sustainability advice instantly.
          </p>
    
          <ul style="margin:0; padding-left:20px; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            <li>Ask about ingredients and claims</li>
            <li>Detect greenwashing language</li>
            <li>Get product recommendations</li>
            <li>Tips for safer / sustainable swaps</li>
          </ul>
        </div>
    
      </div>
    </div>
    """, height=420)

    #---------------------
    # Impact Score
    #---------------------
  
    components.html("""
    <div style="
        background:#1c3b2b;   /* forest green */
        border-radius:18px;
        padding:44px 38px;
        margin-top:22px;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
    ">
      <div style="display:flex; gap:34px; align-items:center;">
    
        <!-- LEFT TEXT -->
        <div style="flex:1.2;">
          <h2 style="margin:0 0 14px 0; font-size:38px; color:white;">
            🌲 Impact Score
          </h2>
    
          <p style="margin:0 0 14px 0; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            See the real environmental impact of every purchase in clear, easy-to-understand metrics.
          </p>
    
          <ul style="margin:0; padding-left:20px; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            <li>Track carbon footprint savings</li>
            <li>Water & plastic reduction estimates</li>
            <li>Compare products side-by-side</li>
            <li>Visualize your eco progress over time</li>
          </ul>
        </div>
    
        <!-- RIGHT IMAGE -->
        <div style="flex:1; display:flex; justify-content:flex-end;">
          <div style="
              width:520px;
              height:320px;
              border-radius:16px;
              overflow:hidden;
              box-shadow: 0 10px 30px rgba(0,0,0,0.30);
              background: rgba(255,255,255,0.06);
          ">
            <img src="https://greenscoreapp.com/wp-content/uploads/2024/09/Empowering-Sustainability-Through-Innovation-image2-Green-Score.webp"
                 style="width:100%; height:100%; object-fit:cover;">
          </div>
        </div>
    
      </div>
    </div>
    """, height=420)

# -------------------------
# GREEN SCORE PAGE
# -------------------------
elif st.session_state.page == "GreenScore":
    import pandas as pd
    import streamlit as st

    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🌱 GreenScore")
    st.caption("Every product tells a story. Let’s read its footprint 🌍")

    # =============================
    # INIT GLOBAL HISTORY (ONCE)
    # =============================
    if "impact_history" not in st.session_state:
        st.session_state.impact_history = pd.DataFrame(columns=[
            "Product", "Category", "Eco Score",
            "Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"
        ])

    # =============================
    # PRODUCT SELECTION
    # =============================
    product_name = st.selectbox(
        "Select a product to analyse",
        summary_df["name"].unique()
    )

    row = summary_df[summary_df["name"] == product_name].iloc[0]

    st.divider()

    # =============================
    # ECO SCORE DISPLAY
    # =============================
    eco_score = row["eco_score"]

    st.markdown(
        f"""
        <div style="
        padding:1rem;
        border-radius:0.75rem;
        background:linear-gradient(135deg,#ecfdf5,#f0fdf4);
        border:1px solid #bbf7d0;
        text-align:center;
        ">
        <h2 style="margin:0;color:#065f46">Eco Score</h2>
        <h1 style="margin:0;color:#16a34a">{eco_score:.1f} / 100</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # =============================
    # IMPACT BREAKDOWN
    # =============================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("💨 Carbon", f"{row['total_carbon_kg']:.2f} kg")
    c2.metric("💧 Water", f"{row['total_water_L']:.0f} L")
    c3.metric("⚡ Energy", f"{row['total_energy_MJ']:.1f} MJ")
    c4.metric("🗑️ Waste", f"{row['total_waste_score']:.1f}")

    st.caption("Lower impact = happier planet 🌍")

    st.divider()

    # =============================
    # LOG PRODUCT (IMMEDIATELY + ONCE)
    # =============================
    log_key = f"{product_name}_{eco_score}"

    if "logged_keys" not in st.session_state:
        st.session_state.logged_keys = set()

    if log_key not in st.session_state.logged_keys:
        new_row = pd.DataFrame([{
            "Product": product_name,
            "Category": row["category"],
            "Eco Score": eco_score,
            "Carbon (kg)": row["total_carbon_kg"],
            "Water (L)": row["total_water_L"],
            "Energy (MJ)": row["total_energy_MJ"],
            "Waste Score": row["total_waste_score"]
        }])

        st.session_state.impact_history = pd.concat(
            [st.session_state.impact_history, new_row],
            ignore_index=True
        )

        st.session_state.logged_keys.add(log_key)

        st.success("🌱 Added to your impact journey")
    else:
        st.info("Already counted — this choice is remembered 🌿")

    st.divider()

    # =============================
    # FRIENDLY ECO INSIGHT
    # =============================
    if eco_score >= 80:
        st.success("🌟 Excellent choice — nature approves")
    elif eco_score >= 65:
        st.info("👍 Solid pick — better than average")
    elif eco_score >= 50:
        st.warning("⚠️ Moderate impact — greener alternatives exist")
    else:
        st.error("❗ Heavy footprint — consider switching")

    # =============================
    # NAVIGATION CTA
    # =============================
    st.markdown(
        """
        🌍 Curious how your choices add up?  
        👉 Head to the **Impact Dashboard** to see your planet story grow.
        """
    )




# -------------------------
# CHATBOT PAGE
# -------------------------

# -------------------------
# CHATBOT PAGE
# -------------------------

elif st.session_state.page == "Chatbot":

    from openai import OpenAI
    import streamlit as st

    st.title("ChatGPT-like clone")

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )



# -------------------------
# TOTAL IMPACT PAGE
# -------------------------
elif st.session_state.page == "Impact Dashboard":
    import pandas as pd
    import plotly.express as px

    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🌍 Your Sustainability Impact")
    st.caption("A living story of how your choices shape the planet 🌱")

    # =============================
    # REQUIRE HISTORY
    # =============================
    if "impact_history" not in st.session_state or st.session_state.impact_history.empty:
        st.info("Analyse products to start building your impact story 🌱")
        st.stop()

    history = st.session_state.impact_history.copy()

    st.divider()

    # =============================
    # 🌱 BIG SUMMARY METRICS
    # =============================
    avg_score = history["Eco Score"].mean()
    total_score = history["Eco Score"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average Eco Score", f"{avg_score:.1f} / 100")
    c2.metric("Products Logged", len(history))
    c3.metric("High-Eco Choices", (history["Eco Score"] >= 80).sum())
    c4.metric("Total Eco Score", int(total_score))

    st.divider()

    # =============================
    # 🌍 HUMAN IMPACT TRANSLATION
    # =============================
    avg_carbon = history["Carbon (kg)"].mean()
    avg_water = history["Water (L)"].mean()
    avg_energy = history["Energy (MJ)"].mean()

    st.markdown("## 🌍 What This Means for the Planet")

    st.markdown(f"""
🌱 **On average, your purchases cause:**

- 💨 **{avg_carbon:.2f} kg CO₂**  
  *(≈ charging a phone {int(avg_carbon*120)} times 📱)*

- 💧 **{avg_water:.1f} L water use**  
  *(≈ {int(avg_water/50)} quick showers 🚿)*

- ⚡ **{avg_energy:.1f} MJ energy demand**  
  *(≈ powering a home for hours 🔌)*

✨ *Small choices. Real consequences. Growing awareness.*
""")

    st.divider()

    # =============================
    # 📈 ECOSCORE TREND
    # =============================
    st.markdown("## 📈 Your EcoScore Journey")

    trend_fig = px.line(
        history.reset_index(),
        x=history.reset_index().index,
        y="Eco Score",
        markers=True,
        color_discrete_sequence=["#22c55e"]
    )
    trend_fig.update_layout(
        xaxis_title="Order of products analysed",
        yaxis_title="Eco Score"
    )

    st.plotly_chart(trend_fig, use_container_width=True)

    if len(history) >= 2:
        delta = history["Eco Score"].iloc[-1] - history["Eco Score"].iloc[0]
        if delta > 5:
            st.success("📈 Your choices are getting greener 🌿")
        elif delta < -5:
            st.warning("📉 Impact increasing — greener swaps help 🔄")
        else:
            st.info("➖ Consistency forming 🌱")

    st.divider()

    # =============================
    # 📊 AVERAGE IMPACT BREAKDOWN
    # =============================
    st.markdown("## 📊 What Impacts You the Most")

    impact_avg = history[
        ["Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"]
    ].mean().reset_index()

    impact_avg.columns = ["Impact Type", "Average Value"]

    impact_fig = px.bar(
        impact_avg,
        x="Impact Type",
        y="Average Value",
        color="Impact Type",
        color_discrete_sequence=px.colors.sequential.Greens
    )

    st.plotly_chart(impact_fig, use_container_width=True)

    st.divider()

    # =============================
    # 🔄 STACKED PRODUCT COMPARISON
    # =============================
    st.markdown("## 🔄 Compare Products by Impact")
    st.caption("See *why* a product scores better — not just the number 🌿")

    compare_products = st.multiselect(
        "Select products",
        history["Product"].unique(),
        default=list(history["Product"].unique()[:2])
    )

    if len(compare_products) >= 2:
        compare_df = history[history["Product"].isin(compare_products)]

        impact_cols = ["Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"]
        normalized = compare_df.copy()

        for col in impact_cols:
            max_val = normalized[col].max()
            normalized[col] = normalized[col] / max_val if max_val > 0 else 0

        stacked_fig = px.bar(
            normalized,
            x="Product",
            y=impact_cols,
            barmode="stack",
            color_discrete_sequence=px.colors.sequential.Greens
        )

        st.plotly_chart(stacked_fig, use_container_width=True)
    else:
        st.info("Select at least two products 🌱")

    st.divider()

    # =============================
    # 🏆 ECO STATUS
    # =============================
    st.markdown("## 🏆 Your Sustainability Status")

    if avg_score >= 80:
        st.success("🌟 Eco Hero — nature approves")
    elif avg_score >= 65:
        st.info("👍 Conscious Consumer")
    elif avg_score >= 50:
        st.warning("⚠️ Improving — momentum building")
    else:
        st.error("❗ High Impact — greener swaps needed")

    st.divider()

    # =============================
    # 📜 HISTORY TABLE
    # =============================
    st.markdown("## 📜 Your Impact Log")
    st.dataframe(history[::-1], use_container_width=True)

    if st.button("🗑️ Clear Impact History"):
        st.session_state.impact_history = history.iloc[0:0]
        st.success("Impact history cleared 🌱")




# -------------------------
# ABOUT PAGE
# -------------------------
elif st.session_state.page == "About":
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("ℹ️ About")

    st.write("Built by **The Quantum Crew** for TISB Hacks.")

    st.subheader("👥 Team")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### Pihu Gupta")
        st.caption("Backend & APIs")

    with col2:
        st.markdown("### Saanvi Khetan")
        st.caption("ML & Scoring")

    with col3:
        st.markdown("### Sinita Ray")
        st.caption("UX & Frontend")

    with col4:
        st.markdown("### Nivedha Sundar")
        st.caption("Product & Pitch")


    
