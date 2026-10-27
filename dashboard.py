import os
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Load data
csv_file = "electricity-production-by-source.csv"
if not os.path.exists(csv_file):
    raise FileNotFoundError(f"Missing {csv_file}")

df = pd.read_csv(csv_file)
df.columns = [c.strip() for c in df.columns]

meta_cols = ["Entity", "Code", "Year"]
fuel_cols = [c for c in df.columns if c not in meta_cols]

clean_names = {
    c: c.replace("Electricity from ", "").replace(" - TWh", "").replace(" (TWh)", "")
    for c in fuel_cols
}
df = df.rename(columns=clean_names)
sources = sorted(list(clean_names.values()))

min_year = 1985
max_year = 2023
df = df[(df["Year"] >= min_year) & (df["Year"] <= max_year)].copy()
df[sources] = df[sources].fillna(0)

# Categorize into Fossil vs Clean
fossil_fuels = [s for s in sources if any(k in s.lower() for k in ["coal", "gas", "oil"])]
clean_fuels = [s for s in sources if s not in fossil_fuels]

df["Total_TWh"] = df[sources].sum(axis=1)
df["Fossil_TWh"] = df[fossil_fuels].sum(axis=1)
df["Clean_TWh"] = df[clean_fuels].sum(axis=1)
df["Clean_Share_Pct"] = (df["Clean_TWh"] / df["Total_TWh"].replace(0, 1)) * 100
df["Fossil_Share_Pct"] = (df["Fossil_TWh"] / df["Total_TWh"].replace(0, 1)) * 100

for s in sources:
    df[f"{s}_pct"] = (df[s] / df["Total_TWh"].replace(0, 1)) * 100

key_entities = ["Australia", "Germany", "Indonesia", "United States", "China", "World"]
available_entities = [e for e in key_entities if e in df["Entity"].unique()]

# Universal Colorblind-Safe Palette (Okabe-Ito)
accessible_palette = {
    "Coal": "#222222",
    "Gas": "#E69F00",
    "Oil": "#8B5A2B",
    "Nuclear": "#0072B2",
    "Hydro": "#56B4E9",
    "Hydropower": "#56B4E9",
    "Wind": "#009E73",
    "Solar": "#F5C710",
    "Bioenergy": "#CC79A7",
    "Other renewables": "#777777"
}

def get_color(fuel_name):
    return next((col for k, col in accessible_palette.items() if k.lower() in fuel_name.lower()), "#555555")

# 2. Build 1x2 Subplot Layout
fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=[
        "<b>View A: Proportional Grid Mix (0–100%)</b>",
        "<b>View B: Absolute Generation Race (TWh)</b>"
    ],
    horizontal_spacing=0.12
)

n_entities = len(available_entities)
ordered_sources = fossil_fuels + clean_fuels
traces_per_country = len(ordered_sources) + 2

for e_idx, entity in enumerate(available_entities):
    sub = df[df["Entity"] == entity].sort_values("Year")
    is_visible = (e_idx == 0)

    # View A: 100% Stacked Area with white separation lines
    for s in ordered_sources:
        fig.add_trace(
            go.Scatter(
                x=sub["Year"],
                y=sub[f"{s}_pct"],
                mode="lines",
                line=dict(width=0.7, color="#FFFFFF"),
                stackgroup=f"stack_{entity}",
                name=s,
                fillcolor=get_color(s),
                visible=is_visible,
                legendgroup=s,
                showlegend=(e_idx == 0),
                customdata=sub[s],
                hovertemplate=f"<b>{s}</b> (%{{x}})<br>Share: %{{y:.1f}}%<br>Volume: %{{customdata:,.1f}} TWh<extra></extra>"
            ),
            row=1, col=1
        )

    # View B: Macro lines (Fossil vs Clean)
    fig.add_trace(
        go.Scatter(
            x=sub["Year"],
            y=sub["Fossil_TWh"],
            mode="lines+markers",
            marker=dict(size=4.5, symbol="circle"),
            name="All Fossil Fuels",
            line=dict(width=3, color="#222222"),
            visible=is_visible,
            legendgroup="All Fossil Fuels",
            showlegend=(e_idx == 0),
            hovertemplate="<b>All Fossil Fuels</b> (%{x})<br>Output: %{y:,.1f} TWh<extra></extra>"
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=sub["Year"],
            y=sub["Clean_TWh"],
            mode="lines+markers",
            marker=dict(size=4.5, symbol="diamond"),
            name="All Clean Energy",
            line=dict(width=3, color="#009E73"),
            visible=is_visible,
            legendgroup="All Clean Energy",
            showlegend=(e_idx == 0),
            hovertemplate="<b>All Clean Energy</b> (%{x})<br>Output: %{y:,.1f} TWh<extra></extra>"
        ),
        row=1, col=2
    )

# 3. Country Dropdown buttons with PERMANENT LEGEND VISIBILITY
country_buttons = []
for i, entity in enumerate(available_entities):
    vis = [False] * (n_entities * traces_per_country)
    for j in range(traces_per_country):
        vis[i * traces_per_country + j] = True
    
    # Keep showlegend True on the currently visible country's traces
    show_leg = [False] * (n_entities * traces_per_country)
    for j in range(traces_per_country):
        show_leg[i * traces_per_country + j] = True

    country_buttons.append(
        dict(
            label=f"Country: {entity}",
            method="update",
            args=[
                {"visible": vis, "showlegend": show_leg},
                {"title.text": f"<b>National Energy Transition Multiplot Dashboard: {entity} (1985–2023)</b>"}
            ]
        )
    )

fig.update_layout(
    title=dict(
        text=f"<b>National Energy Transition Multiplot Dashboard: {available_entities[0]} (1985–2023)</b>",
        font=dict(size=17, family="Arial, sans-serif"),
        x=0.01,
        y=0.98,
        xanchor="left"
    ),
    template="plotly_white",
    height=550,
    autosize=True,
    dragmode=False,
    margin=dict(t=80, b=90, l=60, r=30),
    hovermode="closest",
    updatemenus=[
        dict(
            type="dropdown",
            direction="down",
            buttons=country_buttons,
            x=0.99,
            y=1.14,
            xanchor="right",
            yanchor="bottom",
            bgcolor="#FFFFFF",
            bordercolor="#CCCCCC"
        )
    ],
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.20,
        xanchor="center",
        x=0.5
    )
)

fig.update_xaxes(showgrid=True, gridcolor="#EEEEEE", dtick=5, range=[min_year, max_year], title_text="Year", row=1, col=1)
fig.update_xaxes(showgrid=True, gridcolor="#EEEEEE", dtick=5, range=[min_year, max_year], title_text="Year", row=1, col=2)
fig.update_yaxes(title_text="Grid Share (%)", range=[0, 100], showgrid=True, gridcolor="#EEEEEE", row=1, col=1)
fig.update_yaxes(title_text="Generation Volume (TWh)", rangemode="tozero", showgrid=True, gridcolor="#EEEEEE", row=1, col=2)

html_chart = fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True, "displayModeBar": False}, div_id="multiplot_div")

# Prepare dynamic summary metrics JSON
kpi_data = {}
for entity in available_entities:
    sub = df[df["Entity"] == entity].sort_values("Year")
    latest = sub.iloc[-1]
    kpi_data[entity] = {
        "share": f"{latest['Clean_Share_Pct']:.1f}%",
        "clean_twh": f"{latest['Clean_TWh']:,.1f} TWh",
        "total_twh": f"{latest['Total_TWh']:,.1f} TWh"
    }

kpi_json = json.dumps(kpi_data)

alt_text = (
    "A two-panel juxtaposed multiplot display visualizing national electricity decarbonisation from 1985 to 2023. "
    "View A (Left) displays a 100 percent normalized stacked area chart showing proportional evolution across nine fuel sources. "
    "View B (Right) provides a complementary time-series line chart comparing aggregate fossil fuels directly against "
    "total clean power in Terawatt-hours (TWh). Synchronized timeline controls and dynamic country dropdowns enable exploration."
)

final_webpage = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>National Energy Transition Multiplot Dashboard</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 15px auto;
      max-width: 1100px;
      padding: 0 16px;
      color: #222;
      background-color: #ffffff;
    }}
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-bottom: 12px;
    }}
    .kpi-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 12px 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .kpi-title {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #64748b;
      font-weight: 600;
      margin-bottom: 4px;
    }}
    .kpi-value {{
      font-size: 22px;
      font-weight: 700;
      color: #0f172a;
    }}
    .kpi-note {{
      font-size: 12px;
      color: #009E73;
      font-weight: 500;
      margin-top: 2px;
    }}
    .timeline-bar {{
      background: #f8f9fa;
      border: 1px solid #e1e4e8;
      border-radius: 6px;
      padding: 10px 16px;
      margin-bottom: 12px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .timeline-inputs {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
    }}
    .timeline-inputs input[type="range"] {{
      width: 110px;
      cursor: pointer;
    }}
    .era-presets {{
      display: flex;
      gap: 6px;
    }}
    .preset-btn {{
      padding: 4px 10px;
      font-size: 12px;
      border: 1px solid #d0d7de;
      border-radius: 4px;
      background: #ffffff;
      cursor: pointer;
      font-weight: 500;
      color: #333;
    }}
    .preset-btn:hover {{
      background: #f3f4f6;
    }}
    .accessibility-card {{
      margin-top: 25px;
      padding: 14px 18px;
      background: #f8f9fa;
      border-left: 4px solid #0072B2;
      border-radius: 4px;
      font-size: 13px;
      line-height: 1.5;
    }}
  </style>
</head>
<body>

  <!-- Dynamic Live KPI Metric Cards -->
  <section class="kpi-row" aria-label="Summary KPIs">
    <div class="kpi-card">
      <div class="kpi-title">Clean Power Share (2023)</div>
      <div class="kpi-value" id="kpi-share">{kpi_data[available_entities[0]]['share']}</div>
      <div class="kpi-note">Renewables & Nuclear</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Clean Electricity Output</div>
      <div class="kpi-value" id="kpi-clean-twh">{kpi_data[available_entities[0]]['clean_twh']}</div>
      <div class="kpi-note">Solar, Wind, Hydro, Bio</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Total Grid Generation</div>
      <div class="kpi-value" id="kpi-total-twh">{kpi_data[available_entities[0]]['total_twh']}</div>
      <div class="kpi-note">Annual gross production</div>
    </div>
  </section>

  <!-- Synchronized Multiplot Timeline Controller -->
  <div class="timeline-bar">
    <div class="timeline-inputs">
      <span>Timeline Filter:</span>
      <span id="start-label" style="color: #0072B2;">{min_year}</span>
      <input type="range" id="slider-start" min="{min_year}" max="{max_year}" value="{min_year}" oninput="syncMultiplotTimeline()">
      <span>to</span>
      <input type="range" id="slider-end" min="{min_year}" max="{max_year}" value="{max_year}" oninput="syncMultiplotTimeline()">
      <span id="end-label" style="color: #0072B2;">{max_year}</span>
    </div>

    <div class="era-presets">
      <button class="preset-btn" onclick="applyMultiplotPreset(2015, {max_year})">Post-Paris (2015–{max_year})</button>
      <button class="preset-btn" onclick="applyMultiplotPreset(2000, {max_year})">2000–{max_year}</button>
      <button class="preset-btn" onclick="applyMultiplotPreset({min_year}, {max_year})">Full History ({min_year}–{max_year})</button>
    </div>
  </div>

  <main>
    <figure role="group" aria-label="Juxtaposed multiplot dashboard: Electricity transition" style="margin: 0;">
      {html_chart}
      <figcaption class="accessibility-card">
        <strong>Accessibility Summary & Alt-Text:</strong> {alt_text}
        <br><br>
        <strong>Multiplot Design & Juxtaposition Rationale:</strong>
        <ul style="margin: 6px 0 0 18px; padding: 0;">
          <li><strong>Juxtaposition of Complementary Perspectives:</strong> View A (Left) displays 100% normalized system composition (0–100%), highlighting the proportional substitution of fossil fuels by renewables. View B (Right) juxtaposes absolute physical output (TWh), revealing whether clean energy is genuinely displacing fossil fuels or merely augmenting a rapidly growing baseline.</li>
          <li><strong>Synchronized Cross-Plot Timeline:</strong> The unified timeline scrubber controls the X-axis for both subplots synchronously, allowing targeted historical era comparisons.</li>
          <li><strong>Dynamic Interactive Synchronization:</strong> Selecting a country dynamically updates both juxtaposed visualisations alongside the top summary KPI cards in real time.</li>
          <li><strong>Colorblind-Safe Okabe-Ito Palette:</strong> Visual encodings maintain high contrast across deuteranopia, protanopia, and tritanopia profiles.</li>
        </ul>
        <br><em>Data Source: Our World in Data (Ember & Energy Institute). Filtered to verified records (1985–2023).</em>
      </figcaption>
    </figure>
  </main>

  <script>
    const kpiLookup = {kpi_json};
    const plotDiv = document.getElementById('multiplot_div');

    if (plotDiv) {{
      plotDiv.on('plotly_update', function() {{
        setTimeout(() => {{
          const title = plotDiv.layout.title.text;
          for (const country in kpiLookup) {{
            if (title.includes(country)) {{
              document.getElementById('kpi-share').innerText = kpiLookup[country].share;
              document.getElementById('kpi-clean-twh').innerText = kpiLookup[country].clean_twh;
              document.getElementById('kpi-total-twh').innerText = kpiLookup[country].total_twh;
              break;
            }}
          }}
        }}, 50);
      }});
    }}

    function syncMultiplotTimeline() {{
      let s = parseInt(document.getElementById('slider-start').value);
      let e = parseInt(document.getElementById('slider-end').value);

      if (s >= e) {{
        s = e - 1;
        document.getElementById('slider-start').value = s;
      }}

      document.getElementById('start-label').textContent = s;
      document.getElementById('end-label').textContent = e;

      Plotly.relayout('multiplot_div', {{
        'xaxis.range': [s, e],
        'xaxis2.range': [s, e]
      }});
    }}

    function applyMultiplotPreset(start, end) {{
      document.getElementById('slider-start').value = start;
      document.getElementById('slider-end').value = end;
      syncMultiplotTimeline();
    }}
  </script>
</body>
</html>
"""

with open("module10_multiplot.html", "w", encoding="utf-8") as f:
    f.write(final_webpage)

print("Saved fixed multiplot dashboard with permanent legend to module10_multiplot.html!")