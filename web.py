import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Konfigurasi Halaman & Branding
st.set_page_config(
    page_title="Pusat Analisis Kinerja Rumah Sakit Haisa",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS untuk tampilan lebih manusiawi
st.markdown("""
<style>
    /* Font yang lebih manusiawi */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', times new roman;
    }
    
    /* Background keseluruhan dengan warna biru muda */
    .stApp {
        background-color: #e6f2ff;
    }
    
    /* Membuat Background Header dengan Gradasi Biru Medis yang lebih lembut */
    .header-container {
        background: linear-gradient(135deg, #4a90e2 0%, #7cb9e8 100%);
        padding: 40px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        font-family: 'Inter', sans-serif;
    }
    
    .header-container h1 {
        margin: 0;
        font-size: 35px;
        font-weight: 700;
        color: white !important;
        line-height: 1.2;
    }
    
    .header-container p {
        font-size: 18px;
        opacity: 0.9;
        margin-top: 8px;
    }
    
    /* Styling untuk sidebar */
    .css-1d391kg {
        background-color: #f0f8ff;
        border-right: 1px solid #d0e7ff;
    }
    
    /* Styling untuk card KPI */
    .css-1oe5cao {
        background-color: blue;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        padding: 15px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .css-1oe5cao:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Styling untuk grafik */
    .js-plotly-plot .plotly {
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        background-color: blue;
    }
    
    /* Menghilangkan padding berlebih di atas */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Styling untuk tabel */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Styling untuk info box */
    .stInfo {
        background-color: #e1f5fe;
        border-left: 5px solid #03a9f4;
    }
    .info-box-italic {
    background-color: #e1f5fe;
    border-left: 5px solid #03a9f4;
    padding: 1rem; /* Menambahkan padding agar rapi */
    border-radius: 5px;
    font-style: italic; /* <<< INI YANG MEMBUAT TEKS MIRING */
    color: #01579b; /* Sedikit mengubah warna teks agar kontras lebih baik */
}
    
    /* Styling untuk warning box */
    .stWarning {
        background-color: #fff8e1;
        border-left: 5px solid #ffc107;
    }
    
    /* Styling untuk selectbox dan date input */
    .stSelectbox > div > div {
        background-color: white;
        border-radius: 8px;
    }
    
    .stDateInput > div > div {
        background-color: white;
        border-radius: 8px;
    }
    
    /* Styling untuk footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #4a90e2;
        font-size: 16px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 2. Fungsi Load Data (Diperkuat)
@st.cache_data
def load_data():
    try:
        # Menangani berbagai jenis pemisah CSV (koma atau titik koma)
        df = pd.read_csv("hospital_data.csv", sep=None, engine='python')
        df.columns = df.columns.str.strip() # Hapus spasi di nama kolom
        # Pastikan kolom tanggal dikenali
        df['admission_date'] = pd.to_datetime(df['admission_date'])
        # Tambahkan kolom Bulan untuk analisis tren yang lebih baik
        df['admission_month'] = df['admission_date'].dt.to_period('M').dt.to_timestamp()
        return df, None
    except FileNotFoundError:
        return None, "File 'hospital_data.csv' tidak ditemukan."
    except Exception as e:
        return None, f"Terjadi error saat membaca data: {e}"

# Load Data
df, error_msg = load_data()

if error_msg:
    st.error(error_msg)
    st.stop()

# Setelah load_data
df, error_msg = load_data()

if error_msg:
    st.error(error_msg)
    st.stop()

# Tambahkan pembersihan data
# Hapus baris dengan nilai NaN di kolom penting
df = df.dropna(subset=['primary_diagnosis', 'region', 'gender', 'admission_date'])
# Pastikan kolom readmission_risk_score adalah numerik
df['readmission_risk_score'] = pd.to_numeric(df['readmission_risk_score'], errors='coerce')
df = df.dropna(subset=['readmission_risk_score'])

# 3. Sidebar Filter yang Dinamis
st.sidebar.markdown("###  Pusat Kontrol Filter")
st.sidebar.markdown("Sesuaikan tampilan data berdasarkan kebutuhan analisis Anda.")

# Filter Diagnosis
diag_options = df["primary_diagnosis"].unique().tolist()
selected_diag = st.sidebar.multiselect(
    "Pilih Kategori Diagnosis:",
    options=diag_options,
    default=diag_options, # Default pilih semua
)

# Filter Region
region_options = df["region"].unique().tolist()
selected_region = st.sidebar.multiselect(
    "Pilih Wilayah Pasien:",
    options=region_options,
    default=region_options, # Default pilih semua
)

# Filter Gender (Tambahan untuk variasi)
gender_options = df["gender"].unique().tolist()
selected_gender = st.sidebar.multiselect(
    "Pilih Gender Pasien:",
    options=gender_options,
    default=gender_options,
)

# Filter Range Waktu (Tambahan agar lebih interaktif)
min_date = df["admission_date"].min().date()
max_date = df["admission_date"].max().date()
date_range = st.sidebar.date_input(
    "Pilih Rentang Waktu Kedatangan:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Terapkan Semua Filter
if len(date_range) == 2: # Pastikan range waktu lengkap (start & end)
    start_date, end_date = date_range
    df_selection = df[
        (df["primary_diagnosis"].isin(selected_diag)) &
        (df["region"].isin(selected_region)) &
        (df["gender"].isin(selected_gender)) &
        (df["admission_date"].dt.date >= start_date) &
        (df["admission_date"].dt.date <= end_date)
    ]
else:
    df_selection = df # Tampilkan semua jika range waktu tidak lengkap

st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 Tim Analisis RS Haisa")

# 4. Header Utama & Konteks (Disesuaikan agar CSS Gradasi muncul)
st.markdown(f"""
    <div class="header-container">
        <h1>🏥 Pusat Analisis Kinerja Rumah Sakit Haisa</h1>
        <p>Visualisasi Data Klinis & Operasional | Periode: {start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="info-box-italic">
        <p>Selamat datang di Dashboard Kinerja Rumah Sakit Haisa. Dashboard ini dirancang untuk memberikan wawasan mendalam mengenai efisiensi operasional dan kualitas pelayanan klinis berdasarkan data pasien secara nyata. Gunakan filter di sisi kiri untuk memfokuskan pencarian Anda.</p>
    </div>
""", unsafe_allow_html=True)

# 5. Ringkasan KPI Utama (Metric Cards)
st.markdown("### Key Performance Indicator ")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

if len(df_selection) > 0:
    # KPI 1: Lama Rawat Inap (Efisiensi)
    avg_stay = df_selection["length_of_stay"].mean()
    kpi1.metric(
        label="Rata-rata Lama Inap",
        value=f"{avg_stay:.1f} Hari",
        help="Target efisiensi RS: < 7 hari (contoh)"
    )

    # KPI 2: Skor Risiko Readmission (Kualitas)
    avg_risk = df_selection["readmission_risk_score"].mean()
    kpi2.metric(
        label="Skor Risiko Readmission",
        value=f"{avg_risk:.1f}%",
        help="Semakin rendah skor, semakin baik kualitas pelayanan saat pulang."
    )

    # KPI 3: Jumlah Obat per Pasien (Resource)
    avg_meds = df_selection["medications_count"].mean()
    kpi3.metric(
        label="Rata-rata Jumlah Obat",
        value=f"{avg_meds:.1f} Item",
        help="Rata-rata item obat yang diresepkan per pasien."
    )

    # KPI 4: Total Pasien Teranalisis (Volume)
    kpi4.metric(
        label="Total Pasien Teranalisis",
        value=f"{len(df_selection)} Jiwa"
    )
else:
    st.warning("⚠️ Tidak ada data yang sesuai dengan filter Anda. Silakan sesuaikan filter di sidebar.")
    st.stop()

# 6. Visualisasi Data
st.markdown("### Tren & Distribusi")

# --- Grafik 1: Tren Kedatangan ---
st.markdown("#### Tren Kedatangan Pasien (Per Bulan)")
st.markdown("Menganalisis fluktuasi volume pasien dari waktu ke waktu.")

trend_data = df_selection.groupby('admission_month').size().reset_index(name='Jumlah Pasien')
fig_trend = px.line(
    trend_data, 
    x='admission_month', 
    y='Jumlah Pasien', 
    markers=True,
    template="plotly_white",
    labels={'admission_month': 'Bulan Kedatangan', 'Jumlah Pasien': 'Total Pasien'},
    color_discrete_sequence=['#4a90e2']  # Warna tunggal untuk garis
)
fig_trend.update_xaxes(dtick="M1", tickformat="%b\n%Y")
fig_trend.update_layout(
    font=dict(family="Inter", size=12, color="#333"),
    title_font=dict(family="Inter", size=16, color="#333"),
    hoverlabel=dict(bgcolor="#f0f8ff", font_size=12, font_family="Inter")
)
st.plotly_chart(fig_trend, use_container_width=True)

# --- Grafik 2: Risiko Readmission ---
st.markdown("#### Perbandingan Skor Risiko Berdasarkan Diagnosis")
st.markdown("Identifikasi diagnosis mana yang memiliki risiko readmission tertinggi.")

risk_data = df_selection.groupby("primary_diagnosis")["readmission_risk_score"].mean().reset_index()
risk_data = risk_data.sort_values(by="readmission_risk_score", ascending=False)

fig_risk = px.bar(
    risk_data, 
    x="primary_diagnosis", 
    y="readmission_risk_score", 
    color_discrete_sequence=['#4a90e2'],  # Menggunakan warna tunggal
    template="plotly_white",
    labels={'primary_diagnosis': 'Kategori Diagnosis', 'readmission_risk_score': 'Rerata Skor Risiko (%)'}
)
fig_risk.update_layout(showlegend=False)
fig_risk.update_layout(
    font=dict(family="Inter", size=12, color="#333"),
    title_font=dict(family="Inter", size=16, color="#333"),
    hoverlabel=dict(bgcolor="#f0f8ff", font_size=12, font_family="Inter")
)
st.plotly_chart(fig_risk, use_container_width=True)

# 7. Analisis Mendalam
st.markdown("### Karakteristik Pasien")

# --- Bagian Distribusi Usia ---
st.markdown("#### Distribusi Usia & Gender Pasien")
st.markdown("Memahami profil umur dan jenis kelamin pasien yang dilayani.")
# Pastikan data gender tidak memiliki nilai NaN
df_clean = df_selection.dropna(subset=['gender'])

fig_age = px.histogram(
    df_clean, 
    x="age", 
    color="gender", 
    nbins=20,
    marginal="box",
    template="plotly_white",
    labels={'age': 'Usia Pasien (Tahun)', 'gender': 'Gender'},
    opacity=0.8,
    color_discrete_map={'Male': '#4a90e2', 'Female': '#ff6b9d'}  # Pemetaan warna eksplisit
)
fig_age.update_layout(
    font=dict(family="Inter", size=12, color="#333"),
    title_font=dict(family="Inter", size=16, color="#333"),
    hoverlabel=dict(bgcolor="#f0f8ff", font_size=12, font_family="Inter")
)
st.plotly_chart(fig_age, use_container_width=True)

# --- Bagian Tabel Data ---
st.markdown("#### Sampel Data Pasien (10 Baris Pertama)")
st.markdown("Menampilkan data mentah untuk validasi cepat.")
st.dataframe(df_selection.head(10), use_container_width=True)

# 8. Analisis & Interpretasi Tim (Teks Narasi)
st.divider()
st.markdown("### 📝 Analisis & Interpretasi Tim")
with st.expander("Klik untuk melihat detail analisis dari tim kami", expanded=True):
    st.markdown(
        """
        Berdasarkan dashboard di atas, tim kami merumuskan beberapa poin analisis kunci untuk manajemen RS:

        1.  **Profil Pasien:** Mayoritas pasien berada di kelompok usia produktif dan lansia (cek histogram). Hal ini menjadi dasar untuk menyesuaikan fasilitas rawat inap agar lebih ramah lansia.
        2.  **Kualitas Klinis:**Rata-rata risiko readmission populasi cukup tinggi, yakni 74.8%. Diagnosis dengan risiko di atas rata-rata (seperti Heart Failure) harus menjadi fokus utama dalam pengetatan protokol pemulangan pasien.
        3.  **Tren Volume:** Fluktuasi kedatangan pasien terpantau sangat dinamis dalam skala besar. Data ini sangat valid untuk digunakan sebagai acuan manajemen dalam pembagian shift staf medis agar beban kerja tetap seimbang.
        4.  **Efisiensi Operasional:** Rata-rata lama inap pasien adalah 7.8 Hari. Angka ini menunjukkan durasi perawatan yang lebih intensif, sehingga manajemen perlu mengoptimalkan ketersediaan tempat tidur.

        **Rekomendasi:** Manajer operasional disarankan memantau dashboard ini secara berkala untuk melakukan intervensi dini pada departemen dengan angka risiko readmission yang meningkat.
   """ )
# Footer
st.markdown("""
<div class="footer">
    <p>© 2024 Rumah Sakit Haisa </p>
</div>
""", unsafe_allow_html=True)
