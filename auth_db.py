"""
auth_db.py - Modul manajemen database user RS Haisa
Menangani: pembuatan tabel, registrasi user, verifikasi login.
Jalankan sekali untuk inisialisasi: python auth_db.py
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime

DB_PATH = "haisa_users.db"


# ─────────────────────────────────────────────
# KONEKSI DATABASE
# ─────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Agar hasil query bisa diakses seperti dict
    return conn


# ─────────────────────────────────────────────
# INISIALISASI TABEL
# ─────────────────────────────────────────────
def init_db():
    """Buat tabel users jika belum ada."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            full_name   TEXT    NOT NULL,
            password_hash TEXT  NOT NULL,
            salt        TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'viewer',  -- 'admin' atau 'viewer'
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL,
            last_login  TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Tabel 'users' siap di '{DB_PATH}'")


# ─────────────────────────────────────────────
# HASH PASSWORD
# ─────────────────────────────────────────────
def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    Hash password dengan salt unik menggunakan SHA-256.
    Returns: (password_hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(32)  # 64 karakter hex
    pw_salted = f"{salt}{password}{salt}"
    pw_hash = hashlib.sha256(pw_salted.encode()).hexdigest()
    return pw_hash, salt


# ─────────────────────────────────────────────
# REGISTRASI USER BARU
# ─────────────────────────────────────────────
def register_user(username: str, full_name: str, password: str, role: str = "viewer") -> dict:
    """
    Daftarkan user baru ke database.
    Role: 'admin' atau 'viewer'
    Returns: {'success': bool, 'message': str}
    """
    if role not in ("admin", "viewer"):
        return {"success": False, "message": "Role tidak valid. Gunakan 'admin' atau 'viewer'."}

    if len(password) < 8:
        return {"success": False, "message": "Password minimal 8 karakter."}

    pw_hash, salt = hash_password(password)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, full_name, password_hash, salt, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (username.lower().strip(), full_name.strip(), pw_hash, salt, role, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"User '{username}' berhasil didaftarkan sebagai {role}."}
    except sqlite3.IntegrityError:
        return {"success": False, "message": f"Username '{username}' sudah digunakan."}
    except Exception as e:
        return {"success": False, "message": f"Error: {e}"}


# ─────────────────────────────────────────────
# VERIFIKASI LOGIN
# ─────────────────────────────────────────────
def verify_login(username: str, password: str) -> dict | None:
    """
    Verifikasi username & password.
    Returns: dict user info (tanpa password_hash & salt) jika valid, None jika gagal.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, password_hash, salt, role, is_active
        FROM users WHERE username = ?
    """, (username.lower().strip(),))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None  # User tidak ditemukan

    if not row["is_active"]:
        conn.close()
        return None  # Akun dinonaktifkan

    # Verifikasi password
    pw_hash, _ = hash_password(password, salt=row["salt"])
    if pw_hash != row["password_hash"]:
        conn.close()
        return None  # Password salah

    # Update last_login
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?",
                   (datetime.now().isoformat(), row["id"]))
    conn.commit()
    conn.close()

    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
    }


# ─────────────────────────────────────────────
# AMBIL SEMUA USER (untuk halaman admin)
# ─────────────────────────────────────────────
def get_all_users() -> list[dict]:
    """Kembalikan semua user tanpa password_hash & salt."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, is_active, created_at, last_login
        FROM users ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# NONAKTIFKAN / AKTIFKAN USER
# ─────────────────────────────────────────────
def set_user_active(user_id: int, is_active: bool) -> dict:
    """Admin bisa nonaktifkan/aktifkan akun user."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?",
                       (1 if is_active else 0, user_id))
        conn.commit()
        conn.close()
        status = "diaktifkan" if is_active else "dinonaktifkan"
        return {"success": True, "message": f"User ID {user_id} berhasil {status}."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─────────────────────────────────────────────
# SEED DATA AWAL (jalankan sekali saja)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()

    # Buat akun default jika belum ada
    print("\n[SEED] Membuat akun default...")
    print(register_user("admin",  "Administrator RS Haisa",  "admin123!",  role="admin"))
    print(register_user("drwati", "Dr. Wati Santoso",        "viewer123!", role="viewer"))
    print(register_user("drandi", "Dr. Andi Prasetyo",       "viewer123!", role="viewer"))

    print("\n[INFO] Akun default berhasil dibuat:")
    print("  Admin   → username: admin    | password: admin123!")
    print("  Viewer  → username: drwati   | password: viewer123!")
    print("  Viewer  → username: drandi   | password: viewer123!")
    print("\n⚠️  Segera ganti password default setelah login pertama!")

