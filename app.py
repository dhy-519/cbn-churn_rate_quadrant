import datetime
import io
import pandas as pd
import plotly.express as px
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Regional Churn Quadrant Analyzer",
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
# Default index diset ke 1 (Dark Mode)
theme_mode = st.sidebar.radio(
    "Mode Tema:", ["Light Mode", "Dark Mode"], index=1
)

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
    Dokumentasi ini menjelaskan logika dan cara kerja dari aplikasi **Regional Churn Quadrant Analyzer**.
    
    ### 1. Perhitungan Spesifik Periode
    * **Titik Pembagi X (Churn Rate Nasional)**: Dihitung secara *weighted average* khusus dari total keseluruhan data pada periode yang sedang dipilih.
    * **Titik Pembagi Y (Median Churn Sub)**: Dihitung dari nilai tengah data wilayah pada periode yang sama.
    
    ### 2. Klasifikasi 4 Kuadran
    * **Q1 - High Impact**: Churn Rate > Nasional DAN Churn Sub > Median (Merah).
    * **Q2 - High Rate**: Churn Rate > Nasional DAN Churn Sub $\le$ Median (Oranye).
    * **Q3 - High Volume**: Churn Rate $\le$ Nasional DAN Churn Sub > Median (Kuning).
    * **Q4 - Low**: Churn Rate $\le$ Nasional DAN Churn Sub $\le$ Median (Hijau).
    """)
  st.stop()

# --- HALAMAN UTAMA ---
st.title("📊 Regional Churn Quadrant Analyzer")
st.write(
    "Analisis sebaran kuadran wilayah berdasarkan periode terpilih dan tren"
    " pergerakan historis."
)

# Link Raw CSV dari GitHub kamu
GITHUB_CSV_URL = "https://raw.githubusercontent.com/dhy-519/cbn-churn_rate_quadrant/refs/heads/main/Churn%20Quadrant.csv"


@st.cache_data(ttl=60)
def load_data_from_github(url):
  return pd.read_csv(url)


try:
  df_all = load_data_from_github(GITHUB_CSV_URL)
  df_all.columns = df_all.columns.str.strip()

  # Deteksi kolom periode
  period_col = None
  for col in ["Period", "Month", "Periode"]:
    if col in df_all.columns:
      period_col = col
      break

  if period_col:
    try:
      periods = sorted(
          df_all[period_col].unique(),
          key=lambda x: pd.to_datetime(x, format="%b-%y"),
      )
    except:
      periods = sorted(df_all[period_col].unique())

    # Default ke periode terbaru (elemen terakhir, misal Aug-26)
    selected_period = st.selectbox(
        "Pilih Periode Analisis:", periods, index=len(periods) - 1
    )
    df_current = df_all[df_all[period_col] == selected_period].copy()
  else:
    selected_period = "Terbaru"
    df_current = df_all.copy()

  # Bersihkan baris Grand Total jika terbawa
  total_row_filter = (
      df_current["Region"]
      .astype(str)
      .str.contains("Grand Total|Total", case=False, na=False)
  )
  if total_row_filter.any():
    df_regions = df_current[~total_row_filter].copy()
  else:
    df_regions = df_current.copy()

  # Konversi tipe data numerik
  df_regions["Churn Sub"] = pd.to_numeric(
      df_regions["Churn Sub"], errors="coerce"
  )
  df_regions["EOP"] = pd.to_numeric(df_regions["EOP"], errors="coerce")

  # Hitung Churn Rate per region (%)
  df_regions["Churn Rate (%)"] = (
      df_regions["Churn Sub"] / df_regions["EOP"]
  ) * 100

  # --- KALKULASI SPESIFIK HANYA UNTUK PERIODE TERPILIH ---
  total_churn_sub = df_regions["Churn Sub"].sum()
  total_eop = df_regions["EOP"].sum()
  national_churn_rate = (
      (total_churn_sub / total_eop) * 100 if total_eop > 0 else 0
  )
  median_churn_sub = df_regions["Churn Sub"].median()


  # Fungsi Penentu Kuadran
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


  df_regions["Kuadran"] = df_regions.apply(assign_quadrant, axis=1)

  # Tampilkan Metrik Pembagi untuk Periode Aktif
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

  # Range sumbu scatter plot
  x_min = df_regions["Churn Rate (%)"].min()
  x_max = df_regions["Churn Rate (%)"].max()
  y_min = 0
  y_max = df_regions["Churn Sub"].max()

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

  # Visualisasi Scatter Plot
  st.subheader(f"🗺️ Peta Sebaran Kuadran Wilayah ({selected_period})")
  fig = px.scatter(
      df_regions,
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

  # Tampilkan Tabel Rangkuman Periode Aktif
  st.subheader(f"📋 Tabel Rangkuman Hasil Kuadran ({selected_period})")
  st.dataframe(
      df_regions[
          ["Region", "EOP", "Churn Sub", "Churn Rate (%)", "Kuadran"]
      ].style.format({"Churn Rate (%)": "{:.2f}%", "Churn Sub": "{:,.0f}"}),
      use_container_width=True,
  )

  # --- TABEL TREND HISTORIS LINTAS PERIODE DI BAWAH ---
  if period_col and len(periods) > 1:
    st.markdown("---")
    st.subheader("📈 Tabel Tren Historis Wilayah (Lintas Periode)")

    table_mode = st.radio(
        "Pilih Jenis Tampilan Tren:",
        ["Churn Rate (%)", "Posisi Kuadran"],
        horizontal=True,
    )


    def get_historical_pivot(mode):
      processed_list = []
      for p in periods:
        df_p = df_all[df_all[period_col] == p].copy()
        df_p = df_p[
            ~df_p["Region"]
            .astype(str)
            .str.contains("Grand Total|Total", case=False, na=False)
        ]
        df_p["Churn Sub"] = pd.to_numeric(df_p["Churn Sub"], errors="coerce")
        df_p["EOP"] = pd.to_numeric(df_p["EOP"], errors="coerce")

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
              {"Region": row["Region"], "Period": row[period_col], "Value": val}
          )

      df_proc = pd.DataFrame(processed_list)
      df_pivot = df_proc.pivot(index="Region", columns="Period", values="Value")

      existing_periods = [p for p in periods if p in df_pivot.columns]
      df_pivot = df_pivot[existing_periods]
      return df_pivot


    df_trend = get_historical_pivot(table_mode)


    # Fungsi styling warna background untuk tabel kuadran
    def color_quadrant_cells(val):
      if table_mode == "Posisi Kuadran":
        if "Q1" in str(val):
          return "background-color: rgba(255, 77, 77, 0.4); color: white;"
        elif "Q2" in str(val):
          return "background-color: rgba(255, 148, 77, 0.4); color: white;"
        elif "Q3" in str(val):
          return "background-color: rgba(255, 219, 77, 0.4); color: black;"
        elif "Q4" in str(val):
          return "background-color: rgba(77, 171, 77, 0.4); color: white;"
      return ""


    if table_mode == "Posisi Kuadran":
      st.dataframe(
          df_trend.style.applymap(color_quadrant_cells),
          use_container_width=True,
      )
    else:
      st.dataframe(df_trend, use_container_width=True)

  # Fitur Download ke Excel
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_regions.to_excel(writer, index=False, sheet_name="Hasil Kuadran")
  processed_data = output.getvalue()

  default_filename = (
      f"rekap_pelanggan_update_{datetime.datetime.now().strftime('%Y-%m')}.xlsx"
  )
  st.download_button(
      label="📥 Download Hasil Rekap (Excel)",
      data=processed_data,
      file_name=default_filename,
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )

except Exception as e:
  st.error(f"Gagal memuat atau memproses data dari GitHub. Error: {e}")
