# retirement_dlp_monthly_v14.py
# Model Persamaan (1)–(8) + E_ijk (ideal) & e_ijk (data DOSM)

from __future__ import annotations
import streamlit as st, pandas as pd, numpy as np, pulp, re, io

# ═════════════════════  0 · Tetapan Asas  ════════════════════════
st.set_page_config(page_title="DLP Planner – Monthly v14", layout="wide")
st.title("📊 DLP Retirement Planner – Bulanan (E_ideal vs e_sebenar)")

KATEGORI = [
    "Food and Non-Alcoholic Beverages",
    "Alcoholic Beverages, Tobacco, and Narcotics",
    "Clothing and Footwear",
    "Housing, Water, Electricity, Gas and Other Fuels",
    "Furnishings, Household Equipment and Routine Household Maintenance",
    "Health",
    "Transport",
    "Communication",
    "Recreation and Culture",
    "Education",
    "Restaurants and Hotels",
    "Miscellaneous Goods and Services",
]
M = len(KATEGORI)
K2IDX = {c: k for k, c in enumerate(KATEGORI)}

# Padanan bulan → suku
M2Q = {m: (m - 1) // 3 for m in range(1, 13)}
REGEX = re.compile(r"(.+)_M(\d{1,2})$", re.I)
clean = lambda c: re.sub(r"\s+", " ", c).strip().lstrip("\ufeff")

# ═════════════════════  1 · Input Pendapatan  ════════════════════
st.sidebar.header("A · Pendapatan")
N = st.sidebar.number_input("Bilangan individu", 1, 30, 1, 1)
PEOPLE = [f"Individu {i+1}" for i in range(N)]
INCOME = [
    st.sidebar.number_input(f"{p} (RM setahun)", 0.0, 1e8, 60000.0, 1000.0, key=f"inc_{i}")
    for i, p in enumerate(PEOPLE)
]

# ═════════════════════  2 · Corak P_ij  ══════════════════════════
st.sidebar.header("B · Corak nisbah suku  P\u2096")
p_mode = st.sidebar.selectbox(
    "Corak", ["Horizontal 25/25/25/25", "Staircase 30/30/20/20",
              "Zigzag 35/15/30/20", "Manual", "Optimise"]
)
PRE_P = p_mode != "Optimise"
if p_mode.startswith("Horizontal"):
    P_PAT = [0.25] * 4
elif p_mode.startswith("Staircase"):
    P_PAT = [0.30, 0.30, 0.20, 0.20]
elif p_mode.startswith("Zigzag"):
    P_PAT = [0.35, 0.15, 0.30, 0.20]
elif p_mode == "Manual":
    cols = st.sidebar.columns(4)
    P_PAT = [cols[j].number_input(f"Q{j+1}", 0.0, 1.0, 0.25, 0.01) for j in range(4)]
    if abs(sum(P_PAT) - 1) > 1e-6:
        st.sidebar.error("Jumlah Q1–Q4 mesti 1.")
else:
    P_PAT = None  # akan dioptimum

# ═════════════════════  3 · Pecahan Teori C_ijk  ═════════════════
st.sidebar.header("C · Pecahan Teori C\u2096 (Σ=100 %)")
PRESET = {
    "HES 2019":     [17.3,  2.3, 2.1, 23.6, 5.1, 2.2, 13.5, 4.5, 5.0, 1.5, 13.9, 9.0],
    "B40 Muslim":   [22.0,  2.0, 2.0,  8.0, 5.0, 2.0, 22.0, 3.0, 6.0, 1.0, 15.0,12.0],
    "50/30/20":     [18.0,  3.0, 3.0, 25.0, 5.0, 3.0, 10.0, 4.0, 7.0, 2.0, 15.0, 5.0],
}
c_choice = st.sidebar.selectbox("Pilih preset", ["HES 2019", "B40 Muslim", "50/30/20", "Manual"])
if c_choice == "Manual":
    if "C_df" not in st.session_state:
        st.session_state.C_df = pd.DataFrame({"Kategori": KATEGORI, "%": np.full(M, 100 / M)})
    C_df = st.sidebar.data_editor(st.session_state.C_df, num_rows="fixed")
    if abs(C_df["%"].sum() - 100) > 1e-6:
        st.sidebar.error("Jumlah mestilah 100 %.")
    C_vec = C_df["%"].values / 100
else:
    C_vec = np.array(PRESET[c_choice]) / 100

# ═════════════════════  4 · Fail CSV Bulanan  ════════════════════
st.sidebar.header("D · Muat naik CSV bulanan")
csv_file = st.sidebar.file_uploader("Fail .csv (12 × 12 bulan)", type="csv")
RUN = st.sidebar.button("Run 🚀")

# ═════════════════════  5 · Jalankan Model  ══════════════════════
if RUN:
    if csv_file is None:
        st.error("Sila muat naik fail CSV dahulu.")
        st.stop()

    txt = csv_file.read().decode("utf-8", errors="ignore")
    df = (
        pd.read_csv(io.StringIO(txt), sep=None, engine="python", na_values=["null", "NULL", ""])
          .rename(columns=clean)
          .replace({np.nan: 0.0})
    )
    if "Individu" not in df.columns:
        st.error(f"Kolum ditemui: {list(df.columns)[:10]} …\nTiada 'Individu'.")
        st.stop()

    IND, QTR, CAT = range(N), range(4), range(M)
    e_data = np.zeros((N, 4, M))  # perbelanjaan sebenar
    for i in IND:
        row = df[df["Individu"] == PEOPLE[i]]
        if row.empty:
            st.warning(f"{PEOPLE[i]} tiada dalam CSV; diisi 0.")
            continue
        row = row.iloc[0]
        for col in df.columns:
            m = REGEX.match(col)
            if not m: continue
            cat, month = clean(m.group(1)), int(m.group(2))
            if cat not in K2IDX or not 1 <= month <= 12: continue
            k = K2IDX[cat]; q = M2Q[month]
            e_data[i, q, k] += float(row[col])

    # ── Model LP Persamaan (1)–(8) ─────────────────────────────
    mdl = pulp.LpProblem("DLP_monthly_exact", pulp.LpMaximize)
    P = pulp.LpVariable.dicts("P", (IND, QTR), 0, 1)
    A = pulp.LpVariable.dicts("A", (IND, QTR), lowBound=0)
    B = pulp.LpVariable.dicts("B", (IND, QTR))

    for i in IND:
        if PRE_P:
            for j in QTR:
                mdl += P[i][j] == P_PAT[j]
        else:
            mdl += pulp.lpSum(P[i][j] for j in QTR) == 1

        for j in QTR:
            mdl += A[i][j] == P[i][j] * INCOME[i]

    for i in IND:
        for j in QTR:
            Q_amt = A[i][j] if j == 0 else A[i][j] + B[i][j - 1]
            mdl += B[i][j] == Q_amt - pulp.lpSum(e_data[i, j, k] for k in CAT)

    mdl += pulp.lpSum(B[i][3] for i in IND)
    mdl.solve(pulp.PULP_CBC_CMD(msg=False))

    # ── Kira E_ideal & buat DataFrame perbandingan ─────────────
    cmp_rows = []
    for i in IND:
        for j in QTR:
            E_vec = C_vec * A[i][j].value()
            for k, cat in enumerate(KATEGORI):
                cmp_rows.append(
                    {
                        "Individu": PEOPLE[i],
                        "Suku": f"Q{j+1}",
                        "Kategori": cat,
                        "E_ideal": E_vec[k],
                        "e_sebenar": e_data[i, j, k],
                    }
                )
    df_cmp = pd.DataFrame(cmp_rows)

    # ── Jadual ringkasan individu ──────────────────────────────
    rows = []
    for i in IND:
        r = {"Individu": PEOPLE[i], "Pendapatan": INCOME[i]}
        for j in QTR:
            r[f"P_Q{j+1}"] = P[i][j].value()
            r[f"A_Q{j+1}"] = A[i][j].value()
            r[f"Baki_Q{j+1}"] = B[i][j].value()
        r["Baki_Terkumpul_Bi4"] = B[i][3].value()
        rows.append(r)
    df_out = pd.DataFrame(rows)

    # ── Paparan ────────────────────────────────────────────────
    prop_cols = [c for c in df_out.columns if c.startswith("P_Q")]
    money_cols = [c for c in df_out.columns if c not in prop_cols and c != "Individu"]
    fmt_prop, fmt_money = lambda x: f"{x:.2%}", lambda x: f"RM {x:,.2f}"

    st.subheader("Keputusan Utama")
    st.dataframe(df_out.style.format({**{c: fmt_prop for c in prop_cols},
                                      **{c: fmt_money for c in money_cols}}),
                 height=420)

    st.subheader("Baki Terkumpul Hujung Tahun (B_i4)")
    st.bar_chart(df_out.set_index("Individu")["Baki_Terkumpul_Bi4"])

    st.subheader("Perbandingan E_ideal vs e_sebenar (Setiap Kategori & Suku)")
    st.dataframe(df_cmp.style.format({"E_ideal": fmt_money, "e_sebenar": fmt_money}),
                 height=500)

else:
    st.info("Muat naik CSV bulanan, tetapkan parameter, dan tekan **Run**.")
