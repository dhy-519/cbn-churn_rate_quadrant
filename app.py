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

# Menerapkan style CSS dinamis berdasarkan pilihan tema
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
  # Warna background kuadran untuk tema gelap (sedikit lebih redup agar kontras)
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
  bg_opacity = 0.15

if page == "Technical Documentation":
  st.title("📖 Technical Documentation")
  st.markdown("""
    Dokumentasi ini menjelaskan logika dan cara kerja dari aplikasi **Regional Churn Quadrant Analyzer**.
    
    ### 1. Sumber Data & Format Input
    Aplikasi menerima file berformat **Excel (`.xlsx`)** atau **CSV (`.csv`)** yang memiliki kolom minimal:
    * `Region`: Nama wilayah/cabang.
    * `Churn Sub`: Jumlah pelanggan yang melakukan *churn*.
    * `EOP` (End of Period): Total jumlah pelanggan keseluruhan di wilayah tersebut.
    * Baris **Grand Total**: Diperlukan untuk kalkulasi batas sumbu X secara otomatis.
    
    ### 2. Logika Perhitungan Kuadran
    * **Churn Rate (%)**: Dihitung per baris dengan rumus $\frac{\text{Churn Sub}}{\text{EOP}} \times 100$.
    * **Batas Sumbu X (Churn Rate Nasional)**: Dihitung secara otomatis dari nilai *Grand Total* ($\frac{\text{Total Churn Sub}}{\text{Total EOP}} \times 100$).
    * **Batas Sumbu Y (Churn Sub Median)**: Menggunakan nilai titik tengah (*median*) dari kolom `Churn Sub` di seluruh region.
    
    ### 3. Klasifikasi 4 Kuadran
    * **Q1 - High Impact**: Churn Rate > Nasional DAN Churn Sub > Median (Prioritas Utama).
    * **Q2 - High Rate**: Churn Rate > Nasional DAN Churn Sub $\le$ Median.
    * **Q3 - High Volume**: Churn Rate $\le$ Nasional DAN Churn Sub > Median.
    * **Q4 - Low**: Churn Rate $\le$ Nasional DAN Churn Sub $\le$ Median.
    """)
  st.stop()  # Menghentikan eksekusi agar halaman utama tidak ikut tampil

# --- HALAMAN UTAMA ---
st.title("📊 Regional Churn Quadrant Analyzer")
st.write(
    "Unggah data rekapitulasi wilayah untuk membagi kuadran secara otomatis"
    " berdasarkan Churn Rate Nasional dan Median Churn Sub."
)

# 1. Input Nama File Output di Main Area
default_filename = (
    f"rekap_pelanggan_update_{datetime.datetime.now().strftime('%Y-%m')}.xlsx"
)
output_filename = st.text_input(
    "Nama File Output (Hasil Export):", value=default_filename
)

# 2. Tombol Upload File di Main Area
uploaded_file = st.file_uploader(
    "Upload file Excel (.xlsx) atau CSV (.csv)", type=["xlsx", "csv"]
)

if uploaded_file is not None:
  try:
    # Membaca file berdasarkan ekstensinya
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)

    # Membersihkan nama kolom (menghilangkan spasi berlebih)
    df.columns = df.columns.str.strip()

    # Validasi kolom wajib
    required_cols = ["Region", "Churn Sub", "EOP"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
      st.error(
          f"Format file tidak sesuai! Kolom berikut tidak ditemukan:"
          f" {missing_cols}. Pastikan ada kolom Region, Churn Sub, dan EOP."
      )
    else:
      # Memisahkan baris Grand Total jika ada, atau menghitungnya secara otomatis
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

      # Tentukan range sumbu agar area warna menutupi seluruh plot
      x_min = df_regions["Churn Rate (%)"].min()
      x_max = df_regions["Churn Rate (%)"].max()
      y_min = 0
      y_max = df_regions["Churn Sub"].max()

      x_buffer = (x_max - x_min) * 0.05 if x_max > x_min else 1.0
      y_buffer = y_max * 0.05

      # Warna latar kuadran dinamis
      color_q1_bg = f"rgba(255, 77, 77, {bg_opacity})"   # Merah transparan
      color_q2_bg = f"rgba(255, 148, 77, {bg_opacity})"  # Oranye transparan
      color_q3_bg = f"rgba(255, 219, 77, {bg_opacity})"  # Kuning transparan
      color_q4_bg = f"rgba(77, 171, 77, {bg_opacity})"   # Hijau transparan

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

      # --- TAMBAHKAN SHAPES LATAR BELAKANG KUADRAN ---
      # Q3 - High Volume (Kiri Atas)
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
      # Q1 - High Impact (Kanan Atas)
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
      # Q4 - Low (Kiri Bawah)
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
      # Q2 - High Rate (Kanan Bawah)
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

      # Tambahkan garis pembagi median (Y) dan nasional (X)
      fig.add_hline(
          y=median_churn_sub,
          line_dash="dash",
          line_color="blue",
          annotation_text=f"Median Churn Sub: {median_churn_sub:,.0f}",
          annotation_position="bottom right",
      )
      fig.add_vline(
          x=national_churn_rate,
          line_dash="dash",
          line_color="blue",
          annotation_text=f"Churn Rate Nasional: {national_churn_rate:.2f}%",
          annotation_position="top left",
      )

      fig.update_traces(
          textposition="top center", marker=dict(size=12, opacity=0.9)
      )
      fig.update_layout(
          height=600,
          template=plotly_template,  # Mengikuti tema Light/Dark
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

      st.download_button(
          label="📥 Download Hasil Rekap (Excel)",
          data=processed_data,
          file_name=output_filename,
          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

  except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses file: {e}")
