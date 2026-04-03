"""
backend.py - FastAPI Backend RS Haisa (dengan JWT Auth & Role-Based Access)
Jalankan: uvicorn backend:app --reload --port 8000
Install:  pip install fastapi uvicorn python-jose[cryptography] pandas numpy
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, date, timedelta
from typing import Optional, List
import pandas as pd
import numpy as np
import sys, os

sys.path.append(os.path.dirname(__file__))
from auth_db import init_db, verify_login, get_all_users, register_user, set_user_active

# ─────────────────────────────────────────────
# KONFIGURASI JWT
# ─────────────────────────────────────────────
# ⚠️ WAJIB diganti dengan string acak panjang di production!
SECRET_KEY = "GANTI_DENGAN_STRING_ACAK_PANJANG_DAN_RAHASIA_RS_HAISA_2024"
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 jam = 1 shift kerja

app = FastAPI(
    title="RS Haisa Analytics API",
    description="API backend dengan JWT Auth & Role-Based Access Control.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Inisialisasi DB saat startup
init_db()


# ─────────────────────────────────────────────
# JWT UTILITIES
# ─────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kedaluwarsa.")
    user = {
        "id":        payload.get("sub"),
        "username":  payload.get("username"),
        "full_name": payload.get("full_name"),
        "role":      payload.get("role"),
    }
    if not user["username"]:
        raise HTTPException(status_code=401, detail="Token tidak memiliki informasi user.")
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Hanya admin yang diizinkan.")
    return current_user


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
def load_clean_data() -> pd.DataFrame:
    df = pd.read_csv("hospital_data.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df['admission_date'] = pd.to_datetime(df['admission_date'])
    df['admission_month'] = df['admission_date'].dt.to_period('M').dt.to_timestamp()
    df['readmission_risk_score'] = pd.to_numeric(df['readmission_risk_score'], errors='coerce')
    df = df.dropna(subset=['primary_diagnosis', 'region', 'gender', 'admission_date', 'readmission_risk_score'])
    return df

try:
    _df = load_clean_data()
except Exception as e:
    _df = None
    print(f"[ERROR] Gagal load data: {e}")


def get_filtered(diagnoses, regions, genders, start_date, end_date) -> pd.DataFrame:
    if _df is None:
        raise HTTPException(status_code=500, detail="Data tidak tersedia di server.")
    df = _df.copy()
    if diagnoses:  df = df[df["primary_diagnosis"].isin(diagnoses)]
    if regions:    df = df[df["region"].isin(regions)]
    if genders:    df = df[df["gender"].isin(genders)]
    if start_date: df = df[df["admission_date"].dt.date >= start_date]
    if end_date:   df = df[df["admission_date"].dt.date <= end_date]
    return df


# ─────────────────────────────────────────────
# ENDPOINT: AUTH
# ─────────────────────────────────────────────
@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login — kembalikan JWT token jika username & password valid."""
    user = verify_login(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    token = create_access_token({
        "sub":       str(user["id"]),
        "username":  user["username"],
        "full_name": user["full_name"],
        "role":      user["role"],
    })
    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "username":  user["username"],
            "full_name": user["full_name"],
            "role":      user["role"],
        }
    }


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ─────────────────────────────────────────────
# ENDPOINT: ADMIN — Manajemen User
# ─────────────────────────────────────────────
@app.get("/admin/users")
def list_users(current_user: dict = Depends(require_admin)):
    """[ADMIN ONLY] Lihat semua user terdaftar."""
    return {"users": get_all_users()}


@app.post("/admin/users/register")
def admin_register_user(
    username:  str,
    full_name: str,
    password:  str,
    role:      str = "viewer",
    current_user: dict = Depends(require_admin),
):
    """[ADMIN ONLY] Daftarkan user baru."""
    result = register_user(username, full_name, password, role)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/admin/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id:   int,
    is_active: bool,
    current_user: dict = Depends(require_admin),
):
    """[ADMIN ONLY] Aktifkan atau nonaktifkan akun user."""
    result = set_user_active(user_id, is_active)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ─────────────────────────────────────────────
# ENDPOINT: DATA (semua role, wajib login)
# ─────────────────────────────────────────────
@app.get("/filters/options")
def get_filter_options(current_user: dict = Depends(get_current_user)):
    if _df is None:
        raise HTTPException(status_code=500, detail="Data tidak tersedia.")
    return {
        "diagnoses": sorted(_df["primary_diagnosis"].unique().tolist()),
        "regions":   sorted(_df["region"].unique().tolist()),
        "genders":   sorted(_df["gender"].unique().tolist()),
        "date_min":  str(_df["admission_date"].min().date()),
        "date_max":  str(_df["admission_date"].max().date()),
    }


@app.get("/kpi/summary")
def get_kpi_summary(
    diagnoses:  Optional[List[str]] = Query(default=None),
    regions:    Optional[List[str]] = Query(default=None),
    genders:    Optional[List[str]] = Query(default=None),
    start_date: Optional[date]      = Query(default=None),
    end_date:   Optional[date]      = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    df = get_filtered(diagnoses, regions, genders, start_date, end_date)
    if df.empty:
        return {"total_patients": 0, "avg_length_of_stay": None,
                "avg_readmission_risk": None, "avg_medications_count": None}
    return {
        "total_patients":        int(len(df)),
        "avg_length_of_stay":    round(float(df["length_of_stay"].mean()), 1),
        "avg_readmission_risk":  round(float(df["readmission_risk_score"].mean()), 1),
        "avg_medications_count": round(float(df["medications_count"].mean()), 1),
    }


@app.get("/analytics/trend/monthly")
def get_monthly_trend(
    diagnoses:  Optional[List[str]] = Query(default=None),
    regions:    Optional[List[str]] = Query(default=None),
    genders:    Optional[List[str]] = Query(default=None),
    start_date: Optional[date]      = Query(default=None),
    end_date:   Optional[date]      = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    df = get_filtered(diagnoses, regions, genders, start_date, end_date)
    if df.empty:
        return {"data": []}
    trend = df.groupby("admission_month").size().reset_index(name="jumlah_pasien")
    trend["admission_month"] = trend["admission_month"].dt.strftime("%Y-%m-%d")
    return {"data": trend.to_dict(orient="records")}


@app.get("/analytics/readmission-risk/by-diagnosis")
def get_risk_by_diagnosis(
    diagnoses:  Optional[List[str]] = Query(default=None),
    regions:    Optional[List[str]] = Query(default=None),
    genders:    Optional[List[str]] = Query(default=None),
    start_date: Optional[date]      = Query(default=None),
    end_date:   Optional[date]      = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    df = get_filtered(diagnoses, regions, genders, start_date, end_date)
    if df.empty:
        return {"data": []}
    risk = (df.groupby("primary_diagnosis")["readmission_risk_score"]
              .mean().round(1).reset_index()
              .sort_values("readmission_risk_score", ascending=False))
    risk.columns = ["diagnosis", "avg_risk_score"]
    return {"data": risk.to_dict(orient="records")}


@app.get("/analytics/age-distribution")
def get_age_distribution(
    diagnoses:  Optional[List[str]] = Query(default=None),
    regions:    Optional[List[str]] = Query(default=None),
    genders:    Optional[List[str]] = Query(default=None),
    start_date: Optional[date]      = Query(default=None),
    end_date:   Optional[date]      = Query(default=None),
    bins: int   = Query(default=20, ge=5, le=50),
    current_user: dict = Depends(get_current_user),
):
    df = get_filtered(diagnoses, regions, genders, start_date, end_date)
    if df.empty:
        return {"data": []}
    result = []
    for gender, group in df.groupby("gender"):
        counts, bin_edges = np.histogram(group["age"].dropna(), bins=bins)
        for i, count in enumerate(counts):
            result.append({
                "gender":    gender,
                "age_start": round(float(bin_edges[i]), 1),
                "age_end":   round(float(bin_edges[i + 1]), 1),
                "count":     int(count),
            })
    return {"data": result}
