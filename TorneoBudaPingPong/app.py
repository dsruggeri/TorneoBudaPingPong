import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURACIÓN ---
DATA_FILE = "torneo_data.json"
PASSWORD_RESET = "buda"
PLAYERS = ["Lucho", "Mauro", "Gaspar", "Yoyo", "Santi", "Ale", "Emi", "Diego"]

# Mapeo de fotos (Asegurate de que los nombres de archivo coincidan)
PLAYER_PHOTOS = {p: f"assets/{p.lower()}.png" for p in PLAYERS}

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
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return None

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.partidos, f)

# --- INICIALIZACIÓN DE SESIÓN ---
st.set_page_config(page_title="Ping-Pong 8 Jugadores", page_icon="🏓", layout="wide")

if 'partidos' not in st.session_state:
    saved = load_data()
    st.session_state.partidos = saved if saved else init_matches()

# --- SIDEBAR: RESET Y FOTOS ---
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Mostrar fotos hardcodeadas
    st.subheader("👥 Jugadores")
    for p in PLAYERS:
        col_img, col_name = st.columns([1, 3])
        if os.path.exists(PLAYER_PHOTOS[p]):
            col_img.image(PLAYER_PHOTOS[p], width=40)
        else:
            col_img.write("👤")
        col_name.write(p)

    st.divider()
    
    # Sección de Reset
    st.subheader("🚨 Peligro")
    pwd = st.text_input("Contraseña para resetear", type="password")
    if pwd == PASSWORD_RESET:
        if st.button("BORRAR TODO EL TORNEO"):
            st.session_state.partidos = init_matches()
            save_data()
            st.rerun()

# --- LÓGICA DE TABLA ---
def get_tabla():
    stats = {p: {"PJ": 0, "G": 0, "P": 0, "Pts": 0} for p in PLAYERS}
    for m in st.session_state.partidos:
        if m["Jugado"]:
            stats[m["P1"]]["PJ"] += 1; stats[m["P2"]]["PJ"] += 1
            if m["S1"] > m["S2"]:
                stats[m["P1"]]["G"] += 1; stats[m["P1"]]["Pts"] += 2; stats[m["P2"]]["P"] += 1
            else:
                stats[m["P2"]]["G"] += 1; stats[m["P2"]]["Pts"] += 2; stats[m["P1"]]["P"] += 1
    df = pd.DataFrame.from_dict(stats, orient='index').reset_index()
    df.columns = ["Jugador", "PJ", "G", "P", "Pts"]
    return df.sort_values(by=["Pts", "G"], ascending=False)

# --- INTERFAZ PRINCIPAL ---
st.title("🏓 Torneo de Ping-Pong")

tab1, tab2, tab3 = st.tabs(["📝 Resultados", "📊 Tabla", "🏆 Playoffs"])

with tab1:
    ronda_n = st.selectbox("Seleccionar Fecha", [f"Fecha {i+1}" for i in range(7)])
    partidos_fecha = [p for p in st.session_state.partidos if p["Ronda"] == ronda_n]
    
    for idx, m in enumerate(partidos_fecha):
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 0.5, 1, 2, 1])
            
            # Jugador 1
            c1.markdown(f"**{m['P1']}**")
            s1 = c2.number_input("Pts", value=m["S1"], key=f"s1_{ronda_n}_{idx}", label_visibility="collapsed")
            
            c3.write("vs")
            
            # Jugador 2
            s2 = c4.number_input("Pts", value=m["S2"], key=f"s2_{ronda_n}_{idx}", label_visibility="collapsed")
            c5.markdown(f"**{m['P2']}**")
            
            if c6.button("Guardar", key=f"btn_{ronda_n}_{idx}"):
                # Actualizar en el estado global
                for p in st.session_state.partidos:
                    if p["Ronda"] == ronda_n and p["P1"] == m["P1"] and p["P2"] == m["P2"]:
                        p["S1"], p["S2"], p["Jugado"] = s1, s2, True
                save_data()
                st.success("¡Guardado!")
                st.rerun()

with tab2:
    st.header("Posiciones Actuales")
    st.table(get_tabla())

with tab3:
    st.header("Cruces Finales")
    df_t = get_tabla()
    total_jugados = df_t["PJ"].sum()
    
    if total_jugados >= 28: # Todas las fechas completas
        top = df_t.head(4)["Jugador"].tolist()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Semis")
            st.info(f"1º {top[0]} vs 4º {top[3]}")
            st.info(f"2º {top[1]} vs 3º {top[2]}")
        with col2:
            st.subheader("Final")
            st.warning("Ganadores de Semis")
    else:
        st.info(f"Se han jugado {total_jugados//2} de 28 partidos. Los playoffs se liberan al terminar la fase regular.")
