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
    Dokumentasi ini menjelaskan logika dan cara kerja dari aplikasi **Regional Churn Quadrant Analyzer**.
    
    ### 1. Sumber Data Otomatis
    Aplikasi ini terhubung langsung secara *live* dengan file data di repository GitHub, sehingga dashboard langsung tersaji tanpa perlu repot *upload* file secara manual setiap dibuka.
    
    ### 2. Klasifikasi 4 Kuadran
    * **Q1 - High Impact**: Churn Rate > Nasional DAN Churn Sub > Median (Prioritas Utama).
    * **Q2 - High Rate**: Churn Rate > Nasional DAN Churn Sub $\le$ Median.
    * **Q3 - High Volume**: Churn Rate $\le$ Nasional DAN Churn Sub > Median.
    * **Q4 - Low**: Churn Rate $\le$ Nasional DAN Churn Sub $\le$ Median.
    """)
  st.stop()

# --- HALAMAN UTAMA ---
st.title("📊 Regional Churn Quadrant Analyzer")
st.write(
    "Dashboard analisis sebaran kuadran wilayah berdasarkan data terbaru yang"
    " terhubung langsung dari GitHub."
)

# URL Raw CSV dari GitHub kamu
GITHUB_CSV_URL = "https://raw.githubusercontent.com/dhy-519/cbn-churn_rate_quadrant/refs/heads/main/Churn%20Quadrant.csv"

try:
  # Membaca data langsung dari link GitHub
  df = pd.read_csv(GITHUB_CSV_URL)

  # Membersihkan nama kolom
  df.columns = df.columns.str.strip()

  # Validasi kolom wajib
  required_cols = ["Region", "Churn Sub", "EOP"]
  missing_cols = [col for col in required_cols if col not in df.columns]

  if missing_cols:
    st.error(
        f"Format file di GitHub tidak sesuai! Kolom berikut tidak ditemukan:"
        f" {missing_cols}."
    )
  else:
    # Memisahkan baris Grand Total jika ada
    total_row_filter = (
        df["Region"]
        .astype(str)
        .str.contains("Grand Total|Total", case=False, na=False)
    )

    if total_row_filter.any():
      df_total = df[total_row_filter].iloc[0]
      total_churn_sub = float(df_total["Churn Sub"])
      total_eop = float(df_total["EOP"])
      df_regions = df[~total_row_filter].copy()
    else:
      df_regions = df.copy()
      total_churn_sub = df_regions["Churn Sub"].sum()
      total_eop = df_regions["EOP"].sum()

    # Konversi tipe data numerik
    df_regions["Churn Sub"] = pd.to_numeric(
        df_regions["Churn Sub"], errors="coerce"
    )
    df_regions["EOP"] = pd.to_numeric(df_regions["EOP"], errors="coerce")

    # Hitung Churn Rate per region (%)
    df_regions["Churn Rate (%)"] = (
        df_regions["Churn Sub"] / df_regions["EOP"]
    ) * 100

    # Hitung Sumbu X (Churn Rate Nasional dari Grand Total)
    national_churn_rate = (
        (total_churn_sub / total_eop) * 100 if total_eop > 0 else 0
    )

    # Hitung Sumbu Y (Median Churn Sub dari data region)
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

    # Tampilkan Metrik Titik Pembagi
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
      st.metric(
          label="Titik Pembagi X (Churn Rate Nasional)",
          value=f"{national_churn_rate:.2f}%",
      )
    with col2:
      st.metric(
          label="Titik Pembagi Y (Median Churn Sub)",
          value=f"{median_churn_sub:,.0f}",
      )
    st.markdown("---")

    # Range sumbu untuk background kuadran
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

    # Visualisasi Scatter Plot dengan Plotly
    st.subheader("🗺️ Peta Sebaran Kuadran Wilayah")
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
        title="Distribusi Kuadran Churn Berdasarkan Wilayah",
    )

    # Tambahkan background shapes kuadran
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

    # Garis pembagi median & nasional
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

    # Tampilkan Tabel Hasil Pemetaan
    st.subheader("📋 Tabel Rangkuman Hasil Kuadran")
    st.dataframe(
        df_regions[
            ["Region", "EOP", "Churn Sub", "Churn Rate (%)", "Kuadran"]
        ].style.format({"Churn Rate (%)": "{:.2f}%", "Churn Sub": "{:,.0f}"}),
        use_container_width=True,
    )

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
  st.error(
      f"Gagal memuat data dari GitHub. Pastikan link Raw URL sudah benar. Error:"
      f" {e}"
  )
