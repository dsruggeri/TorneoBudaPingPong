import streamlit as st
import pandas as pd
import json
import os
from streamlit_gsheets import GSheetsConnection 

# --- CONFIGURACIÓN ---

PASSWORD_RESET = "buda"
PLAYERS = ["Lucho", "Mauro", "Gaspar", "Yoyo", "Santi", "Ale", "Emi", "Diego"]
# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)


# Mapeo de fotos
# --- CONFIGURACIÓN DE RUTAS ---
# Obtenemos la ruta absoluta de la carpeta donde está este archivo app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construimos las rutas uniendo BASE_DIR + la carpeta assets
PLAYER_PHOTOS = {p: os.path.join(BASE_DIR, "assets", f"{p.lower()}.png") for p in PLAYERS}
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

def init_matches():
    fixture_raw = [
        ["Fecha 1", "Lucho vs Mauro", "Gaspar vs Yoyo", "Santi vs Ale", "Emi vs Diego"],
        ["Fecha 2", "Lucho vs Gaspar", "Mauro vs Yoyo", "Santi vs Emi", "Ale vs Diego"],
        ["Fecha 3", "Lucho vs Yoyo", "Mauro vs Gaspar", "Santi vs Diego", "Ale vs Emi"],
        ["Fecha 4", "Lucho vs Santi", "Mauro vs Ale", "Gaspar vs Emi", "Yoyo vs Diego"],
        ["Fecha 5", "Lucho vs Ale", "Mauro vs Santi", "Gaspar vs Diego", "Yoyo vs Emi"],
        ["Fecha 6", "Lucho vs Emi", "Mauro vs Diego", "Gaspar vs Santi", "Yoyo vs Ale"],
        ["Fecha 7", "Lucho vs Diego", "Mauro vs Emi", "Gaspar vs Ale", "Yoyo vs Santi"]
    ]
    partidos = []
    for f in fixture_raw:
        for enc in f[1:]:
            p1, p2 = enc.split(" vs ")
            partidos.append({"Ronda": f[0], "P1": p1, "P2": p2, "S1": 0, "S2": 0, "Jugado": False})
    return partidos

def load_data():
    try:
        # Leemos la hoja "Partidos" de tu Google Sheet
        df = conn.read(worksheet="Partidos", ttl=0)
        if df.empty:
            return None
        # Convertimos el DataFrame a lista de diccionarios para que tu código siga funcionando igual
        return df.to_dict(orient="records")
    except Exception:
        return None

def save_data():
    # Convertimos los datos actuales a DataFrame y los subimos
    df_to_save = pd.DataFrame(st.session_state.partidos)
    conn.update(worksheet="Partidos", data=df_to_save)
    st.toast("✅ Datos sincronizados en la nube")

# --- INICIALIZACIÓN ---
# Cambiamos el icono de la página y el título de la pestaña del navegador
st.set_page_config(page_title="Torneo Budaístico PP", page_icon="🧘", layout="wide")

if 'partidos' not in st.session_state:
    saved = load_data()
    st.session_state.partidos = saved if saved else init_matches()

# --- SIDEBAR ---
with st.sidebar:
    st.header("👥 Jugadores")
    for p in PLAYERS:
        col_img, col_name = st.columns([1, 3])
        if os.path.exists(PLAYER_PHOTOS[p]):
            col_img.image(PLAYER_PHOTOS[p], width=40)
        else:
            col_img.write("👤")
        col_name.write(p)

    st.divider()
    st.subheader("🚨 Resetear Torneo")
    pwd = st.text_input("Contraseña", type="password")
    if pwd == PASSWORD_RESET:
        if st.button("BORRAR DATOS", type="primary"):
            st.session_state.partidos = init_matches()
            save_data()
            st.rerun()

# --- LÓGICA DE TABLA ---
def get_tabla():
    stats = {p: {"PJ": 0, "G": 0, "P": 0, "PF": 0, "PC": 0, "Dif": 0, "Pts": 0} for p in PLAYERS}
    for m in st.session_state.partidos:
        if m["Jugado"]:
            p1, p2 = m["P1"], m["P2"]
            s1, s2 = m["S1"], m["S2"]
            
            stats[p1]["PJ"] += 1; stats[p2]["PJ"] += 1
            stats[p1]["PF"] += s1; stats[p1]["PC"] += s2
            stats[p2]["PF"] += s2; stats[p2]["PC"] += s1
            stats[p1]["Dif"] = stats[p1]["PF"] - stats[p1]["PC"]
            stats[p2]["Dif"] = stats[p2]["PF"] - stats[p2]["PC"]
            
            if s1 > s2:
                stats[p1]["G"] += 1; stats[p1]["Pts"] += 2; stats[p2]["P"] += 1
            elif s2 > s1:
                stats[p2]["G"] += 1; stats[p2]["Pts"] += 2; stats[p1]["P"] += 1
                
    df = pd.DataFrame.from_dict(stats, orient='index').reset_index()
    df.columns = ["Jugador", "PJ", "G", "P", "PF", "PC", "Dif", "Pts"]
    cols_enteros = ["PJ", "G", "P", "PF", "PC", "Dif", "Pts"]
    df[cols_enteros] = df[cols_enteros].astype(int)
    return df.sort_values(by=["Pts", "Dif"], ascending=False)

# --- HEADER PERSONALIZADO ---
# Usamos columnas para poner el logo al lado del título
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=120) # Ajusta el width si el logo es muy grande o chico
    else:
        st.write("🧘") # Placeholder si no encuentra la imagen
with col_title:
    # Usamos markdown con CSS inline para centrar verticalmente el título si hace falta
    st.markdown("""
        <h1 style='text-align: left; margin-top: 20px;'>
            Torneo Budaístico de Ping-Pong
        </h1>
        """, unsafe_allow_html=True)

# --- TABS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs(["📝 Cargar Resultados", "📊 Tabla de Posiciones", "🏆 Playoffs"])

with tab1:
    ronda_sel = st.selectbox("Elegir Fecha", [f"Fecha {i+1}" for i in range(7)])
    partidos_f = [p for p in st.session_state.partidos if p["Ronda"] == ronda_sel]
    
    for idx, m in enumerate(partidos_f):
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 0.5, 1, 2, 1])
            
            c1.markdown(f"**{m['P1']}**")
            
            if m["Jugado"]:
                c2.write(f"## {int(m['S1'])}")  # Agregamos int()
                c3.write("vs")
                c4.write(f"## {int(m['S2'])}")  # Agregamos int()
                c5.markdown(f"**{m['P2']}**")
                if c6.button("Editar", key=f"edit_{ronda_sel}_{idx}"):
                    for p_orig in st.session_state.partidos:
                        if p_orig["Ronda"] == ronda_sel and p_orig["P1"] == m["P1"]:
                            p_orig["Jugado"] = False
                    st.rerun()
            else:
                # Forzamos value=int(...) y step=1 para que Streamlit sepa que es un entero
                s1 = c2.number_input("Pts", value=int(m["S1"]), step=1, key=f"in1_{ronda_sel}_{idx}", label_visibility="collapsed")
                c3.write("vs")
                s2 = c4.number_input("Pts", value=int(m["S2"]), step=1, key=f"in2_{ronda_sel}_{idx}", label_visibility="collapsed")
                c5.markdown(f"**{m['P2']}**")
                if c6.button("Guardar", key=f"save_{ronda_sel}_{idx}", type="primary"):
                    for p_orig in st.session_state.partidos:
                        if p_orig["Ronda"] == ronda_sel and p_orig["P1"] == m["P1"]:
                            p_orig["S1"], p_orig["S2"], p_orig["Jugado"] = s1, s2, True
                    save_data()
                    st.rerun()

with tab2:
    st.header("Clasificación General")
    df_pos = get_tabla()
    st.dataframe(df_pos, hide_index=True, use_container_width=True)

with tab3:
    st.header("Cuadro Final")
    df_t = get_tabla()
    if df_t["PJ"].sum() >= 28:
        top = df_t.head(4)["Jugador"].tolist()
        st.success("¡Fase regular completada!")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
             st.subheader("Semifinal 1")
             st.info(f"1º {top[0]} vs 4º {top[3]}")
        with col_s2:
             st.subheader("Semifinal 2")
             st.info(f"2º {top[1]} vs 3º {top[2]}")
    else:
        partidos_restantes = 28 - (df_t["PJ"].sum() // 2)
        st.warning(f"Faltan jugar {partidos_restantes} partidos para definir los Playoffs.")






