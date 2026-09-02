import datetime
import io
import pandas as pd
import plotly.express as px
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Regional Churn Quadrant Analyzer - Multi Periode",
    page_icon="📊",
    layout="wide",
)

# --- SIDEBAR: NAVIGASI & PENGATURAN TEMA ---
st.sidebar.title("Navigasi")
page = st.sidebar.radio(
    "Pilih Halaman:", ["Aplikasi Utama", "Technical Documentation"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Pengaturan Tampilan")
theme_mode = st.sidebar.radio("Mode Tema:", ["Light Mode", "Dark Mode"], index=0)

# Pengaturan styling dan warna berdasarkan pilihan tema
if theme_mode == "Dark Mode":
  st.markdown(
      """
        <style>
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        </style>
        """,
      unsafe_allow_html=True,
  )
  plotly_template = "plotly_dark"
  grid_color = "rgba(255, 255, 255, 0.1)"
  line_color = "#4E83EE"
  text_color = "#ffffff"
  bg_opacity = 0.2
else:
  st.markdown(
      """
        <style>
        .stApp {
            background-color: #ffffff;
            color: #31333F;
        }
        </style>
        """,
      unsafe_allow_html=True,
  )
  plotly_template = "plotly_white"
  grid_color = "lightgray"
  line_color = "#1f77b4"
  text_color = "#333333"
  bg_opacity = 0.25

if page == "Technical Documentation":
  st.title("📖 Technical Documentation")
  st.markdown("""
    Dokumentasi ini menjelaskan logika dan cara kerja dari aplikasi **Regional Churn Quadrant Analyzer (Multi-Periode)**.
    
    ### 1. Sumber Data & Multi-Periode
    Aplikasi membaca data historis yang memuat kolom `Period` (atau bulan), `Region`, `Churn Sub`, dan `EOP`. 
    
    ### 2. Klasifikasi 4 Kuadran per Periode
    * **Churn Rate (%)**: $\frac{\text{Churn Sub}}{\text{EOP}} \times 100$.
    * **Batas Sumbu X (Churn Rate Nasional)**: Dihitung dari akumulasi total seluruh wilayah pada periode terpilih.
    * **Batas Sumbu Y (Median Churn Sub)**: Nilai tengah dari sebaran `Churn Sub` pada periode tersebut.
    * **Q1 - High Impact** | **Q2 - High Rate** | **Q3 - High Volume** | **Q4 - Low**.
    """)
  st.stop()

# --- HALAMAN UTAMA ---
st.title("📊 Regional Churn Quadrant Analyzer")
st.write(
    "Analisis sebaran kuadran wilayah berdasarkan periode waktu dan tren"
    " pergerakan historis."
)

# Contoh struktur data multi-periode (atau kamu bisa menghubungkannya ke file CSV multi-periode di GitHub)
# Kamu dapat menyesuaikan atau membaca file CSV yang memiliki kolom 'Period'
@st.cache_data
def load_data():
  # Simulasi data multi-periode. Ganti bagian ini dengan pd.read_csv('url_github_anda.csv') jika datanya sudah multi-periode.
  data = [
      # Periode 2026-06
      {
          "Period": "2026-06",
          "Region": "JABEKA",
          "Churn Sub": 3200,
          "EOP": 44000,
      },
      {
          "Period": "2026-06",
          "Region": "SUMATRA UTARA",
          "Churn Sub": 2750,
          "EOP": 49500,
      },
      {
          "Period": "2026-06",
          "Region": "JAWA TIMUR",
          "Churn Sub": 2150,
          "EOP": 50500,
      },
      {
          "Period": "2026-06",
          "Region": "JAWA BARAT",
          "Churn Sub": 1950,
          "EOP": 34000,
      },
      {
          "Period": "2026-06",
          "Region": "BOGOR DEPOK",
          "Churn Sub": 1750,
          "EOP": 28500,
      },
      {"Period": "2026-06", "Region": "BALI", "Churn Sub": 1850, "EOP": 101000},
      {"Period": "2026-06", "Region": "BANTEN", "Churn Sub": 1650, "EOP": 42000},
      {
          "Period": "2026-06",
          "Region": "SUMATRA SELATAN",
          "Churn Sub": 1300,
          "EOP": 34000,
      },
      {
          "Period": "2026-06",
          "Region": "JAKARTA ARBI",
          "Churn Sub": 950,
          "EOP": 18500,
      },
      {
          "Period": "2026-06",
          "Region": "JAWA TENGAH",
          "Churn Sub": 580,
          "EOP": 15000,
      },
      {
          "Period": "2026-06",
          "Region": "SULAWESI SELATAN",
          "Churn Sub": 340,
          "EOP": 9000,
      },
      {"Period": "2026-06", "Region": "RIAU", "Churn Sub": 380, "EOP": 7600},
      {"Period": "2026-06", "Region": "LAMPUNG", "Churn Sub": 190, "EOP": 4000},
      {
          "Period": "2026-06",
          "Region": "KALIMANTAN SELATAN",
          "Churn Sub": 175,
          "EOP": 6000,
      },
      {
          "Period": "2026-06",
          "Region": "D.I. YOGYAKARTA",
          "Churn Sub": 75,
          "EOP": 2000,
      },
      # Periode 2026-07
      {
          "Period": "2026-07",
          "Region": "JABEKA",
          "Churn Sub": 3300,
          "EOP": 44100,
      },
      {
          "Period": "2026-07",
          "Region": "SUMATRA UTARA",
          "Churn Sub": 2800,
          "EOP": 49800,
      },
      {
          "Period": "2026-07",
          "Region": "JAWA TIMUR",
          "Churn Sub": 2200,
          "EOP": 51000,
      },
      {
          "Period": "2026-07",
          "Region": "JAWA BARAT",
          "Churn Sub": 2000,
          "EOP": 34200,
      },
      {
          "Period": "2026-07",
          "Region": "BOGOR DEPOK",
          "Churn Sub": 1800,
          "EOP": 28700,
      },
      {"Period": "2026-07", "Region": "BALI", "Churn Sub": 1900, "EOP": 101500},
      {"Period": "2026-07", "Region": "BANTEN", "Churn Sub": 1680, "EOP": 42100},
      {
          "Period": "2026-07",
          "Region": "SUMATRA SELATAN",
          "Churn Sub": 1330,
          "EOP": 34200,
      },
      {
          "Period": "2026-07",
          "Region": "JAKARTA ARBI",
          "Churn Sub": 965,
          "EOP": 18700,
      },
      {
          "Period": "2026-07",
          "Region": "JAWA TENGAH",
          "Churn Sub": 590,
          "EOP": 15200,
      },
      {
          "Period": "2026-07",
          "Region": "SULAWESI SELATAN",
          "Churn Sub": 345,
          "EOP": 9100,
      },
      {"Period": "2026-07", "Region": "RIAU", "Churn Sub": 385, "EOP": 7700},
      {"Period": "2026-07", "Region": "LAMPUNG", "Churn Sub": 193, "EOP": 4050},
      {
          "Period": "2026-07",
          "Region": "KALIMANTAN SELATAN",
          "Churn Sub": 178,
          "EOP": 6050,
      },
      {
          "Period": "2026-07",
          "Region": "D.I. YOGYAKARTA",
          "Churn Sub": 78,
          "EOP": 2050,
      },
      # Periode 2026-08 (Terbaru)
      {
          "Period": "2026-08",
          "Region": "JABEKA",
          "Churn Sub": 3392,
          "EOP": 44280,
      },
      {
          "Period": "2026-08",
          "Region": "SUMATRA UTARA",
          "Churn Sub": 2881,
          "EOP": 50100,
      },
      {
          "Period": "2026-08",
          "Region": "JAWA TIMUR",
          "Churn Sub": 2225,
          "EOP": 51200,
      },
      {
          "Period": "2026-08",
          "Region": "JAWA BARAT",
          "Churn Sub": 2028,
          "EOP": 34500,
      },
      {
          "Period": "2026-08",
          "Region": "BOGOR DEPOK",
          "Churn Sub": 1839,
          "EOP": 28900,
      },
      {"Period": "2026-08", "Region": "BALI", "Churn Sub": 1948, "EOP": 102400},
      {"Period": "2026-08", "Region": "BANTEN", "Churn Sub": 1716, "EOP": 42300},
      {
          "Period": "2026-08",
          "Region": "SUMATRA SELATAN",
          "Churn Sub": 1362,
          "EOP": 34500,
      },
      {
          "Period": "2026-08",
          "Region": "JAKARTA ARBI",
          "Churn Sub": 981,
          "EOP": 18900,
      },
      {
          "Period": "2026-08",
          "Region": "JAWA TENGAH",
          "Churn Sub": 603,
          "EOP": 15400,
      },
      {
          "Period": "2026-08",
          "Region": "SULAWESI SELATAN",
          "Churn Sub": 353,
          "EOP": 9200,
      },
      {"Period": "2026-08", "Region": "RIAU", "Churn Sub": 392, "EOP": 7800},
      {"Period": "2026-08", "Region": "LAMPUNG", "Churn Sub": 196, "EOP": 4100},
      {
          "Period": "2026-08",
          "Region": "KALIMANTAN SELATAN",
          "Churn Sub": 181,
          "EOP": 6100,
      },
      {
          "Period": "2026-08",
          "Region": "D.I. YOGYAKARTA",
          "Churn Sub": 80,
          "EOP": 2100,
      },
  ]
  return pd.DataFrame(data)


df_all = load_data()

# Dapatkan daftar periode yang tersedia, urutkan (terbaru di akhir/default)
periods = sorted(df_all["Period"].unique())
latest_period = periods[-1]

# --- KONTROL DROPDOWN PERIODE DI MAIN AREA ---
selected_period = st.selectbox(
    "Pilih Periode untuk Analisis Kuadran:",
    periods,
    index=len(periods) - 1,  # Default ke periode terbaru
)

# Filter data berdasarkan periode yang dipilih
df_current = df_all[df_all["Period"] == selected_period].copy()

# Kalkulasi metrik untuk periode terpilih
total_churn_sub = df_current["Churn Sub"].sum()
total_eop = df_current["EOP"].sum()
national_churn_rate = (
    (total_churn_sub / total_eop) * 100 if total_eop > 0 else 0
)
median_churn_sub = df_current["Churn Sub"].median()

df_current["Churn Rate (%)"] = (
    df_current["Churn Sub"] / df_current["EOP"]
) * 100


def assign_quadrant(row):
  cr = row["Churn Rate (%)"]
  cs = row["Churn Sub"]
  if cr > national_churn_rate and cs > median_churn_sub:
    return "Q1 - High Impact"
  elif cr > national_churn_rate and cs <= median_churn_sub:
    return "Q2 - High Rate"
  elif cr <= national_churn_rate and cs > median_churn_sub:
    return "Q3 - High Volume"
  else:
    return "Q4 - Low"


df_current["Kuadran"] = df_current.apply(assign_quadrant, axis=1)

# Tampilkan Metrik Pembagi
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
  st.metric(
      label=f"Titik Pembagi X (Churn Rate Nasional - {selected_period})",
      value=f"{national_churn_rate:.2f}%",
  )
with col2:
  st.metric(
      label=f"Titik Pembagi Y (Median Churn Sub - {selected_period})",
      value=f"{median_churn_sub:,.0f}",
  )
st.markdown("---")

# Visualisasi Scatter Plot
x_min = df_current["Churn Rate (%)"].min()
x_max = df_current["Churn Rate (%)"].max()
y_min = 0
y_max = df_current["Churn Sub"].max()
x_buffer = (x_max - x_min) * 0.05 if x_max > x_min else 1.0
y_buffer = y_max * 0.05

if theme_mode == "Light Mode":
  color_q1_bg = "rgba(255, 99, 132, 0.12)"
  color_q2_bg = "rgba(255, 159, 64, 0.12)"
  color_q3_bg = "rgba(255, 205, 86, 0.12)"
  color_q4_bg = "rgba(75, 192, 192, 0.12)"
else:
  color_q1_bg = "rgba(255, 77, 77, 0.2)"
  color_q2_bg = "rgba(255, 148, 77, 0.2)"
  color_q3_bg = "rgba(255, 219, 77, 0.2)"
  color_q4_bg = "rgba(77, 171, 77, 0.2)"

st.subheader(f"🗺️ Peta Sebaran Kuadran Wilayah (Periode {selected_period})")
fig = px.scatter(
    df_current,
    x="Churn Rate (%)",
    y="Churn Sub",
    text="Region",
    color="Kuadran",
    color_discrete_map={
        "Q1 - High Impact": "#ff4d4d",
        "Q2 - High Rate": "#ff944d",
        "Q3 - High Volume": "#ffdb4d",
        "Q4 - Low": "#4dab4d",
    },
    hover_data=["EOP"],
    title=f"Distribusi Kuadran Churn - {selected_period}",
)

# Shapes Latar Belakang Kuadran
fig.add_shape(
    type="rect",
    xref="x",
    yref="y",
    x0=x_min - x_buffer,
    y0=median_churn_sub,
    x1=national_churn_rate,
    y1=y_max + y_buffer,
    fillcolor=color_q3_bg,
    layer="below",
    line_width=0,
)
fig.add_shape(
    type="rect",
    xref="x",
    yref="y",
    x0=national_churn_rate,
    y0=median_churn_sub,
    x1=x_max + x_buffer,
    y1=y_max + y_buffer,
    fillcolor=color_q1_bg,
    layer="below",
    line_width=0,
)
fig.add_shape(
    type="rect",
    xref="x",
    yref="y",
    x0=x_min - x_buffer,
    y0=y_min,
    x1=national_churn_rate,
    y1=median_churn_sub,
    fillcolor=color_q4_bg,
    layer="below",
    line_width=0,
)
fig.add_shape(
    type="rect",
    xref="x",
    yref="y",
    x0=national_churn_rate,
    y0=y_min,
    x1=x_max + x_buffer,
    y1=median_churn_sub,
    fillcolor=color_q2_bg,
    layer="below",
    line_width=0,
)

fig.add_hline(
    y=median_churn_sub,
    line_dash="dash",
    line_color=line_color,
    annotation_text=f"Median Churn Sub: {median_churn_sub:,.0f}",
    annotation_position="bottom right",
    annotation_font=dict(color=text_color),
)
fig.add_vline(
    x=national_churn_rate,
    line_dash="dash",
    line_color=line_color,
    annotation_text=f"Churn Rate Nasional: {national_churn_rate:.2f}%",
    annotation_position="top left",
    annotation_font=dict(color=text_color),
)

fig.update_traces(textposition="top center", marker=dict(size=12, opacity=0.9))
fig.update_layout(
    height=600,
    template=plotly_template,
    font=dict(color=text_color),
    xaxis=dict(showgrid=True, gridcolor=grid_color),
    yaxis=dict(showgrid=True, gridcolor=grid_color),
)
st.plotly_chart(fig, use_container_width=True)

# --- TABEL PERGERAKAN HISTORIS DI BAWAH ---
st.markdown("---")
st.subheader("📈 Tabel Pergerakan Historis Wilayah Setiap Periode")

# Pilihan toggle antara Churn Rate atau Kuadran
table_mode = st.radio(
    "Pampilkan Tampilan Trend Berdasarkan:",
    ["Churn Rate (%)", "Posisi Kuadran"],
    horizontal=True,
)


# Fungsi untuk menyiapkan data pivot historis
def get_historical_pivot(mode):
  # Proses seluruh data untuk menghitung churn rate dan kuadran tiap periode
  processed_list = []
  for p in periods:
    df_p = df_all[df_all["Period"] == p].copy()
    tot_cs = df_p["Churn Sub"].sum()
    tot_eop = df_p["EOP"].sum()
    nat_rate = (tot_cs / tot_eop) * 100 if tot_eop > 0 else 0
    med_cs = df_p["Churn Sub"].median()

    df_p["Churn Rate (%)"] = (df_p["Churn Sub"] / df_p["EOP"]) * 100
    for _, row in df_p.iterrows():
      cr = row["Churn Rate (%)"]
      cs = row["Churn Sub"]
      if cr > nat_rate and cs > med_cs:
        quad = "Q1 - High Impact"
      elif cr > nat_rate and cs <= med_cs:
        quad = "Q2 - High Rate"
      elif cr <= nat_rate and cs > med_cs:
        quad = "Q3 - High Volume"
      else:
        quad = "Q4 - Low"

      val = f"{cr:.2f}%" if mode == "Churn Rate (%)" else quad
      processed_list.append(
          {"Region": row["Region"], "Period": row["Period"], "Value": val}
      )

  df_proc = pd.DataFrame(processed_list)
  df_pivot = df_proc.pivot(index="Region", columns="Period", values="Value")
  return df_pivot


df_trend = get_historical_pivot(table_mode)
st.dataframe(df_trend, use_container_width=True)
