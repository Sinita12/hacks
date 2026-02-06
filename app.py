

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
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🌿 GreenScore")    
    # Check if user clicked an alternative product
    if "impact_history" not in st.session_state:
        st.session_state.impact_history = pd.DataFrame(columns=[
            "Product", "Category", "Eco Score",
            "Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"
        ])
    if "logged_keys" not in st.session_state:
        st.session_state.logged_keys = set()
    
    # -----------------------------
    # Step 7: USER INPUT + DISPLAY
    # -----------------------------
    st.subheader("📸 Scan Product (optional)")
    
    image_file = st.camera_input("Take a photo of the product")
    
    if image_file:
        image = Image.open(image_file)
    
        with st.spinner("Reading packaging text..."):
            all_text = ocr_image(image)
        
        with st.spinner("Identifying product..."):
            detected_name = extract_product_name(all_text)
            matched_name, confidence = fuzzy_match_product(detected_name, summary_df)
        
        st.success(f"Detected: {matched_name}")
        st.session_state.selected_product = matched_name
    
    # -----------------------------
    # PRODUCT SEARCH (SINGLE SOURCE OF TRUTH)
    # -----------------------------
    product_options = sorted(summary_df["name"].unique())
    preselected_product = None
    
    # Priority:
    # 1. Alternative click
    # 2. Previously selected product
    if "selected_alternative" in st.session_state:
        preselected_product = st.session_state.selected_alternative
    elif "selected_product" in st.session_state:
        preselected_product = st.session_state.selected_product
    
    # -----------------------------
    # SINGLE SELECTBOX (NO DOUBLE CLICK)
    # -----------------------------
    if preselected_product in product_options:
        product_input = st.selectbox(
            "🔍 Search for a product",
            options=product_options,
            index=product_options.index(preselected_product),
            key="product_selectbox",
            placeholder="Start typing to search..."
        )
    else:
        product_input = st.selectbox(
            "🔍 Search for a product",
            options=product_options,
            index=None,
            key="product_selectbox",
            placeholder="Start typing to search..."
        )
    
    # -----------------------------
    # CLEAN UP ONE-TIME FLAGS
    # -----------------------------
    if "selected_alternative" in st.session_state:
        del st.session_state["selected_alternative"]
    
    # -----------------------------
    # PERSIST SELECTION (IMMEDIATE)
    # -----------------------------
    if product_input:
        st.session_state.selected_product = product_input
        result = summary_df[summary_df["name"] == product_input]
        if result.empty:
            st.error("❌ Product not found in database.")
        else:
            r = result.iloc[0]
            st.divider()
            
            # ---------- ECO SCORE ----------
            st.markdown("### 🌿 Eco Score")
            
            # Create a more visually appealing score display
            score_col1, score_col2 = st.columns([2, 3])
            
            with score_col1:
                # Large score display
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #2d5016 0%, #3d6b1f 100%);
                        border-radius: 18px;
                        padding: 30px;
                        text-align: center;
                        box-shadow: 0 8px 20px rgba(45, 80, 22, 0.3);
                    ">
                        <h1 style="color: #f5f1e8; margin: 0; font-size: 4em;">{r['eco_score']}</h1>
                        <p style="color: #c5d4b8; margin: 5px 0 0 0; font-size: 1.1em;">out of 100</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with score_col2:
                # Score interpretation
                if r['eco_score'] >= 80:
                    badge_color = "#2d5016"
                    badge_text = "Excellent"
                    emoji = "🌟"
                elif r['eco_score'] >= 60:
                    badge_color = "#4d7b2f"
                    badge_text = "Good"
                    emoji = "👍"
                elif r['eco_score'] >= 40:
                    badge_color = "#d4a373"
                    badge_text = "Moderate"
                    emoji = "⚠️"
                else:
                    badge_color = "#a85232"
                    badge_text = "Needs Improvement"
                    emoji = "❗"
                
                st.markdown(f"""
                    <div style="padding: 20px 0;">
                        <div style="
                            background-color: {badge_color};
                            color: #f5f1e8;
                            padding: 15px 25px;
                            border-radius: 14px;
                            display: inline-block;
                            font-size: 1.3em;
                            font-weight: bold;
                            margin-bottom: 15px;
                            box-shadow: 0 4px 12px rgba(45, 80, 22, 0.2);
                        ">
                            {emoji} {badge_text}
                        </div>
                        <p style="color: #9cb380; margin-top: 10px; line-height: 1.6;">
                            This score reflects the overall environmental impact across carbon, water, energy, and waste metrics.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Progress bar with custom styling
            st.markdown(f"""
                <div style="margin: 20px 0;">
                    <div style="
                        background-color: #3d4a35;
                        border-radius: 12px;
                        height: 14px;
                        overflow: hidden;
                    ">
                        <div style="
                            background: linear-gradient(90deg, #2d5016 0%, #4d7b2f 50%, #7c9070 100%);
                            width: {r['eco_score']}%;
                            height: 100%;
                            border-radius: 12px;
                            transition: width 0.5s ease;
                        "></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
            st.divider()
    
            # ---------- METRICS ----------
            st.markdown("### 📊 Environmental Impact Breakdown")
            
            col1, col2, col3, col4 = st.columns(4)
    
            with col1:
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #f5f1e8 0%, #faf8f3 100%);
                        border-left: 4px solid #d4a373;
                        border-radius: 12px;
                        padding: 20px 15px;
                        text-align: center;
                        box-shadow: 0 4px 12px rgba(45, 80, 22, 0.1);
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">🌫</div>
                        <div style="color: #5d4e37; font-size: 0.85em; margin-bottom: 5px; font-weight: 600;">Carbon Footprint</div>
                        <div style="color: #2d1810; font-size: 1.5em; font-weight: bold;">{r['total_carbon_kg']}</div>
                        <div style="color: #5d4e37; font-size: 0.75em;">kg CO₂e</div>
                    </div>
                """, unsafe_allow_html=True)
    
            with col2:
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f3 100%);
                        border-left: 4px solid #4d7b2f;
                        border-radius: 12px;
                        padding: 20px 15px;
                        text-align: center;
                        box-shadow: 0 4px 12px rgba(45, 80, 22, 0.1);
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">💧</div>
                        <div style="color: #2d5016; font-size: 0.85em; margin-bottom: 5px; font-weight: 600;">Water Usage</div>
                        <div style="color: #1a3d0f; font-size: 1.5em; font-weight: bold;">{r['total_water_L']}</div>
                        <div style="color: #2d5016; font-size: 0.75em;">Liters</div>
                    </div>
                """, unsafe_allow_html=True)
    
            with col3:
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #fff9e6 0%, #fffcf0 100%);
                        border-left: 4px solid #d4a373;
                        border-radius: 12px;
                        padding: 20px 15px;
                        text-align: center;
                        box-shadow: 0 4px 12px rgba(45, 80, 22, 0.1);
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">⚡</div>
                        <div style="color: #6b4423; font-size: 0.85em; margin-bottom: 5px; font-weight: 600;">Energy Use</div>
                        <div style="color: #3d2815; font-size: 1.5em; font-weight: bold;">{r['total_energy_MJ']}</div>
                        <div style="color: #6b4423; font-size: 0.75em;">MJ</div>
                    </div>
                """, unsafe_allow_html=True)
    
            with col4:
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #f5f1e8 0%, #faf8f3 100%);
                        border-left: 4px solid #7c9070;
                        border-radius: 12px;
                        padding: 20px 15px;
                        text-align: center;
                        box-shadow: 0 4px 12px rgba(45, 80, 22, 0.1);
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">🗑</div>
                        <div style="color: #3d4a35; font-size: 0.85em; margin-bottom: 5px; font-weight: 600;">Waste Impact</div>
                        <div style="color: #1a2318; font-size: 1.5em; font-weight: bold;">{r['total_waste_score']}</div>
                        <div style="color: #3d4a35; font-size: 0.75em;">Score</div>
                    </div>
                """, unsafe_allow_html=True)

            # ---------- INGREDIENT FLAGS (only show present ones) ----------
            st.markdown("### 🧪 Ingredient Flags")
            
            flag_defs = [
                {
                    "key": "microplastics",
                    "title": "Microplastics",
                    "emoji": "🧬",
                    "present": int(r["microplastics"]) == 1,
                    "why": "Microplastics can persist in waterways and harm aquatic life when washed down drains."
                },
                {
                    "key": "silicones",
                    "title": "Silicones",
                    "emoji": "🧴",
                    "present": int(r["silicones"]) == 1,
                    "why": "Some silicones are persistent and can contribute to long-lasting pollution in the environment."
                },
                {
                    "key": "petroleum",
                    "title": "Petroleum-derived",
                    "emoji": "🛢️",
                    "present": int(r["petroleum"]) == 1,
                    "why": "Petroleum-based ingredients come from fossil fuels, increasing reliance on non-renewable resources."
                },
            ]
            
            present_flags = [f for f in flag_defs if f["present"]]
            
            if present_flags:
                cols = st.columns(len(present_flags))
                for col, flag in zip(cols, present_flags):
                    with col:
                        st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, #fff4e6 0%, #f5f1e8 100%);
                                border-left: 4px solid #d4a373;
                                border-radius: 12px;
                                padding: 18px 14px;
                                box-shadow: 0 4px 12px rgba(45, 80, 22, 0.10);
                                min-height: 155px;
                            ">
                                <div style="font-size: 1.8em; margin-bottom: 6px;">{flag["emoji"]}</div>
                                <div style="font-weight: 700; font-size: 1.05em; color: #1a2318;">{flag["title"]} — Present</div>
                                <div style="margin-top: 10px; font-size: 0.9em; line-height: 1.45; color: #3d4a35;">
                                    {flag["why"]}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.success("✅ No ingredient red flags detected for this product (based on our database).")
    
            st.markdown("<br>", unsafe_allow_html=True)
    
            # ---------- OPTIONAL DETAILS ----------
            with st.expander("📊 View detailed data"):
                st.dataframe(result, use_container_width=True)
        
            st.divider()
            
            st.subheader("🛒 Purchase Logging")
            
            if st.button("✅ Log this product as purchased", use_container_width=True):
                log_key = f"{product_input}_{r['eco_score']}"
            
                if log_key not in st.session_state.logged_keys:
                    st.session_state.impact_history.loc[len(st.session_state.impact_history)] = {
                        "Product": product_input,
                        "Category": r["category"],
                        "Eco Score": r["eco_score"],
                        "Carbon (kg)": r["total_carbon_kg"],
                        "Water (L)": r["total_water_L"],
                        "Energy (MJ)": r["total_energy_MJ"],
                        "Waste Score": r["total_waste_score"]
                    }
                    st.session_state.logged_keys.add(log_key)
                    st.success("🎉 Product logged! Your Impact Dashboard has been updated.")
                else:
                    st.info("This product is already logged as purchased.")
            
            
            st.subheader("🌿 Greener Alternatives")
            st.caption("Click any product to view its full eco score")
            
            alternatives = get_greener_alternatives(product_input, summary_df, max_alternatives=5)
            
            # ✅ CASE 1: NO greener alternatives
            if not alternatives:
                st.success("🎉 Great choice! This is already one of the greenest options in its category.")
            
            # ✅ CASE 2: Greener alternatives exist
            else:
                for alt in alternatives:
                    col1, col2 = st.columns([4, 1])
            
                    with col1:
                        st.markdown(
                            f"""
                            <div style="
                                background: linear-gradient(135deg, #e8f5e9 0%, #f5f1e8 100%);
                                border-left: 5px solid #2d5016;
                                border-radius: 14px;
                                padding: 18px;
                                margin-bottom: 14px;
                                box-shadow: 0 4px 12px rgba(45, 80, 22, 0.15);
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="color:#1a3d0f; font-size:17px;">{alt['name']}</strong><br>
                                        <span style="color:#4d7b2f; font-size:14px;">✨ {alt['improvement']}</span>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color:#2d5016; font-size:26px; font-weight:700;">
                                            {alt['eco_score']}
                                        </div>
                                        <div style="color:#5d4e37; font-size:12px;">
                                            +{alt['score_diff']:.1f} points
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            
                    with col2:
                        if st.button("View →", key=f"view_{alt['name']}", use_container_width=True):
                            st.session_state['selected_alternative'] = alt['name']
                            st.rerun()



            # =============================
            # AI DEEP DIVE EXPLANATION
            # =============================
            # =============================
            # AI PRODUCT CHATBOT
            # =============================
            st.divider()
            st.subheader("🤖 AI Insight: Explore This Product")

            st.caption(
                "Ask in-depth questions about this product's ingredients, impacts, and "
                "how to make better purchase choices."
            )

            from openai import OpenAI
            client = OpenAI(api_key=st.secrets["OpenAIKey"])

            # -----------------------------
            # INIT / RESET PRODUCT CHAT MEMORY
            # -----------------------------
            if (
                "product_ai_messages" not in st.session_state
                or st.session_state.get("product_chat_product") != product_input
            ):
                st.session_state.product_chat_product = product_input
                
                # Use the actual selected product data (r) instead of hardcoded first product
                st.session_state.product_ai_messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a product-focused sustainability assistant.\n\n"
                            "You help users understand a SINGLE product in depth.\n\n"
                            "You may answer questions about:\n"
                            "- why this product scores the way it does\n"
                            "- ingredient and material impacts\n"
                            "- microplastics, silicones, petroleum, etc.\n"
                            "- what makes this product better or worse than alternatives\n"
                            "- what to look for when buying a greener option next time\n\n"
                            "Rules:\n"
                            "- Focus only on purchase-related advice\n"
                            "- No lifestyle tips\n"
                            "- Be specific to THIS product\n"
                            "- Do not invent data\n\n"
                            f"PRODUCT CONTEXT:\n"
                            f"Name: {r['name']}\n"
                            f"Category: {r['category']}\n"
                            f"Eco Score: {r['eco_score']} / 100\n"
                            f"Carbon: {r['total_carbon_kg']} kg CO₂e\n"
                            f"Water: {r['total_water_L']} L\n"
                            f"Energy: {r['total_energy_MJ']} MJ\n"
                            f"Waste Score: {r['total_waste_score']}\n"
                            f"Microplastics: {bool(int(r['microplastics']))}\n"
                            f"Silicones: {bool(int(r['silicones']))}\n"
                            f"Petroleum-derived: {bool(int(r['petroleum']))}"
                        ),
                    }
                ]

            # -----------------------------
            # DISPLAY CHAT
            # -----------------------------
            for msg in st.session_state.product_ai_messages[1:]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # -----------------------------
            # USER QUESTION INPUT
            # -----------------------------
            product_question = st.chat_input(
                "Ask about ingredients, impacts, or better alternatives for this product…"
            )

            if product_question:
                st.session_state.product_ai_messages.append(
                    {"role": "user", "content": product_question}
                )

                with st.chat_message("user"):
                    st.markdown(product_question)

                # -----------------------------
                # AI RESPONSE
                # -----------------------------
                with st.chat_message("assistant"):
                    with st.spinner("Thinking about this product… 🌍"):
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            temperature=0.4,
                            messages=st.session_state.product_ai_messages,
                        )

                        ai_reply = response.choices[0].message.content
                        st.markdown(ai_reply)

                st.session_state.product_ai_messages.append(
                    {"role": "assistant", "content": ai_reply}
                )



# -------------------------
# CHATBOT PAGE
# -------------------------

# -------------------------
# CHATBOT PAGE
# -------------------------

elif st.session_state.page == "Chatbot":

    import streamlit as st
    from openai import OpenAI

    # -----------------------------
    # INIT OPENAI CLIENT
    # -----------------------------
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # -----------------------------
    # PAGE SETUP
    # -----------------------------
    st.title("🤖 Eco Assistant")
    st.caption("Ask me about sustainability, eco scores, or greener choices 🌱")

    # -----------------------------
    # CHAT MEMORY
    # -----------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful sustainability assistant. "
                    "Give clear, practical, beginner-friendly answers. "
                    "Be concise and encouraging."
                )
            }
        ]

    # -----------------------------
    # DISPLAY CHAT
    # -----------------------------
    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # -----------------------------
    # USER INPUT
    # -----------------------------
    user_input = st.chat_input("Ask something eco-related...")

    if user_input:
        # show user message
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        # -----------------------------
        # OPENAI RESPONSE
        # -----------------------------
        with st.chat_message("assistant"):
            with st.spinner("Thinking 🌍"):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    temperature=0.6
                )

                assistant_reply = response.choices[0].message.content
                st.markdown(assistant_reply)

        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_reply}
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
                st.success(f"📈 Your EcoScore improved by **{delta:.1f} points** — your choices are getting greener 🌿")
            elif delta < -5:
                st.warning(f"📉 Your EcoScore dropped by **{abs(delta):.1f} points** — consider greener swaps 🔄")
            else:
                st.info("➖ Your EcoScore has stayed fairly stable — consistency is forming 🌱")

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
        st.session_state.impact_history = st.session_state.impact_history.iloc[0:0]

        # 🔑 also reset logging guards
        if "logged_keys" in st.session_state:
            st.session_state.logged_keys.clear()

        st.success("Impact history cleared 🌱")
        st.rerun()





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


    
