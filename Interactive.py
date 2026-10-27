import os
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
    c: (
        c.replace("Electricity from ", "")
        .replace(" - TWh", "")
        .replace(" (TWh)", "")
    )
    for c in fuel_cols
}
df = df.rename(columns=clean_names)
sources = sorted(list(clean_names.values()))

# Upper limit: 2023 (fully reconciled records across all countries)
# Lower limit: 1985 (disaggregated technology tracking starts)
min_year = 1985
max_year = 2023

df = df[(df["Year"] >= min_year) & (df["Year"] <= max_year)].copy()
df[sources] = df[sources].fillna(0)

# Calculate totals and percentage shares
df["Total_TWh"] = df[sources].sum(axis=1)
for s in sources:
    df[f"{s}_pct"] = (df[s] / df["Total_TWh"].replace(0, 1)) * 100

key_entities = [
    "Australia",
    "Germany",
    "Indonesia",
    "United States",
    "China",
    "World",
]
available_entities = [e for e in key_entities if e in df["Entity"].unique()]

# Universal Colorblind-Safe Palette (Okabe-Ito derived)
accessible_palette = {
    "Coal": "#111111",      # Charcoal
    "Gas": "#E69F00",       # Orange
    "Oil": "#8B5A2B",       # Umber brown
    "Nuclear": "#0072B2",   # Dark Blue
    "Hydro": "#56B4E9",     # Sky Blue
    "Hydropower": "#56B4E9",
    "Wind": "#009E73",      # Green
    "Solar": "#F5C710",     # Deep Yellow
    "Bioenergy": "#CC79A7",  # Purple
    "Other renewables": "#777777", # Grey
}

def get_color(fuel_name):
    return next((col for k, col in accessible_palette.items() if k.lower() in fuel_name.lower()), "#555555")

# -------------------------------------------------------------
# CHART 1: COMBINED OVERVIEW
# -------------------------------------------------------------
fig_combined = go.Figure()

for e_idx, entity in enumerate(available_entities):
    sub = df[df["Entity"] == entity].sort_values("Year")
    is_visible = (e_idx == 0)
    for s in sources:
        fig_combined.add_trace(
            go.Scatter(
                x=sub["Year"],
                y=sub[s],
                mode="lines+markers",
                marker=dict(size=4.5, symbol="circle"),
                name=s,
                line=dict(width=2.2, color=get_color(s)),
                visible=is_visible,
                customdata=sub[f"{s}_pct"],
                hovertemplate=f"<b>{s}</b> (%{{x}}): %{{y:,.1f}} TWh (%{{customdata:.1f}}%)<extra></extra>",
                legendgroup=s
            )
        )

n_sources = len(sources)
n_entities = len(available_entities)

combined_country_buttons = []
for i, entity in enumerate(available_entities):
    vis = [False] * (n_entities * n_sources)
    for j in range(n_sources):
        vis[i * n_sources + j] = True
    combined_country_buttons.append(
        dict(label=f"Country: {entity}", method="update", args=[{"visible": vis}])
    )

y_twh_comb = []
y_pct_comb = []
for entity in available_entities:
    sub = df[df["Entity"] == entity].sort_values("Year")
    for s in sources:
        y_twh_comb.append(sub[s])
        y_pct_comb.append(sub[f"{s}_pct"])

combined_metric_buttons = [
    dict(
        label="Absolute Output (TWh)",
        method="update",
        args=[
            {"y": y_twh_comb},
            {"yaxis": {"title": "Electricity Output (TWh)", "autorange": True, "rangemode": "tozero"}}
        ]
    ),
    dict(
        label="Grid Share (%)",
        method="update",
        args=[
            {"y": y_pct_comb},
            {"yaxis": {"title": "Relative Share (%)", "range": [0, 100]}}
        ]
    )
]

fig_combined.update_layout(
    template="plotly_white",
    height=540,
    autosize=True,
    dragmode=False,  # Locks the canvas from accidental dragging
    margin=dict(t=50, b=70, l=60, r=40),
    hovermode="x unified",
    xaxis=dict(
        title="Year",
        range=[min_year, max_year],
        dtick=5,
        tickangle=0,
        showgrid=True,
        gridcolor="#EEEEEE",
        fixedrange=False
    ),
    yaxis=dict(
        title="Electricity Output (TWh)",
        showgrid=True,
        gridcolor="#EEEEEE",
        rangemode="tozero",
        fixedrange=True
    ),
    updatemenus=[
        dict(
            type="dropdown",
            direction="down",
            buttons=combined_country_buttons,
            x=0.0,
            y=1.14,
            xanchor="left",
            yanchor="bottom",
            bgcolor="#FFFFFF",
            bordercolor="#CCCCCC"
        ),
        dict(
            type="buttons",
            direction="left",
            buttons=combined_metric_buttons,
            showactive=True,
            x=1.0,
            y=1.14,
            xanchor="right",
            yanchor="bottom",
            bgcolor="#F5F5F5",
            bordercolor="#CCCCCC"
        )
    ],
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.22,
        xanchor="center",
        x=0.5,
        title=dict(text="<b>Fuel Source:</b>")
    )
)

# -------------------------------------------------------------
# CHART 2: FACETED SMALL MULTIPLES
# -------------------------------------------------------------
rows, cols = 3, 3
fig_faceted = make_subplots(
    rows=rows,
    cols=cols,
    subplot_titles=[f"<b>{s}</b>" for s in sources],
    shared_xaxes=True,
    vertical_spacing=0.10,
    horizontal_spacing=0.08
)

grid_positions = {}
for idx, s in enumerate(sources):
    grid_positions[s] = ((idx // cols) + 1, (idx % cols) + 1)

for e_idx, entity in enumerate(available_entities):
    sub = df[df["Entity"] == entity].sort_values("Year")
    is_visible = (e_idx == 0)

    for s in sources:
        r, c = grid_positions[s]
        fig_faceted.add_trace(
            go.Scatter(
                x=sub["Year"],
                y=sub[s],
                mode="lines+markers",
                marker=dict(size=3.5, symbol="circle"),
                name=s,
                line=dict(width=2.0, color=get_color(s)),
                visible=is_visible,
                customdata=sub[f"{s}_pct"],
                hovertemplate=f"<b>{s}</b><br>Year: %{{x}}<br>Output: %{{y:,.1f}} TWh<br>Share: %{{customdata:.1f}}%<extra></extra>",
                showlegend=False
            ),
            row=r, col=c
        )

faceted_country_buttons = []
for i, entity in enumerate(available_entities):
    vis = [False] * (n_entities * n_sources)
    for j in range(n_sources):
        vis[i * n_sources + j] = True
    faceted_country_buttons.append(
        dict(label=f"Country: {entity}", method="update", args=[{"visible": vis}])
    )

faceted_metric_buttons = [
    dict(
        label="Absolute Output (TWh)",
        method="restyle",
        args=[{"y": y_twh_comb}, [i for i in range(n_entities * n_sources)]]
    ),
    dict(
        label="Grid Share (%)",
        method="restyle",
        args=[{"y": y_pct_comb}, [i for i in range(n_entities * n_sources)]]
    )
]

fig_faceted.update_layout(
    template="plotly_white",
    height=680,
    autosize=True,
    dragmode=False,  # Locks canvas from accidental dragging
    margin=dict(t=50, b=50, l=50, r=30),
    updatemenus=[
        dict(
            type="dropdown",
            direction="down",
            buttons=faceted_country_buttons,
            x=0.0,
            y=1.12,
            xanchor="left",
            yanchor="bottom",
            bgcolor="#FFFFFF",
            bordercolor="#CCCCCC"
        ),
        dict(
            type="buttons",
            direction="left",
            buttons=faceted_metric_buttons,
            showactive=True,
            x=1.0,
            y=1.12,
            xanchor="right",
            yanchor="bottom",
            bgcolor="#F5F5F5",
            bordercolor="#CCCCCC"
        )
    ]
)

fig_faceted.update_yaxes(showgrid=True, gridcolor="#F2F2F2", rangemode="tozero", fixedrange=True)
fig_faceted.update_xaxes(
    showgrid=True,
    gridcolor="#F2F2F2",
    dtick=10,
    tickangle=0,
    range=[min_year, max_year],
    fixedrange=False
)

html_comb = fig_combined.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True, "displayModeBar": False}, div_id="plot_combined")
html_facet = fig_faceted.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True, "displayModeBar": False}, div_id="plot_faceted")

# -------------------------------------------------------------
# MASTER WEBPAGE WRAPPER WITH SYNCHRONIZED TIMELINE CONTROLLER
# -------------------------------------------------------------
final_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>National Electricity Transition Explorer</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 15px auto;
      max-width: 1060px;
      padding: 0 16px;
      color: #222;
      background-color: #ffffff;
    }}
    .header-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      border-bottom: 2px solid #eaeaea;
      padding-bottom: 12px;
      margin-bottom: 12px;
    }}
    .header-titles h1 {{
      margin: 0;
      font-size: 20px;
      color: #111;
    }}
    .header-titles p {{
      margin: 4px 0 0 0;
      font-size: 13px;
      color: #666;
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
      width: 120px;
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
    .view-switcher {{
      display: inline-flex;
      background-color: #ebebeb;
      border-radius: 6px;
      padding: 2px;
      gap: 3px;
    }}
    .view-btn {{
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 600;
      border: none;
      background: none;
      cursor: pointer;
      border-radius: 4px;
      color: #555;
      transition: all 0.2s ease-in-out;
    }}
    .view-btn.active {{
      background: #0072B2;
      color: #ffffff;
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }}
    .chart-panel {{
      display: block;
      width: 100%;
    }}
    .hidden {{
      display: none !important;
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

  <header class="header-bar">
    <div class="header-titles">
      <h1 id="main-title">Decarbonising the Grid: Electricity Transition ({min_year}–{max_year})</h1>
      <p id="sub-title">Tracking the structural shift from fossil baseloads to renewable power</p>
    </div>
    <div class="view-switcher" role="group" aria-label="Display View Switcher">
      <button class="view-btn active" id="btn-combined" onclick="switchView('combined')">Combined Overview</button>
      <button class="view-btn" id="btn-faceted" onclick="switchView('faceted')">Faceted Breakdown (Small Multiples)</button>
    </div>
  </header>

  <!-- Universal Synchronized Timeline Bar for BOTH Combined & Faceted Views -->
  <div class="timeline-bar">
    <div class="timeline-inputs">
      <span>Timeline Range:</span>
      <span id="start-label" style="color: #0072B2;">{min_year}</span>
      <input type="range" id="slider-start" min="{min_year}" max="{max_year}" value="{min_year}" oninput="syncTimeline()">
      <span>to</span>
      <input type="range" id="slider-end" min="{min_year}" max="{max_year}" value="{max_year}" oninput="syncTimeline()">
      <span id="end-label" style="color: #0072B2;">{max_year}</span>
    </div>

    <div class="era-presets">
      <button class="preset-btn" onclick="applyPreset(2015, {max_year})">Post-Paris (2015–{max_year})</button>
      <button class="preset-btn" onclick="applyPreset(2000, {max_year})">2000–{max_year}</button>
      <button class="preset-btn" onclick="applyPreset({min_year}, {max_year})">Full History ({min_year}–{max_year})</button>
    </div>
  </div>

  <main>
    <section id="panel-combined" class="chart-panel">
      {html_comb}
    </section>

    <section id="panel-faceted" class="chart-panel hidden">
      {html_facet}
    </section>

    <article class="accessibility-card">
      <strong>Accessibility Summary (Alt-Text):</strong>
      Interactive dashboard detailing electricity production across primary fuel sources from {min_year} to {max_year}.
      The main plotting canvas is locked to prevent accidental dragging. A dedicated timeline scrubber synchronously controls
      both the multi-fuel Combined Overview and the 9-panel Faceted Breakdown.
      <br><br>
      <strong>Intentional Interactivity Features:</strong>
      <ul style="margin: 6px 0 0 18px; padding: 0;">
        <li><strong>Canvas Drag Lock (<code>dragmode=False</code>):</strong> Disables canvas dragging so user interactions remain focused exclusively on intentional timeline filtering and hover inspection.</li>
        <li><strong>Cross-View Synchronized Timeline:</strong> Unified timeline slider dynamically updates the visible year boundaries across both the combined view and all 9 faceted subplots simultaneously.</li>
        <li><strong>Faceted Small Multiples:</strong> Resolves scale compression by separating low-magnitude clean fuels from legacy coal baselines.</li>
        <li><strong>Country Dropdown & Metric Switcher:</strong> Instantly compares national portfolios and switches between physical generation volume (TWh) and relative grid proportion (% Share).</li>
      </ul>
      <br><em>Data Source: Our World in Data (Ember & Energy Institute). Filtered to verified records ({min_year}–{max_year}).</em>
    </article>
  </main>

  <script>
    function switchView(viewName) {{
      const pCombined = document.getElementById('panel-combined');
      const pFaceted = document.getElementById('panel-faceted');
      const btnCombined = document.getElementById('btn-combined');
      const btnFaceted = document.getElementById('btn-faceted');

      if (viewName === 'combined') {{
        pCombined.classList.remove('hidden');
        pFaceted.classList.add('hidden');
        btnCombined.classList.add('active');
        btnFaceted.classList.remove('active');
        window.dispatchEvent(new Event('resize'));
      }} else {{
        pCombined.classList.add('hidden');
        pFaceted.classList.remove('hidden');
        btnCombined.classList.remove('active');
        btnFaceted.classList.add('active');
        window.dispatchEvent(new Event('resize'));
      }}
    }}

    function syncTimeline() {{
      let s = parseInt(document.getElementById('slider-start').value);
      let e = parseInt(document.getElementById('slider-end').value);

      if (s >= e) {{
        s = e - 1;
        document.getElementById('slider-start').value = s;
      }}

      document.getElementById('start-label').textContent = s;
      document.getElementById('end-label').textContent = e;

      // Update Combined Chart
      Plotly.relayout('plot_combined', {{ 'xaxis.range': [s, e] }});

      // Update all 9 axes on Faceted Chart
      let facetUpdate = {{}};
      for (let i = 1; i <= 9; i++) {{
        let key = (i === 1) ? 'xaxis.range' : 'xaxis' + i + '.range';
        facetUpdate[key] = [s, e];
      }}
      Plotly.relayout('plot_faceted', facetUpdate);
    }}

    function applyPreset(start, end) {{
      document.getElementById('slider-start').value = start;
      document.getElementById('slider-end').value = end;
      syncTimeline();
    }}
  </script>
</body>
</html>
"""

with open("module9_interactive.html", "w", encoding="utf-8") as f:
    f.write(final_page)

print("Saved clean, locked-canvas dashboard to module9_interactive.html!")