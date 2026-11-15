"""
SupeRR Selector | IPL 2027 Pressure Performance Analytics
Run with:  streamlit run app.py

Folder layout:
    app.py
    Results/final_batter_ratings.csv
    Results/final_bowler_ratings.csv
    images/<player_name_in_lowercase_with_underscores>.jpg   (e.g. rinku_singh.jpg)
"""

import base64
import html
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

# ----------------------------------------------------------------------------
# PAGE SETUP
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="SupeRR Selector | Auction Intelligence",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).parent
PINK_DARK = "#880E4F"
PINK = "#C2185B"
NAVY = "#172554"

# Special file names for batters whose photo name differs from the player name
IMAGE_OVERRIDES = {
    "Namboori Tilak Varma": "images/tilak_varma.jpg",
}

# ----------------------------------------------------------------------------
# STYLING
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(135deg, #FCE4EF 0%, #F8BBD0 50%, #F48FB1 100%);
    color: #172554;
}
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, p, label { color: #172554 !important; }

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 2px solid #E91E63;
    padding: 20px;
    border-radius: 15px;
}
[data-testid="stMetricValue"] { color: #E91E63 !important; }

.stButton button {
    background: #E83E8C; color: white; border: none; border-radius: 10px;
}
.stButton button:hover {
    background: #C92772; color: white; border: 1px solid #FFFFFF;
}

.profile-card {
    background: white;
    padding: 25px;
    border-radius: 22px;
    box-shadow: 0 10px 25px rgba(194,24,91,0.15);
    margin-bottom: 15px;
}
.rating-number { color: #C2185B; font-size: 55px; font-weight: 900; line-height: 1.1; }
.stat-box {
    background: #FCE4EF;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    margin-bottom: 10px;
}
.stat-value { color: #C2185B; font-size: 25px; font-weight: bold; }
.placeholder-stage {
    background: linear-gradient(135deg, #FCE4EF, #F8BBD0, #EC407A);
    border-radius: 25px;
    height: 480px;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    box-shadow: 0 12px 35px rgba(194,24,91,0.25);
}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def slugify(name: str) -> str:
    """'Rishabh Pant' -> 'rishabh_pant'"""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def pretty(col: str) -> str:
    """'runs_pressure' -> 'Runs Pressure'"""
    return col.replace("_", " ").title()


def load_image(name: str):
    """Return (mime, base64) for a player's photo, or None if not found."""
    candidates = []
    if name in IMAGE_OVERRIDES:
        candidates.append(BASE_DIR / IMAGE_OVERRIDES[name])
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidates.append(BASE_DIR / "images" / f"{slugify(name)}.{ext}")

    for path in candidates:
        if path.exists():
            ext = path.suffix.lower().lstrip(".")
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext
            data = base64.b64encode(path.read_bytes()).decode()
            return mime, data
    return None


PLAYER_3D_TEMPLATE = """
<div class="scene">
  <div class="player-card" id="player">
    <div class="glow"></div>
    <img src="data:image/MIME;base64,IMAGE_DATA">
  </div>
</div>
<style>
body { margin: 0; }
.scene {
    width: 100%; height: 510px;
    display: flex; justify-content: center; align-items: center;
    perspective: 1000px;
    background: linear-gradient(135deg, #FCE4EF, #F8BBD0, #EC407A);
    border-radius: 25px; overflow: hidden;
    font-family: sans-serif;
}
.player-card {
    position: relative; width: 85%; height: 450px;
    display: flex; align-items: center; justify-content: center;
    transform-style: preserve-3d;
    transition: transform 0.12s ease-out;
}
.player-card img {
    height: 100%; max-width: 100%;
    object-fit: contain; object-position: center bottom;
    position: relative; z-index: 2;
    transform: translateZ(50px);
    filter: drop-shadow(12px 15px 12px rgba(70,0,30,0.4));
}
.glow {
    position: absolute; width: 220px; height: 220px;
    background: #EC407A; border-radius: 50%;
    filter: blur(65px); opacity: 0.5;
}
</style>
<script>
const card = document.getElementById("player");
const scene = document.querySelector(".scene");
scene.addEventListener("mousemove", (e) => {
    const r = scene.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width;
    const y = (e.clientY - r.top) / r.height;
    card.style.transform = "rotateX(" + ((0.5 - y) * 20) + "deg) rotateY(" + ((x - 0.5) * 30) + "deg)";
});
scene.addEventListener("mouseleave", () => {
    card.style.transform = "rotateX(0deg) rotateY(0deg)";
});
</script>
"""


def show_player_stage(name: str, role_label: str):
    """Show the 3D photo card, or a placeholder if no photo is found."""
    image = load_image(name)
    if image:
        mime, data = image
        page = (
            PLAYER_3D_TEMPLATE.replace("MIME", mime)
            .replace("IMAGE_DATA", data)
        )
        components.html(page, height=530, scrolling=False)
    else:
        st.markdown(
            f"""
            <div class="placeholder-stage">
                <h1 style="color:{PINK_DARK} !important;">{html.escape(name)}</h1>
                <h3 style="color:{PINK_DARK} !important;">{html.escape(role_label)}</h3>
                <p style="color:{PINK_DARK} !important;">Player photo coming soon</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def stat_box(value: str, label: str) -> str:
    return f'<div class="stat-box"><div class="stat-value">{value}</div><b>{label}</b></div>'


def rating_card(rating: float) -> str:
    return f"""
    <div class="profile-card">
        <p style="color:{PINK_DARK};font-weight:bold;">PRESSURE PERFORMANCE RATING</p>
        <div class="rating-number">{rating:.2f}</div>
        <p style="color:#777;">OUT OF 100</p>
    </div>
    """


def rating_chart(df: pd.DataFrame, name_col: str, title: str):
    fig = px.bar(
        df.sort_values("rating"),
        x="rating",
        y=name_col,
        orientation="h",
        text="rating",
        title=title,
        color_discrete_sequence=[PINK],
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(255,255,255,0.75)",
        font_color=NAVY,
        xaxis_title="Pressure Rating",
        yaxis_title="",
        showlegend=False,
    )
    return fig


# ----------------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    batters = pd.read_csv(BASE_DIR / "Results" / "final_batter_ratings.csv")
    bowlers = pd.read_csv(BASE_DIR / "Results" / "final_bowler_ratings.csv")
    return batters, bowlers


try:
    batters_df, bowlers_df = load_data()
except FileNotFoundError as err:
    st.error(f"Could not find a data file: {err}. Check the 'Results' folder.")
    st.stop()

top_batters = batters_df.sort_values("rating", ascending=False).head(10)
top_bowlers = bowlers_df.sort_values("rating", ascending=False).head(10)

# ----------------------------------------------------------------------------
# HEADER + KEY NUMBERS
# ----------------------------------------------------------------------------
st.title("🏏 SupeRR Selector")
st.subheader("IPL 2027 | Pressure Performance Analytics")



c1, c2, c3 = st.columns(3)
c1.metric("Total Deliveries", "194,014")
c2.metric("Pressure Deliveries", "48,751")
c3.metric("Players Ranked", "20")

st.divider()

# ----------------------------------------------------------------------------
# BATTER PROFILES
# ----------------------------------------------------------------------------
st.markdown("## ⭐ TOP 10 BATTER PROFILES")

selected_batter = st.selectbox("Select a Batter", top_batters["striker_name"].tolist())
b = top_batters[top_batters["striker_name"] == selected_batter].iloc[0]

st.markdown("## ⭐ PRESSURE STAR")
left, right = st.columns([1.1, 1])

with left:
    st.markdown(f"### {b['striker_name']}")
    show_player_stage(str(b["striker_name"]), "PRESSURE STAR")

with right:
    st.markdown(rating_card(float(b["rating"])), unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            stat_box(f"{int(b['runs_pressure']):,}", "Pressure Runs")
            + stat_box(f"{float(b['average_pressure']):.2f}", "Average"),
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            stat_box(f"{float(b['strike_rate_pressure']):.2f}", "Strike Rate")
            + stat_box(f"{int(b['matches_pressure'])}", "Matches"),
            unsafe_allow_html=True,
        )
    with st.expander("VIEW COMPLETE PLAYER ANALYSIS"):
        st.write("**Pressure Balls:**", int(b["balls_pressure"]))
        st.write("**Pressure Dismissals:**", int(b["dismissals_pressure"]))
        st.write("**Strike Rate Improvement:**", f"+{float(b['sr_improvement']):.2f}")

st.plotly_chart(
    rating_chart(top_batters, "striker_name", "⭐ TOP 10 PRESSURE BATTERS"),
    use_container_width=True,
)

st.divider()

# Top 10 Batter Table
with st.expander("See full batter table (Top 10)"):
    st.dataframe(
        top_batters,
        use_container_width=True,
        hide_index=True
    )
# ----------------------------------------------------------------------------
# BOWLER PROFILES
# ----------------------------------------------------------------------------
st.markdown("## 🎯 TOP 10 BOWLER PROFILES")

selected_bowler = st.selectbox("Select a Bowler", top_bowlers["bowler_name"].tolist())
w = top_bowlers[top_bowlers["bowler_name"] == selected_bowler].iloc[0]

left2, right2 = st.columns([1.1, 1])

with left2:
    st.markdown(f"### {w['bowler_name']}")
    show_player_stage(str(w["bowler_name"]), "PRESSURE BOWLER")

with right2:
    st.markdown(rating_card(float(w["rating"])), unsafe_allow_html=True)

    # Bowler stats: runs conceded, balls bowled, overs and economy under pressure
    runs_c = float(w["runs_pressure"])
    balls_b = float(w["balls_pressure"])
    overs = int(balls_b // 6) + (int(balls_b % 6) / 10)   # e.g. 65.2 overs
    economy = runs_c / balls_b * 6 if balls_b else 0.0

    # Find a wickets column automatically (any column with 'wicket' in its name)
    wicket_col = next((c for c in top_bowlers.columns if "wicket" in c.lower()), None)

    left_boxes = stat_box(f"{int(runs_c):,}", "Runs Conceded (Pressure)") + stat_box(
        f"{economy:.2f}", "Economy (Pressure)"
    )
    right_boxes = stat_box(f"{int(balls_b):,}", "Balls Bowled (Pressure)") + stat_box(
        f"{overs:.1f}", "Overs Bowled (Pressure)"
    )

    if wicket_col:
        wkts = int(w[wicket_col])
        bpw = f"{balls_b / wkts:.1f}" if wkts else "-"
        left_boxes = stat_box(f"{wkts}", "Wickets (Pressure)") + left_boxes
        right_boxes = stat_box(bpw, "Balls per Wicket") + right_boxes

    g1, g2 = st.columns(2)
    with g1:
        st.markdown(left_boxes, unsafe_allow_html=True)
    with g2:
        st.markdown(right_boxes, unsafe_allow_html=True)

    if not wicket_col:
        st.info("No wickets column found in final_bowler_ratings.csv, so wickets are not shown.")

st.plotly_chart(
    rating_chart(top_bowlers, "bowler_name", "🎯 TOP 10 PRESSURE BOWLERS"),
    use_container_width=True,
)

with st.expander("See full bowler table"):
    st.dataframe(top_bowlers, use_container_width=True, hide_index=True)

st.divider()



st.markdown("## 🧠 HOW WE RATED PLAYERS")

st.markdown("""
### 1. Identifying Pressure Situations

We classified a delivery as a pressure delivery when either condition was met:

- Death overs: Over 16 and above.
- Low wickets: Four or fewer wickets remaining.

**Dataset summary**
- Total deliveries: 194,014
- Pressure deliveries: 48,751
- Normal deliveries: 145,263

---

### 2. Batter Rating – 100 Points

| Performance factor | Weight |
|---|---:|
| Pressure Strike Rate | 30% |
| Pressure Average | 30% |
| Strike Rate Improvement | 25% |
| Pressure Runs | 15% |

### 3. Bowler Rating – 100 Points

| Performance factor | Weight |
|---|---:|
| Pressure Economy | 30% |
| Pressure Average | 25% |
| Pressure Wicket Rate | 20% |
| Economy Improvement | 15% |
| Pressure Wickets | 10% |

### 4. Player Eligibility

**Batters**
- Minimum 100 pressure balls.
- Minimum 10 pressure matches.
- At least one pressure dismissal.

**Bowlers**
- Minimum 60 pressure legal balls.
- Minimum 10 pressure matches.
- At least one pressure wicket.

### 5. Rating Interpretation

Player ratings are weighted percentile-based scores out of 100.
""")

st.markdown("---")

st.markdown("## 6. Release Players (Personal Opinion)")
st.markdown("""
1. Shimron Hetmyer
2. Adam Milne
3. Dasun Shanaka
4. Kwena Maphaka
""")

st.markdown("---")

st.markdown("## 7. Players to Target (Personal Opinion)")
st.markdown("""
1. Bevon Jacobs
2. Marcus Stoinis (if released)
3. Shai Hope
4. A quality pacer who can support Jofra Archer
""")

st.markdown("---")

st.markdown("## 8. Key Players – Current Squad (Personal Opinion)")
st.markdown("""
1. Donovan Ferreira
2. Vaibhav Sooryavanshi
3. Dhruv Jurel
4. Jofra Archer
5. Yashasvi Jaiswal
""")




# ----------------------------------------------------------------------------
# RR AUCTION STRATEGY INSIGHTS
# ----------------------------------------------------------------------------

st.divider()
st.markdown("## 🏆 RR AUCTION STRATEGY INSIGHTS")
st.markdown("### Data-driven shortlist for IPL 2027")

# Identify leading players
best_batter = top_batters.iloc[0]
best_bowler = top_bowlers.iloc[0]

# Batter with the highest pressure runs
most_runs = top_batters.loc[
    top_batters["runs_pressure"].idxmax()
]

# Bowler with the highest pressure wickets
wicket_col = next(
    (c for c in top_bowlers.columns if "wicket" in c.lower()),
    None
)

# Display four key insights
a, b, c, d = st.columns(4)

a.metric(
    "Top Rated Batter",
    best_batter["striker_name"],
    f'{best_batter["rating"]:.2f} Rating'
)

b.metric(
    "Top Rated Bowler",
    best_bowler["bowler_name"],
    f'{best_bowler["rating"]:.2f} Rating'
)

c.metric(
    "Most Pressure Runs",
    most_runs["striker_name"],
    f'{int(most_runs["runs_pressure"]):,} Runs'
)

if wicket_col:
    most_wickets = top_bowlers.loc[
        top_bowlers[wicket_col].idxmax()
    ]
    d.metric(
        "Most Pressure Wickets",
        most_wickets["bowler_name"],
        f'{int(most_wickets[wicket_col])} Wickets'
    )
else:
    d.metric("Pressure Wickets", "Not available")

st.markdown("### 📊 Auction Recommendations")

st.info(
    f'**Batting Target:** {best_batter["striker_name"]} '
    f'leads the batter rankings with a pressure rating of '
    f'{best_batter["rating"]:.2f}.'
)

st.info(
    f'**Bowling Target:** {best_bowler["bowler_name"]} '
    f'leads the bowler rankings with a pressure rating of '
    f'{best_bowler["rating"]:.2f}.'
)

st.info(
    f'**Batting Strength:** {most_runs["striker_name"]} '
    f'has scored the highest number of pressure runs '
    f'among the shortlisted batters.'
)

if wicket_col:
    st.info(
        f'**Bowling Strength:** {most_wickets["bowler_name"]} '
        f'has taken the most pressure wickets among the shortlisted bowlers.'
    )

st.info(
    f'**Subject:**  '
    f'The above player may be retained by their respective team.'
    f'I have analysed based on the dataset which has given'
)
