import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

st.title("Configuración Inicial de la Red de Protección")

import streamlit as st

st.header("Paso 1: Entrada de Líneas y Nodos")

# --- Crear 4 columnas ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    cantidad_nodos = st.number_input("Cantidad de Nodos", min_value=1, step=1)

with col2:
    cantidad_lineas = st.number_input("Cantidad de Líneas", min_value=1, step=1)

with col3:
    rtc = st.text_input("RTC", value="1.0")
    try:
        st.session_state["rtc"] = float(rtc)
    except ValueError:
        st.warning("⚠️ Ingrese un valor numérico para RTC.")

with col4:
    rtp = st.text_input("RTP", value="1.0")
    try:
        st.session_state["rtp"] = float(rtp)
    except ValueError:
        st.warning("⚠️ Ingrese un valor numérico para RTP.")

# --- Validación de líneas ---
if cantidad_lineas < (cantidad_nodos - 1):
    st.warning("⚠️ La cantidad de líneas no es suficiente para conectar todos los nodos. Debe ser al menos igual a la cantidad de nodos menos 1.")
else:
    st.success("✅ Cantidad de líneas válida.")

# Guardar en session_state para usar en el paso 2
st.session_state["cantidad_lineas"] = cantidad_lineas

#------------------------------------------------------------------------------------------------------------------------------------

st.header("Paso 2: Creación de Líneas y Transformadores")

# --- Validación del paso anterior ---
if "cantidad_lineas" not in st.session_state:
    st.error("⚠️ Primero completa el Paso 1 para definir la cantidad de líneas.")
    st.stop()

cantidad_lineas = st.session_state["cantidad_lineas"]

# Crear dos columnas
col1, col2 = st.columns(2)

# =========================
# COLUMNA 1 - LÍNEAS
# =========================
with col1:
    st.subheader("Definición de Líneas")

    # Inicialización de datos si no existen o si cambió la cantidad
    if "lineas_data" not in st.session_state or len(st.session_state.lineas_data) != cantidad_lineas:
        st.session_state.lineas_data = [{"origen": "", "destino": ""} for _ in range(cantidad_lineas)]

    if "linea_protegida_idx" not in st.session_state:
        st.session_state.linea_protegida_idx = 0

    opciones_proteccion = [f"Línea {i + 1}" for i in range(cantidad_lineas)]
    linea_protegida = st.radio("Selecciona la línea a proteger:", opciones_proteccion, index=st.session_state.linea_protegida_idx)
    st.session_state.linea_protegida_idx = opciones_proteccion.index(linea_protegida)

    # Ingreso de nodos de cada línea
    for i in range(cantidad_lineas):
        with st.expander(f"📡 Línea {i + 1}", expanded=True):
            col_origen, col_destino = st.columns(2)
            with col_origen:
                origen = st.text_input(f"Origen L{i + 1}", key=f"origen_{i}")
            with col_destino:
                destino = st.text_input(f"Destino L{i + 1}", key=f"destino_{i}")
            st.session_state.lineas_data[i]["origen"] = origen
            st.session_state.lineas_data[i]["destino"] = destino

    # Validación de línea protegida vs transformadores
    lp_idx = st.session_state.linea_protegida_idx
    lp_origen = st.session_state.lineas_data[lp_idx]["origen"].strip()
    lp_destino = st.session_state.lineas_data[lp_idx]["destino"].strip()
    linea_protegida_set = frozenset([lp_origen, lp_destino])

    trafos = st.session_state.get("trafos_data", []) if st.session_state.get("hay_transformadores") == "Sí" else []
    for trafo in trafos:
        t1 = trafo["origen"].strip()
        t2 = trafo["destino"].strip()
        if frozenset([t1, t2]) == linea_protegida_set:
            st.warning("⚠️ La línea seleccionada como protegida no puede ser protegida porque hay un transformador entre los mismos nodos.")
            break

# =========================
# COLUMNA 2 - TRANSFORMADORES
# =========================
with col2:
    st.subheader("Transformadores en la Red")

    hay_transformadores = st.radio(
        "¿Hay transformadores en la red?",
        options=["No", "Sí"],
        index=0,
        key="hay_transformadores"
    )

    if hay_transformadores == "Sí":
        cantidad_transformadores = st.number_input(
            "¿Cuántos transformadores?",
            min_value=1,
            step=1,
            key="num_trafo"
        )

        if "trafos_data" not in st.session_state or len(st.session_state.trafos_data) != cantidad_transformadores:
            st.session_state.trafos_data = [{"origen": "", "destino": ""} for _ in range(cantidad_transformadores)]

        for i in range(cantidad_transformadores):
            with st.expander(f"🔌 Transformador {i + 1}", expanded=True):
                col_origen, col_destino = st.columns(2)
                with col_origen:
                    origen = st.text_input(f"Origen T{i + 1}", key=f"trafo_origen_{i}")
                with col_destino:
                    destino = st.text_input(f"Destino T{i + 1}", key=f"trafo_destino_{i}")
                st.session_state.trafos_data[i]["origen"] = origen
                st.session_state.trafos_data[i]["destino"] = destino

#----------------------------------------------------------------------------------------------------------------------------------------------

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

st.header("Paso 3: Visualización de la Red")

if st.button("Graficar"):
    # --- Inicializar grafo como MultiGraph para permitir múltiples aristas ---
    G = nx.MultiGraph()
    conflictos = set()

    # --- Recuperar datos ---
    lineas = st.session_state.get("lineas_data", [])
    trafos = st.session_state.get("trafos_data", []) if st.session_state.get("hay_transformadores") == "Sí" else []
    linea_idx = st.session_state.get("linea_protegida_idx", None)

    if linea_idx is None or linea_idx >= len(lineas):
        st.error("❌ No se ha seleccionado una línea protegida válida.")
        st.stop()

    linea_protegida = lineas[linea_idx]
    lp_origen = linea_protegida["origen"].strip()
    lp_destino = linea_protegida["destino"].strip()
    linea_protegida_set = frozenset([lp_origen, lp_destino])

    lineas_set = []
    trafos_set = set()

    # --- Agregar líneas ---
    for linea in lineas:
        n1 = linea["origen"].strip()
        n2 = linea["destino"].strip()
        if n1 and n2:
            key = frozenset([n1, n2])
            lineas_set.append(key)
            G.add_edge(n1, n2, tipo="linea")

    # --- Agregar transformadores y validar conflictos ---
    for trafo in trafos:
        t1 = trafo["origen"].strip()
        t2 = trafo["destino"].strip()
        par = frozenset([t1, t2])
        if par in lineas_set:
            conflictos.add(tuple(sorted([t1, t2])))
        else:
            trafos_set.add(par)
            G.add_edge(t1, t2, tipo="trafo")

    if linea_protegida_set in trafos_set:
        st.warning("⚠️ La línea seleccionada como protegida no puede ser protegida porque hay un transformador entre los mismos nodos.")
        st.stop()

    if conflictos:
        st.error(f"❌ Conflicto: hay líneas y transformadores entre los mismos nodos: {list(conflictos)}")
        st.stop()

    # --- Dibujar el grafo ---
    st.subheader("🔍 Visualización de la Red")
    fig, ax = plt.subplots(figsize=(8, 6))
    pos = nx.spring_layout(G, seed=42)

    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color="lightblue", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold", ax=ax)

    # Dibujar líneas (soporta paralelas con desplazamiento)
    edges_lineas = [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True) if d["tipo"] == "linea"]
    multi_edges = defaultdict(list)
    for u, v, k in edges_lineas:
        key = frozenset([u, v])
        multi_edges[key].append((u, v, k))

    # Identificar el índice de la línea protegida en el conjunto total
    linea_protegida_idx = st.session_state.linea_protegida_idx
    lineas_en_grafo = list(G.edges(keys=True, data=True))
    lineas_tipo_linea = [e for e in lineas_en_grafo if e[3].get("tipo") == "linea"]

    # Obtener el triple (u, v, k) de la línea protegida
    if linea_protegida_idx < len(lineas_tipo_linea):
        linea_protegida_u, linea_protegida_v, linea_protegida_k, _ = lineas_tipo_linea[linea_protegida_idx]
    else:
        linea_protegida_u = linea_protegida_v = linea_protegida_k = None  # caso inválido

    for edge_list in multi_edges.values():
        n = len(edge_list)
        for i, (u, v, k) in enumerate(edge_list):
            offset = (i - (n - 1) / 2) * 0.05
            x0, y0 = pos[u]
            x1, y1 = pos[v]

            dx = y1 - y0
            dy = x0 - x1
            norm = (dx ** 2 + dy ** 2) ** 0.5 or 1
            dx /= norm
            dy /= norm

            x0_off = x0 + offset * dx
            y0_off = y0 + offset * dy
            x1_off = x1 + offset * dx
            y1_off = y1 + offset * dy

            # Verificar si esta es la línea protegida exacta (por índice y clave)
            is_protected = (u == linea_protegida_u and v == linea_protegida_v and k == linea_protegida_k) or \
                        (v == linea_protegida_u and u == linea_protegida_v and k == linea_protegida_k)

            color = "green" if is_protected else "gray"
            ax.plot([x0_off, x1_off], [y0_off, y1_off], color=color, linewidth=3)


    # Dibujar transformadores
    edges_trafos = [(u, v) for u, v, d in G.edges(data=True) if d["tipo"] == "trafo"]
    nx.draw_networkx_edges(G, pos, edgelist=edges_trafos, style="dashed", width=2, edge_color="red", ax=ax)

    for u, v in edges_trafos:
        # Punto medio para poner la letra T
        x = (pos[u][0] + pos[v][0]) / 2
        y = (pos[u][1] + pos[v][1]) / 2
        ax.text(x, y, "T", fontsize=14, fontweight="bold", ha="center", va="center",
                bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3"))

    # === Dibujar recuadro "R" encima de la línea protegida, cerca al nodo de origen ===
    if lp_origen in pos and lp_destino in pos:
        x0, y0 = pos[lp_origen]
        x1, y1 = pos[lp_destino]

        # Calcular punto entre origen y destino, más cerca del origen (70%)
        rx = x0 * 0.8 + x1 * 0.2
        ry = y0 * 0.8 + y1 * 0.2

        ax.text(
            rx, ry, "R",
            fontsize=14, fontweight="bold", ha="center", va="center",
            bbox=dict(facecolor="mediumpurple", edgecolor="black", boxstyle="round,pad=0.3")
        )

    
    st.pyplot(fig)

#-----------------------------------------------------------------------------------------------------------------------------7
import streamlit as st

st.header("Paso 4: Ingreso de Parámetros Eléctricos")

# Recuperar entradas del paso 1 (con fallback por si acaso)
rtc = st.session_state.get("rtc", 1.0)
rtp = st.session_state.get("rtp", 1.0)
ajuste_impedancia = rtc / rtp if rtp != 0 else 1.0

# Recuperar entradas del paso 2
lineas = st.session_state.get("lineas_data", [])
trafos = st.session_state.get("trafos_data", []) if st.session_state.get("hay_transformadores") == "Sí" else []

# Crear sets de nodos conectados para evitar duplicación
trafos_set = {frozenset([t["origen"].strip(), t["destino"].strip()]) for t in trafos}

# Crear columnas principales
col_lineas, col_trafos = st.columns(2)

# Inicialización de parámetros si no existe
if "param_lineas" not in st.session_state:
    st.session_state.param_lineas = {}
if "param_trafos" not in st.session_state:
    st.session_state.param_trafos = {}

# ============================
# COLUMNA IZQUIERDA: LÍNEAS
# ============================
with col_lineas:
    st.subheader("Parámetros de Líneas")

    for linea in lineas:
        origen = linea["origen"].strip()
        destino = linea["destino"].strip()
        par = frozenset([origen, destino])

        if not origen or not destino or par in trafos_set:
            continue

        key = f"{origen}_{destino}"
        if key not in st.session_state.param_lineas:
            st.session_state.param_lineas[key] = {
                "z_mag": 0.0, "z_ang": 0.0, "i_mag": 0.0, "i_ang": 0.0
            }

        with st.expander(f"📡 Línea ({origen} → {destino})", expanded=True):
            st.markdown("**Impedancia Z**")
            col1, col2 = st.columns(2)
            with col1:
                z_mag_input = st.number_input(
                    f"Magnitud (Ω) [{key}]", key=f"z_mag_{key}", min_value=0.0, format="%.4f"
                )
            with col2:
                z_ang_input = st.number_input(
                    f"Ángulo (°) [{key}]", key=f"z_ang_{key}", format="%.2f"
                )

            st.session_state.param_lineas[key]["z_mag"] = z_mag_input * ajuste_impedancia
            st.session_state.param_lineas[key]["z_ang"] = z_ang_input

            st.markdown("**Corriente de Cortocircuito**")
            col3, col4 = st.columns(2)
            with col3:
                st.session_state.param_lineas[key]["i_mag"] = st.number_input(
                    f"Magnitud (A) [{key}]", key=f"i_mag_{key}", min_value=0.0, format="%.2f"
                )
            with col4:
                st.session_state.param_lineas[key]["i_ang"] = st.number_input(
                    f"Ángulo (°) [{key}]", key=f"i_ang_{key}", format="%.2f"
                )

# ===============================
# COLUMNA DERECHA: TRANSFORMADORES
# ===============================
with col_trafos:
    st.subheader("Parámetros de Transformadores")

    for trafo in trafos:
        origen = trafo["origen"].strip()
        destino = trafo["destino"].strip()
        if not origen or not destino:
            continue

        key = f"{origen}_{destino}"
        if key not in st.session_state.param_trafos:
            st.session_state.param_trafos[key] = {
                "z_mag": 0.0, "z_ang": 0.0, "i_mag": 0.0, "i_ang": 0.0
            }

        with st.expander(f"🔌 Transformador ({origen} → {destino})", expanded=True):
            st.markdown("**Impedancia Z**")
            col1, col2 = st.columns(2)
            with col1:
                z_mag_input = st.number_input(
                    f"Magnitud (Ω) [{key}]", key=f"z_mag_trafo_{key}", min_value=0.0, format="%.4f"
                )
            with col2:
                z_ang_input = st.number_input(
                    f"Ángulo (°) [{key}]", key=f"z_ang_trafo_{key}", format="%.2f"
                )

            st.session_state.param_trafos[key]["z_mag"] = z_mag_input * ajuste_impedancia
            st.session_state.param_trafos[key]["z_ang"] = z_ang_input

            st.markdown("**Corriente de Cortocircuito**")
            col3, col4 = st.columns(2)
            with col3:
                st.session_state.param_trafos[key]["i_mag"] = st.number_input(
                    f"Magnitud (A) [{key}]", key=f"i_mag_trafo_{key}", min_value=0.0, format="%.2f"
                )
            with col4:
                st.session_state.param_trafos[key]["i_ang"] = st.number_input(
                    f"Ángulo (°) [{key}]", key=f"i_ang_trafo_{key}", format="%.2f"
                )



#-----------------------------------------------------------------------------------------------------------------------------------
import math
import cmath
import streamlit as st

st.header("Paso 5: Coordinación de Protección")

st.subheader("Alcances de protección")
st.markdown("#### Zona 1")
st.markdown(
    "*⏱️ Tiempo de operación: Instantaneo*"
)

# Asegurar que trafos_data esté inicializado
if "trafos_data" not in st.session_state:
    st.session_state.trafos_data = []

if "param_trafos" not in st.session_state:
    st.session_state.param_trafos = {}

if "lineas_data" not in st.session_state:
    st.session_state.lineas_data = []

if "param_lineas" not in st.session_state:
    st.session_state.param_lineas = {}


# Obtener la línea protegida
linea_idx = st.session_state.linea_protegida_idx
linea_protegida = st.session_state.lineas_data[linea_idx]
lp_origen = linea_protegida["origen"].strip()
lp_destino = linea_protegida["destino"].strip()
key_lp = f"{lp_origen}_{lp_destino}"

# Verificar si la línea protegida está en los parámetros
if key_lp not in st.session_state.param_lineas:
    st.error("❌ No se encontraron los parámetros de la línea protegida.")
    st.stop()

# Obtener impedancia de la línea protegida
z_mag = st.session_state.param_lineas[key_lp]["z_mag"]
z_ang_deg = st.session_state.param_lineas[key_lp]["z_ang"]
z_ang_rad = math.radians(z_ang_deg)

# Calcular impedancia compleja
z_linea = cmath.rect(z_mag, z_ang_rad)

#st.latex(f"{z_linea}")

# Zona 1 - Ajuste con porcentaje
st.markdown("#### Zona 1")
st.markdown("*⏱️ Tiempo de operación: Instantáneo*")

# Slider para porcentaje
porcentaje_z1 = st.slider(
    "Selecciona el porcentaje del alcance de la Zona 1:",
    min_value=0,
    max_value=100,
    value=85,
    step=1
)

# Calcular Z_alcance_z1
factor_z1 = porcentaje_z1 / 100
z_alcance_z1 = factor_z1 * z_linea
#st.latex(f"{z_alcance_z1}")

# Mostrar resultado
st.markdown("**Resultado:**")
mod = abs(z_alcance_z1)
ang = math.degrees(cmath.phase(z_alcance_z1))
st.latex(f"Z_{{alcance\\_z1}} = {mod:.4f} \\angle {ang:.2f}^\\circ \\, \\Omega")




st.markdown("#### Zona 2")
st.markdown(
    "*⏱️ Tiempo de operación: **300–400 ms** con Esquema PUTT, "
    "**150–250 ms** sin esquema de teleprotección*"
)
# Reusar z_linea de zona 1
z2_min = 1.2 * z_linea

# ---------------------------------------------------
# Buscar líneas conectadas al nodo de destino
lineas_conectadas = []
for linea in st.session_state.lineas_data:
    o = linea["origen"].strip()
    d = linea["destino"].strip()
    if not o or not d:
        continue
    if {o, d} == {lp_origen, lp_destino}:
        continue  # evitar incluir la línea protegida
    if lp_destino in (o, d):
        key = f"{o}_{d}"
        if key in st.session_state.param_lineas:
            z_mag = st.session_state.param_lineas[key]["z_mag"]
            z_ang = math.radians(st.session_state.param_lineas[key]["z_ang"])
            z = cmath.rect(z_mag, z_ang)
            lineas_conectadas.append(z)

if lineas_conectadas:
    z_min_linea = min(lineas_conectadas, key=abs)
    z2_med = z_linea + 0.5 * z_min_linea
else:
    z2_med = 0

# ---------------------------------------------------
# Buscar transformadores conectados al nodo de destino
trafos_conectados = []
for trafo in st.session_state.trafos_data:
    o = trafo["origen"].strip()
    d = trafo["destino"].strip()
    if lp_destino in (o, d):
        key = f"{o}_{d}"
        if key in st.session_state.param_trafos:
            z_mag = st.session_state.param_trafos[key]["z_mag"]
            z_ang = math.radians(st.session_state.param_trafos[key]["z_ang"])
            z = cmath.rect(z_mag, z_ang)
            trafos_conectados.append(z)

if trafos_conectados:
    z_min_trafo = min(trafos_conectados, key=abs)
    z2_max = z_linea + 0.5 * z_min_trafo
else:
    z2_max = float('inf') ## CONDICION DE QUE NO HAY TRAFO Y EL VALOR SE VA A INFINITO

# ---------------------------------------------------
# Selección del alcance de zona 2
z_alcance_z2 = z2_min  # default

if abs(z2_med) < abs(z2_min):
    z_alcance_z2 = z2_med
elif abs(z2_med) > abs(z2_max):
    z_alcance_z2 = z2_max
else:
    z_alcance_z2 = z2_min

# ---------------------------------------------------
# Mostrar resultados
st.markdown("**Resultado:**")

mod1 = abs(z2_min)
ang1 = math.degrees(cmath.phase(z2_min))
mod2 = abs(z2_med)
ang2 = math.degrees(cmath.phase(mod2))
mod3 = abs(z2_max)
ang3 = math.degrees(cmath.phase(z2_max))

st.latex(f"Z_{{z2\\_min}} = {mod1:.4f} \\angle {ang1:.2f}^\\circ \\, \\Omega")
st.latex(f"Z_{{z2\\_}} = {mod2:.4f} \\angle {ang2:.2f}^\\circ \\, \\Omega")
st.latex(f"Z_{{z2\\_max}} = {mod3:.4f} \\angle {ang3:.2f}^\\circ \\, \\Omega")

st.markdown(
    "*Valor escogido*"
)

mod = abs(z_alcance_z2)
ang = math.degrees(cmath.phase(z_alcance_z2))
st.latex(f"Z_{{alcance\\_z2}} = {mod:.4f} \\angle {ang:.2f}^\\circ \\, \\Omega")





st.markdown("#### Zona 3")
st.markdown(
    "*⏱️ Tiempo de operación: **800–1000 ms***"
)
# ------------------------------------------
z_mayor_linea = None
for linea in st.session_state.lineas_data:
    o = linea["origen"].strip()
    d = linea["destino"].strip()
    if not o or not d:
        continue
    if {o, d} == {lp_origen, lp_destino}:
        continue  # evitar la línea protegida
    if o == lp_destino:  # solo las que INICIAN en el nodo destino
        key = f"{min(o, d)}_{max(o, d)}"
        if key in st.session_state.param_lineas:
            z_mag = st.session_state.param_lineas[key]["z_mag"]
            z_ang = math.radians(st.session_state.param_lineas[key]["z_ang"])
            z = cmath.rect(z_mag, z_ang)
            if not z_mayor_linea or abs(z) > abs(z_mayor_linea):
                z_mayor_linea = z
                

if z_mayor_linea is None:
    z_mayor_linea = 0j



# ------------------------------------------
# Buscar trafo con mayor impedancia conectado al nodo destino
z_mayor_trafo = None
for trafo in st.session_state.trafos_data:
    o = trafo["origen"].strip()
    d = trafo["destino"].strip()
    if lp_destino in (o, d):
        key = f"{o}_{d}"
        if key in st.session_state.param_trafos:
            z_mag = st.session_state.param_trafos[key]["z_mag"]
            z_ang = math.radians(st.session_state.param_trafos[key]["z_ang"])
            z = cmath.rect(z_mag, z_ang)
            if not z_mayor_trafo or abs(z) > abs(z_mayor_trafo):
                z_mayor_trafo = z

if not z_mayor_trafo:
    z_mayor_trafo = float('inf')

# ------------------------------------------
# Cálculos de Z3_1, Z3_2, Z3_3
z3_1 = 1.2 * (z_linea + z_mayor_linea)
z3_2 = z_linea + 1.25 * z_mayor_linea
z3_3 = z_linea + 0.8 * z_mayor_trafo



mod1 = abs(z3_1)
ang1 = math.degrees(cmath.phase(z3_1))
mod2 = abs(z3_2)
ang2 = math.degrees(cmath.phase(z3_2))
mod3 = abs(z3_3)
ang3 = math.degrees(cmath.phase(z3_3))


# Mostrar resultado
st.markdown("**Resultado:**")

st.latex(f"Z_{{z3\\_1}} = {mod1:.4f} \\angle {ang1:.2f}^\\circ \\, \\Omega")
st.latex(f"Z_{{z3\\_}} = {mod2:.4f} \\angle {ang2:.2f}^\\circ \\, \\Omega")
st.latex(f"Z_{{z3\\_3}} = {mod3:.4f} \\angle {ang3:.2f}^\\circ \\, \\Omega")

# Seleccionar el valor con menor magnitud
z_alcance_z3 = min([z3_1, z3_2, z3_3], key=abs)

st.markdown(
    "*Valor escogido*"
)

mod = abs(z_alcance_z3)
ang = math.degrees(cmath.phase(z_alcance_z3))
st.latex(f"Z_{{alcance\\_z3}} = {mod:.4f} \\angle {ang:.2f}^\\circ \\, \\Omega")

st.markdown("#### Zona 4")
st.markdown(
    "*⏱️ Tiempo de operación: **<1500 ms***"
)

# -----------------------------
# Z4_1: 20% de la línea más corta que inicia en el nodo de origen
z_min_linea_inicio = None
for linea in st.session_state.lineas_data:
    o = linea["origen"].strip()
    d = linea["destino"].strip()
    if not o or not d:
        continue
    if {o, d} == {lp_origen, lp_destino}:
        continue  # evitar la línea protegida
    if o == lp_origen:
        key = f"{o}_{d}"
        if key in st.session_state.param_lineas:
            z_mag = st.session_state.param_lineas[key]["z_mag"]
            z_ang = math.radians(st.session_state.param_lineas[key]["z_ang"])
            z = cmath.rect(z_mag, z_ang)
            if not z_min_linea_inicio or abs(z) < abs(z_min_linea_inicio):
                z_min_linea_inicio = z

z4_1 = 0.2 * z_min_linea_inicio if z_min_linea_inicio else 0

# -----------------------------
# Z4_2: 20% de la impedancia de la línea protegida
z4_2 = 0.2 * z_linea

# -----------------------------
# Z4_3: 20% del trafo más pequeño conectado al nodo de origen
z_min_trafo_origen = None
for trafo in st.session_state.trafos_data:
    o = trafo["origen"].strip()
    d = trafo["destino"].strip()
    if lp_origen in (o, d):
        key = f"{o}_{d}"
        if key in st.session_state.param_trafos:
            z_mag = st.session_state.param_trafos[key]["z_mag"]
            z_ang = math.radians(st.session_state.param_trafos[key]["z_ang"])
            z = cmath.rect(z_mag, z_ang)
            if not z_min_trafo_origen or abs(z) < abs(z_min_trafo_origen):
                z_min_trafo_origen = z

z4_3 = 0.2 * z_min_trafo_origen if z_min_trafo_origen else 0

# -----------------------------
# Selección final por menor módulo
#z_alcance_z4 = min([z4_1, z4_2, z4_3], key=abs)
z_alcance_z4 = min((z for z in [z4_1, z4_2, z4_3] if z != 0), key=abs)

# -----------------------------
# Mostrar resultado
st.markdown("**Resultado:**")

mod1 = abs(z4_1)
ang1 = math.degrees(cmath.phase(z4_1))
mod2 = abs(z4_2)
ang2 = math.degrees(cmath.phase(z4_2))
mod3 = abs(z4_3)
ang3 = math.degrees(cmath.phase(z4_3))


# Mostrar resultado
st.markdown("**Resultado:**")

st.latex(f"Z_{{z4\\_1}} = {mod1:.4f} \\angle {ang1:.2f}^\\circ \\, \\Omega")
st.latex(f"Z_{{z4\\_}} = {mod2:.4f} \\angle {ang2:.2f}^\\circ \\, \\Omega")
st.latex(f"Z_{{z4\\_3}} = {mod3:.4f} \\angle {ang3:.2f}^\\circ \\, \\Omega")

st.markdown(
    "*Valor escogido*"
)

mod = abs(z_alcance_z4)
ang = math.degrees(cmath.phase(z_alcance_z4))
st.latex(f"Z_{{alcance\\_z4}} = {mod:.4f} \\angle {ang:.2f}^\\circ \\, \\Omega")

#---------------------------------------------------------------------------------------------------------------------------------------
st.markdown("## Paso 6 – Ajustes de Protección")

col1, col2 = st.columns(2)

# -----------------------
# 🟦 Columna 1: Ajuste por R_Arco
with col1:
    st.markdown("### Ajuste por Rₐᵣcₒ")

    # Selección del ángulo
    theta_escogido_deg = st.selectbox(
        "Selecciona el ángulo de ajuste (Theta):",
        [45, 60, 75],
        index=1,
        key="theta_arco"
    )
    theta_escogido_rad = math.radians(theta_escogido_deg)

    # Función para calcular R_Arco (como impedancia compleja)
    def calcular_r_arco(z_original, theta_ajuste_rad):
        modulo = abs(z_original)
        angulo_z = cmath.phase(z_original)
        try:
            nuevo_modulo = modulo / math.cos(angulo_z - theta_ajuste_rad)
        except ZeroDivisionError:
            nuevo_modulo = float("inf")
        return cmath.rect(nuevo_modulo, theta_ajuste_rad)

    # Calcular impedancias ajustadas
    r_arco_z1 = calcular_r_arco(z_alcance_z1, theta_escogido_rad)
    r_arco_z2 = calcular_r_arco(z_alcance_z2, theta_escogido_rad)
    r_arco_z3 = calcular_r_arco(z_alcance_z3, theta_escogido_rad)
    r_arco_z4 = calcular_r_arco(z_alcance_z4, theta_escogido_rad)

    # Mostrar resultados
    for i, z in enumerate([r_arco_z1, r_arco_z2, r_arco_z3, r_arco_z4], start=1):
        mod = abs(z)
        ang = math.degrees(cmath.phase(z))
        st.latex(f"R_{{Arco\\_Z\\_alcance\\_z{i}}} = {mod:.4f} \\angle {ang:.2f}^\\circ \\, \\Omega")

# -----------------------
# -----------------------
# -----------------------
# 🟨 Columna 2: Ajuste por Infeed – Zona 2
with col2:
    st.markdown("### Ajuste por Infeed – Zona 2")

    st.markdown("*Este ajuste utiliza la corriente de cortocircuito del paso 4.*")

    # Obtener origen y destino de la línea protegida
    origen_lp = st.session_state.lineas_data[st.session_state.linea_protegida_idx]["origen"].strip()
    destino_lp = st.session_state.lineas_data[st.session_state.linea_protegida_idx]["destino"].strip()
    key_lp = f"{origen_lp}_{destino_lp}"

    # Corriente del relé = corriente de la línea protegida
    ir = st.session_state.param_lineas.get(key_lp, {}).get("i_mag", 1.0)

    # Determinar qué impedancia fue usada para z_alcance_z2
    if abs(z_alcance_z2 - z2_min) < 1e-6:
        z_excluir = z_min_linea  # Línea más corta
        tipo_excluir = "linea"
    elif abs(z_alcance_z2 - z2_max) < 1e-6:
        z_excluir = z_min_trafo  # Trafo más corto
        tipo_excluir = "trafo"
    else:
        z_excluir = None
        tipo_excluir = None

    if_total = 0.0

    # Líneas aguas abajo
    for linea in st.session_state.lineas_data:
        o = linea["origen"].strip()
        d = linea["destino"].strip()
        if o == destino_lp:
            key = f"{o}_{d}"
            if key in st.session_state.param_lineas:
                z_mag = st.session_state.param_lineas[key]["z_mag"]
                z_ang = math.radians(st.session_state.param_lineas[key]["z_ang"])
                z_actual = cmath.rect(z_mag, z_ang)
                if not (tipo_excluir == "linea" and abs(z_actual - z_excluir) < 1e-6):
                    if_total += st.session_state.param_lineas[key]["i_mag"]

    # Transformadores aguas abajo
    for trafo in st.session_state.trafos_data:
        o = trafo["origen"].strip()
        d = trafo["destino"].strip()
        if o == destino_lp:
            key = f"{o}_{d}"
            if key in st.session_state.param_trafos:
                z_mag = st.session_state.param_trafos[key]["z_mag"]
                z_ang = math.radians(st.session_state.param_trafos[key]["z_ang"])
                z_actual = cmath.rect(z_mag, z_ang)
                if not (tipo_excluir == "trafo" and abs(z_actual - z_excluir) < 1e-6):
                    if_total += st.session_state.param_trafos[key]["i_mag"]

    # Calcular K y Z2 corregida
    k_infeed = if_total / ir if ir != 0 else 0
    z2_infeed = z_alcance_z2 * (1 + k_infeed)

    st.markdown("**Cálculos automáticos:**")
    st.write(f"Corriente del relé (I_r): {ir:.2f} A")
    st.write(f"Corrientes aguas abajo (I_f): {if_total:.2f} A")
    st.write(f"Factor de Infeed (K): {k_infeed:.2f}")

    st.markdown("**Resultado corregido por Infeed:**")
    mod = abs(z2_infeed)
    ang = math.degrees(cmath.phase(z2_infeed))
    st.latex(f"Z_{{alcance\\_z2\\_infeed}} = {mod:.4f} \\angle {ang:.2f}^\\circ \\, \\Omega")

    st.markdown("### Ajuste por Infeed – Zona 3")

    # Determinar qué impedancia fue usada para z_alcance_z3
    if abs(z_alcance_z3 - z3_1) < 1e-6:
        z_excluir = z_mayor_linea
        tipo_excluir = "linea"
    elif abs(z_alcance_z3 - z3_2) < 1e-6:
        z_excluir = z_mayor_linea
        tipo_excluir = "linea"
    elif abs(z_alcance_z3 - z3_3) < 1e-6:
        z_excluir = z_mayor_trafo
        tipo_excluir = "trafo"
    else:
        z_excluir = None
        tipo_excluir = None

    if_total_z3 = 0.0

    # Líneas aguas abajo desde el nodo destino
    for linea in st.session_state.lineas_data:
        o = linea["origen"].strip()
        d = linea["destino"].strip()
        if o == destino_lp:
            key = f"{o}_{d}"
            if key in st.session_state.param_lineas:
                z_mag = st.session_state.param_lineas[key]["z_mag"]
                z_ang = math.radians(st.session_state.param_lineas[key]["z_ang"])
                z_actual = cmath.rect(z_mag, z_ang)
                if not (tipo_excluir == "linea" and abs(z_actual - z_excluir) < 1e-6):
                    if_total_z3 += st.session_state.param_lineas[key]["i_mag"]

    # Transformadores aguas abajo desde el nodo destino
    for trafo in st.session_state.trafos_data:
        o = trafo["origen"].strip()
        d = trafo["destino"].strip()
        if o == destino_lp:
            key = f"{o}_{d}"
            if key in st.session_state.param_trafos:
                z_mag = st.session_state.param_trafos[key]["z_mag"]
                z_ang = math.radians(st.session_state.param_trafos[key]["z_ang"])
                z_actual = cmath.rect(z_mag, z_ang)
                if not (tipo_excluir == "trafo" and abs(z_actual - z_excluir) < 1e-6):
                    if_total_z3 += st.session_state.param_trafos[key]["i_mag"]

    # Calcular K y Z3 corregida
    k_infeed_z3 = if_total_z3 / ir if ir != 0 else 0
    z3_infeed = z_alcance_z3 * (1 + k_infeed_z3)

    st.markdown("**Cálculos automáticos Zona 3:**")
    st.write(f"Corriente del relé (I_r): {ir:.2f} A")
    st.write(f"Corrientes aguas abajo (I_f): {if_total_z3:.2f} A")
    st.write(f"Factor de Infeed (K): {k_infeed_z3:.2f}")

    st.markdown("**Resultado corregido por Infeed:**")
    mod = abs(z3_infeed)
    ang = math.degrees(cmath.phase(z3_infeed))
    st.latex(f"Z_{{alcance\\_z3\\_infeed}} = {mod:.4f} \\angle {ang:.2f}^\\circ \\, \\Omega")


#------------------------------------------------------------------------------------------------

# Función actualizada
def graficar_zonas_con_circulos(z1, z2, z3, z4):
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(10, 8))

    def graficar_z(z, color, etiqueta):
        x = z.real
        y = z.imag
        radio = abs(z) / 2
        angulo = np.angle(z)
        centro_x = radio * np.cos(angulo)
        centro_y = radio * np.sin(angulo)

        circulo = plt.Circle((centro_x, centro_y), radio, color=color, fill=False, linestyle='--', linewidth=2, label=f"{etiqueta} (|Z|={abs(z):.2f})")
        ax.add_patch(circulo)
        ax.plot(x, y, 'o', color=color)
        ax.plot([0, x], [0, y], color=color, linewidth=1, linestyle=':')

    graficar_z(z1, 'blue', 'Zona 1 (R_arco)')
    graficar_z(z2, 'green', 'Zona 2 (R_arco)')
    graficar_z(z3, 'red', 'Zona 3 (R_arco)')
    graficar_z(z4, 'orange', 'Zona 4 (R_arco)')

    ax.set_xlabel('Parte Real (Ω)')
    ax.set_ylabel('Parte Imaginaria (Ω)')
    ax.set_title('Zonas de Protección con Ajuste por Rₐᵣcₒ')
    ax.grid(True)
    ax.legend()
    ax.set_aspect('equal', adjustable='box')
    ax.axhline(0, color='gray', linewidth=0.5)
    ax.axvline(0, color='gray', linewidth=0.5)

    return fig

# Mostrar en Streamlit con los valores ajustados
fig = graficar_zonas_con_circulos(r_arco_z1, r_arco_z2, r_arco_z3, r_arco_z4)
st.pyplot(fig, use_container_width=True)
