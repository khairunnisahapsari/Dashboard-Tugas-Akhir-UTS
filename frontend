"""
frontend.py - Streamlit Frontend RS Haisa (dengan Login & Role-Based UI)
Jalankan: streamlit run frontend.py
Pastikan backend.py sudah berjalan di port 8000.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date

API_BASE = "http://localhost:8000"

# ─────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RS Haisa — Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #e6f2ff; }

    /* ── Login Card ── */
    .login-wrapper {
        display: flex; justify-content: center; align-items: center;
        min-height: 70vh;
    }
    .login-card {
        background: white; border-radius: 20px;
        padding: 48px 40px; max-width: 420px; width: 100%;
        box-shadow: 0 8px 32px rgba(74,144,226,0.15);
        text-align: center;
    }
    .login-card h2 { color: #4a90e2; font-size: 26px; margin-bottom: 4px; }
    .login-card p  { color: #888; font-size: 14px; margin-bottom: 28px; }

    /* ── Header Dashboard ── */
    .header-container {
        background: linear-gradient(135deg, #4a90e2 0%, #7cb9e8 100%);
        padding: 36px 40px; border-radius: 15px; color: white;
        margin-bottom: 24px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-container h1 { margin: 0; font-size: 30px; font-weight: 700; color: white !important; }
    .header-container p  { font-size: 16px; opacity: 0.88; margin-top: 6px; }

    /* ── Info box ── */
    .info-box-italic {
        background-color: #e1f5fe; border-left: 5px solid #03a9f4;
        padding: 1rem; border-radius: 5px; font-style: italic; color: #01579b;
        margin-bottom: 16px;
    }

    /* ── Role badge ── */
    .badge-admin  { background:#4a90e2; color:white; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-viewer { background:#e0e0e0; color:#555;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }

    /* ── Admin panel card ── */
    .admin-panel {
        background: #fff8e1; border-left: 5px solid #ffc107;
        padding: 1rem; border-radius: 8px; margin-bottom: 16px;
    }

    .footer { text-align:center; padding:20px; color:#4a90e2; font-size:14px; margin-top:20px; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE — Inisialisasi
# ─────────────────────────────────────────────
if "token"     not in st.session_state: st.session_state.token     = None
if "user_info" not in st.session_state: st.session_state.user_info = None
if "logged_in" not in st.session_state: st.session_state.logged_in = False


# ─────────────────────────────────────────────
# HELPER: API call dengan token
# ─────────────────────────────────────────────
def api_get(endpoint: str, params=None) -> tuple:
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", params=params, headers=headers, timeout=10)
        if resp.status_code == 401:
            # Token kedaluwarsa — paksa logout
            do_logout()
            st.rerun()
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "❌ Backend tidak bisa dihubungi. Pastikan `backend.py` berjalan di port 8000."
    except Exception as e:
        return None, str(e)


def api_post(endpoint: str, data: dict = None, params: dict = None) -> tuple:
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", data=data, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def build_params(selected_diag, selected_region, selected_gender, start_date, end_date):
    params = []
    for d in selected_diag:   params.append(("diagnoses", d))
    for r in selected_region: params.append(("regions", r))
    for g in selected_gender: params.append(("genders", g))
    params.append(("start_date", str(start_date)))
    params.append(("end_date",   str(end_date)))
    return params


def do_logout():
    st.session_state.token     = None
    st.session_state.user_info = None
    st.session_state.logged_in = False


# ─────────────────────────────────────────────
# HALAMAN LOGIN
# ─────────────────────────────────────────────
def show_login_page():
    # Sembunyikan sidebar saat login
    st.markdown("<style>[data-testid='stSidebar']{display:none}</style>", unsafe_allow_html=True)

    # Logo & judul di atas form
    st.markdown("""
        <div style="text-align:center; margin-top: 60px; margin-bottom: 24px;">
            <div style="font-size:64px;">🏥</div>
            <h1 style="color:#4a90e2; font-size:28px; font-weight:700; margin:8px 0 4px;">
                Rumah Sakit Haisa
            </h1>
            <p style="color:#888; font-size:15px;">Pusat Analisis Kinerja Klinis & Operasional</p>
        </div>
    """, unsafe_allow_html=True)

    # Form login di tengah halaman
    col_l, col_mid, col_r = st.columns([1, 1.2, 1])
    with col_mid:
        with st.container(border=True):
            st.markdown("#### 🔐 Masuk ke Dashboard")
            username = st.text_input("Username", placeholder="Contoh: admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            login_btn = st.button("Masuk", use_container_width=True, type="primary")

            if login_btn:
                if not username or not password:
                    st.warning("Harap isi username dan password.")
                else:
                    with st.spinner("Memverifikasi..."):
                        result, err = api_post(
                            "/auth/login",
                            data={"username": username, "password": password}
                        )
                    if err:
                        st.error(f"Login gagal: {err}")
                    else:
                        st.session_state.token     = result["access_token"]
                        st.session_state.user_info = result["user"]
                        st.session_state.logged_in = True
                        st.success(f"Selamat datang, {result['user']['full_name']}!")
                        st.rerun()

        st.markdown("""
            <p style="text-align:center; color:#aaa; font-size:12px; margin-top:12px;">
                Hubungi administrator jika tidak memiliki akses.
            </p>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PANEL ADMIN: Manajemen User
# ─────────────────────────────────────────────
def show_admin_panel():
    st.markdown("---")
    st.markdown("### 🛡️ Panel Admin — Manajemen User")
    st.markdown('<div class="admin-panel">Panel ini hanya terlihat oleh akun dengan role <strong>Admin</strong>.</div>', unsafe_allow_html=True)

    # Tabel user aktif
    users_data, err = api_get("/admin/users")
    if err:
        st.error(err)
        return

    users_df = pd.DataFrame(users_data["users"])
    users_df["Status"] = users_df["is_active"].apply(lambda x: "✅ Aktif" if x else "🚫 Nonaktif")
    users_df["Role"]   = users_df["role"].apply(
        lambda r: "👑 Admin" if r == "admin" else "👁️ Viewer"
    )

    st.dataframe(
        users_df[["id", "username", "full_name", "Role", "Status", "created_at", "last_login"]].rename(columns={
            "id": "ID", "username": "Username", "full_name": "Nama Lengkap",
            "created_at": "Dibuat", "last_login": "Login Terakhir"
        }),
        use_container_width=True
    )

    # Form: Daftarkan user baru
    with st.expander("➕ Daftarkan User Baru"):
        c1, c2 = st.columns(2)
        new_username  = c1.text_input("Username Baru")
        new_fullname  = c2.text_input("Nama Lengkap")
        new_password  = c1.text_input("Password (min. 8 karakter)", type="password")
        new_role      = c2.selectbox("Role", ["viewer", "admin"])
        if st.button("Daftarkan User", type="primary"):
            if not all([new_username, new_fullname, new_password]):
                st.warning("Semua field wajib diisi.")
            else:
                res, err = api_post(
                    "/admin/users/register",
                    params={"username": new_username, "full_name": new_fullname,
                            "password": new_password, "role": new_role}
                )
                if err: st.error(err)
                else:   st.success(res["message"]); st.rerun()

    # Form: Toggle aktif/nonaktif
    with st.expander("🔧 Aktifkan / Nonaktifkan User"):
        user_id_input = st.number_input("ID User", min_value=1, step=1)
        toggle_val    = st.radio("Ubah status menjadi:", ["Aktif", "Nonaktif"], horizontal=True)
        if st.button("Terapkan Perubahan"):
            res, err = api_post(
                f"/admin/users/{int(user_id_input)}/toggle-active",
                params={"is_active": toggle_val == "Aktif"}
            )
            if err: st.error(err)
            else:   st.success(res["message"]); st.rerun()


# ─────────────────────────────────────────────
# HALAMAN DASHBOARD UTAMA
# ─────────────────────────────────────────────
def show_dashboard():
    user      = st.session_state.user_info
    role      = user["role"]
    role_html = f'<span class="badge-admin">👑 Admin</span>' if role == "admin" \
                else f'<span class="badge-viewer">👁️ Viewer</span>'

    # ── Sidebar ──────────────────────────────
    with st.sidebar:
        st.markdown(f"**{user['full_name']}** {role_html}", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### ⚙️ Pusat Kontrol Filter")

        # Load opsi filter dari API
        @st.cache_data(ttl=300)
        def fetch_opts():
            return api_get("/filters/options")

        filter_opts, filter_err = fetch_opts()
        if filter_err:
            st.error(filter_err)
            st.stop()

        diag_options   = filter_opts["diagnoses"]
        region_options = filter_opts["regions"]
        gender_options = filter_opts["genders"]
        min_date = date.fromisoformat(filter_opts["date_min"])
        max_date = date.fromisoformat(filter_opts["date_max"])

        selected_diag   = st.multiselect("Diagnosis:",  diag_options,   default=diag_options)
        selected_region = st.multiselect("Wilayah:",    region_options, default=region_options)
        selected_gender = st.multiselect("Gender:",     gender_options, default=gender_options)
        date_range = st.date_input("Rentang Waktu:", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            do_logout()
            st.rerun()

        st.markdown("© 2024 Tim Analisis RS Haisa")

    start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)
    q_params = build_params(selected_diag, selected_region, selected_gender, start_date, end_date)

    # ── Header ───────────────────────────────
    st.markdown(f"""
        <div class="header-container">
            <h1>🏥 Pusat Analisis Kinerja Rumah Sakit Haisa</h1>
            <p>Visualisasi Data Klinis & Operasional | {start_date.strftime('%B %Y')} – {end_date.strftime('%B %Y')}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="info-box-italic">
            <p>Selamat datang di Dashboard Kinerja RS Haisa. Data ditampilkan dalam bentuk agregat —
            data individu pasien tidak diekspos di antarmuka ini. Gunakan filter di sisi kiri untuk
            memfokuskan analisis Anda.</p>
        </div>
    """, unsafe_allow_html=True)

    # ── KPI ──────────────────────────────────
    st.markdown("### 📊 Key Performance Indicator")
    kpi_data, kpi_err = api_get("/kpi/summary", params=q_params)

    if kpi_err:
        st.error(kpi_err); st.stop()
    if kpi_data["total_patients"] == 0:
        st.warning("⚠️ Tidak ada data sesuai filter. Sesuaikan filter di sidebar."); st.stop()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Rata-rata Lama Inap",      f"{kpi_data['avg_length_of_stay']} Hari")
    k2.metric("Skor Risiko Readmission",  f"{kpi_data['avg_readmission_risk']}%")
    k3.metric("Rata-rata Jumlah Obat",    f"{kpi_data['avg_medications_count']} Item")
    k4.metric("Total Pasien Teranalisis", f"{kpi_data['total_patients']} Jiwa")

    # ── Grafik 1: Tren Bulanan ───────────────
    st.markdown("### 📈 Tren & Distribusi")
    st.markdown("#### Tren Kedatangan Pasien (Per Bulan)")
    trend_raw, trend_err = api_get("/analytics/trend/monthly", params=q_params)
    if trend_err: st.error(trend_err)
    elif not trend_raw["data"]: st.info("Tidak ada data tren.")
    else:
        trend_df = pd.DataFrame(trend_raw["data"])
        trend_df["admission_month"] = pd.to_datetime(trend_df["admission_month"])
        fig = px.line(trend_df, x="admission_month", y="jumlah_pasien", markers=True,
                      template="plotly_white", color_discrete_sequence=["#4a90e2"],
                      labels={"admission_month": "Bulan", "jumlah_pasien": "Total Pasien"})
        fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
        fig.update_layout(font=dict(family="Inter", size=12))
        st.plotly_chart(fig, use_container_width=True)

    # ── Grafik 2: Risiko per Diagnosis ───────
    st.markdown("#### Perbandingan Skor Risiko Berdasarkan Diagnosis")
    risk_raw, risk_err = api_get("/analytics/readmission-risk/by-diagnosis", params=q_params)
    if risk_err: st.error(risk_err)
    elif not risk_raw["data"]: st.info("Tidak ada data risiko.")
    else:
        risk_df = pd.DataFrame(risk_raw["data"])
        fig2 = px.bar(risk_df, x="diagnosis", y="avg_risk_score",
                      template="plotly_white", color_discrete_sequence=["#4a90e2"],
                      labels={"diagnosis": "Kategori Diagnosis", "avg_risk_score": "Rerata Skor Risiko (%)"})
        fig2.update_layout(showlegend=False, font=dict(family="Inter", size=12))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Grafik 3: Distribusi Usia ─────────────
    st.markdown("### 👥 Karakteristik Pasien")
    st.markdown("#### Distribusi Usia & Gender")
    age_raw, age_err = api_get("/analytics/age-distribution", params=q_params)
    if age_err: st.error(age_err)
    elif not age_raw["data"]: st.info("Tidak ada data distribusi usia.")
    else:
        age_df = pd.DataFrame(age_raw["data"])
        age_df["age_midpoint"] = ((age_df["age_start"] + age_df["age_end"]) / 2).round(1)
        fig3 = px.bar(age_df, x="age_midpoint", y="count", color="gender",
                      barmode="overlay", opacity=0.8, template="plotly_white",
                      labels={"age_midpoint": "Usia (Tahun)", "count": "Jumlah Pasien", "gender": "Gender"},
                      color_discrete_map={"Male": "#4a90e2", "Female": "#ff6b9d"})
        fig3.update_layout(font=dict(family="Inter", size=12))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Panel Admin (hanya admin) ─────────────
    if role == "admin":
        show_admin_panel()

    # ── Analisis Tim ─────────────────────────
    st.divider()
    st.markdown("### 📝 Analisis & Interpretasi Tim")
    with st.expander("Klik untuk melihat detail analisis dari tim kami", expanded=True):
        st.markdown(f"""
        1. **Profil Pasien:** Distribusi usia mencerminkan kebutuhan penyesuaian fasilitas, terutama untuk kelompok lansia.
        2. **Kualitas Klinis:** Rata-rata risiko readmission **{kpi_data['avg_readmission_risk']}%**.
           Diagnosis berisiko tinggi perlu pengetatan protokol pemulangan.
        3. **Tren Volume:** Fluktuasi kedatangan sangat dinamis — acuan valid untuk manajemen shift staf medis.
        4. **Efisiensi Operasional:** Rata-rata lama inap **{kpi_data['avg_length_of_stay']} hari**.
           Optimasi ketersediaan tempat tidur perlu diperhatikan.

        **Rekomendasi:** Pantau dashboard secara berkala untuk intervensi dini pada departemen berisiko tinggi.
        """)

    st.markdown('<div class="footer">© 2024 Rumah Sakit Haisa</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ROUTER UTAMA
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login_page()
else:
    show_dashboard()
