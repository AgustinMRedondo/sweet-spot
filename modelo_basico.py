import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import datetime
from PIL import Image


def mb():
    # =======================
    # 1. INPUTS INTERACTIVOS
    # =======================
    with st.sidebar:
        equity = st.number_input("Capital necesario (equity) (€)", value=1000, step=1000, format="%d")
        acq_cost = st.number_input("Coste total de compra del activo (€)", value=1000, step=1000, format="%d")
        tasacion = st.number_input("Valor de tasación del activo", value=1000, step=1000, format="%d")
        hard_costs = st.number_input("Coste de obra/CAPEX (€)", value=1000, step=1000, format="%d")
        soft_costs_sin_fee = st.number_input("Costes indirectos (sin fee) (€)", value=1000, step=1000, format="%d")
        comercial_cost = st.number_input("Coste comercial (agencia inmobiliaria) (€)", value=0, step=1000, format="%d")
        ingresos_esperados = st.number_input("Ingresos esperados (€)", value=2000, step=1000, format="%d")
        total_unidades = st.number_input("Total de unidades", value=1, step=1)
        meses_totales = st.slider("Meses totales del proyecto", min_value=1, max_value=24, value=12)
        comision_apertura_interes = st.slider("Comisión de apertura (%)", min_value=1.5, max_value=6.0, value=3.0, step=0.1) / 100
        tasa_anual_deuda = st.slider("Tipo interés anual (%)", min_value=0.0, max_value=30.0, value=13.5, step=0.1) / 100
        

    # ==========================
    # 2. CÁLCULOS PRINCIPALES
    # ==========================
    # Calcular deuda total
    deuda_total = 0
    tolerancia = 1
    max_iteraciones = 100
    iteraciones = 0
    
    while tolerancia > 0.01 and iteraciones < max_iteraciones:
        deuda_total_pre = hard_costs + soft_costs_sin_fee + acq_cost - equity
        comision_levantamiento = (1.5 / 100) * deuda_total_pre
        credere_fee = (
            (1.2 / 100) * hard_costs +
            (0.3 / 100) * deuda_total_pre +
            comision_levantamiento
        )
        deuda_total_nueva = deuda_total_pre + credere_fee
        tolerancia = abs(deuda_total_nueva - deuda_total)
        deuda_total = deuda_total_nueva
        iteraciones += 1

    soft_costs_con_fee = soft_costs_sin_fee + credere_fee
    total_costs_sin_deuda = hard_costs + soft_costs_con_fee + acq_cost + comercial_cost

    # Calcular disposiciones (outflows)
    disposiciones_totales = meses_totales - 1
    disposicion_media_hard_cost = hard_costs / disposiciones_totales
    disposicion_media_soft_cost = soft_costs_con_fee / disposiciones_totales
    disposición_inicial = acq_cost

    outflows = [0] * meses_totales
    outflows[0] = disposición_inicial + (disposicion_media_hard_cost + disposicion_media_soft_cost)
    for mes in range(1, disposiciones_totales):
        outflows[mes] += disposicion_media_hard_cost + disposicion_media_soft_cost
    outflows[-1] = 0

    # Calcular inflows
    inflows = [0] * meses_totales
    deuda_mes = [0] * meses_totales
    inflow_inicial = equity
    inflow_final = ingresos_esperados
    inflows[0] = inflow_inicial

    for mes in range(meses_totales):
        net_cashflow = sum(inflows[:mes + 1]) - sum(outflows[:mes + 1])
        if net_cashflow < 0:
            deuda = abs(net_cashflow)
            inflows[mes] += deuda
            deuda_mes[mes] = deuda
    inflows[-1] = inflow_final

    # Calcular intereses y ajustar el último outflow
    intereses_por_disposicion = [0] * meses_totales
    tasa_mensual_dis = tasa_anual_deuda / 12
    deuda_acumulada = 0

    for mes in range(meses_totales):
        if deuda_mes[mes] > 0:
            meses_restantes = meses_totales - mes
            intereses_por_disposicion[mes] = deuda_mes[mes] * tasa_mensual_dis * meses_restantes
            deuda_acumulada += deuda_mes[mes]

    intereses_acumulados = sum(intereses_por_disposicion)
    comision_apertura = deuda_total * comision_apertura_interes
    outflows[-1] += deuda_acumulada + intereses_acumulados + comision_apertura

    # Net cashflow
    net_cashflow = [inflows[mes] - outflows[mes] for mes in range(meses_totales)]

    # EBIT y ratios
    EBIT = net_cashflow[-1] - equity
    ROI_prom = EBIT / equity
    ROI_anualizado = ROI_prom / meses_totales * 12

    # Ratios del inversor
    comision_apertura_com_int =  1.5/100 #HAY UN 1.5% QUE SIEMPRE DE DISTRIBUYE A ALGUIEN QUE NO ES EL INVERSOR
    comision_apertura_com =  deuda_acumulada * comision_apertura_com_int
    free_cash_inver = intereses_acumulados + comision_apertura - comision_apertura_com
    ROI_inv = free_cash_inver/deuda_total
    ROI_inv_anualizado = ROI_inv/meses_totales*12

    # Ratios iniciales
    LTV = deuda_total/ingresos_esperados
    LTV_inicial = (inflows[0] - equity) / tasacion
    LTC = (deuda_total) / total_costs_sin_deuda

    # ==========================
    # 3. VISUALIZACIÓN DE RESULTADOS E INPUTS CUALITATIVOS DEL PROYECTO
    # ==========================
    with st.expander("Información del proyecto (Rellenar)"):
        fecha_creacion = datetime.date.today()
        st.text(f"Fecha de creación del informe: {fecha_creacion}")
        titulo = st.text_input("Titulo del proyecto", value= "Proyecto")
        localizacion = st.text_input("Localización del proyecto", value = "Provincia, España")
        descripcion = st.text_area("Descripción del proyecto", value = "Descripción")
        fecha_financiacion = st.date_input("Fecha de neceisdad de financiación")
    

    st.markdown("<h1 style='text-align: center;'>Condiciones deuda</h1>", unsafe_allow_html=True)
    col_tasa, col_aper, col_dur = st.columns(3)
    with col_tasa:
        st.metric("Tasa anual", f"{tasa_anual_deuda:.2%}")
    with col_aper:
        st.metric("Comisión apertura", f"{comision_apertura_interes:.2%}")
    with col_dur:
        st.metric("Duración", f"{meses_totales:,.0f} meses" )

    st.markdown("<h1 style='text-align: center;'>Resumen</h1>", unsafe_allow_html=True)
    col_ratio, col_promotor, col_deuda= st.columns(3)
    with col_ratio:
        st.subheader("Proyecto")
        st.metric("Coste total sin intereses", f"{total_costs_sin_deuda:,.0f} €")
        st.metric("Ingresos totales", f"{ingresos_esperados:,.0f} €")
        st.metric("EBIT", f"{EBIT:,.0f} €")
        st.metric("LTV Inicial", f"{LTV_inicial:.2%}")
        st.metric("LTV", f"{LTV:.2%}")
        st.metric("LTC", f"{LTC:.2%}")
    
    with col_promotor:
        st.subheader("Promotor")
        st.metric("Equity aportado", f"{equity:,.0f} €")
        st.metric("Valor del garantía",f"{tasacion:,.0f} €")
        st.metric("ROI Promotor", f"{ROI_prom:.2%}")
        st.metric("ROI Promotor Anualizado", f"{ROI_anualizado:.2%}")
        st.metric("Coste real de la deuda + fees", f"{(intereses_acumulados+comision_apertura+credere_fee)/deuda_total:.2%}")
        st.metric ("EBIT sobre ingresos", f"{EBIT/ingresos_esperados:.2%}")

    with col_deuda:
        st.subheader("Deuda")
        st.metric("Deuda necesaria", f"{deuda_total:,.0f} €")
        st.metric("Total adeudado", f"{outflows[-1]:,.0f} €")
        st.metric("Intereses totales", f"{intereses_acumulados:,.0f} €" )
        st.metric("Comision apertura", f"{comision_apertura:,.0f} €")
        st.metric("Rendimiento Deuda", f"{ROI_inv:.2%}")
        st.metric("Rendimiento Deuda anualizado", f"{ROI_inv_anualizado:.2%}")


    st.markdown("<h1 style='text-align: center;'>Cuenta de resultados</h1>", unsafe_allow_html=True)

    reporte = f"""

Ingresos Totales:                                   €{ingresos_esperados:,.2f}

Costes Totales:                                   - €{total_costs_sin_deuda:,.2f}
    Hard Costs:                         - €{hard_costs:,.2f}
    Soft Costs (sin Credere Fee):       - €{soft_costs_sin_fee:,.2f}
    Credere Fee:                        - €{credere_fee:,.2f}

EBITDA:                                              €{ingresos_esperados - total_costs_sin_deuda:,.2f}

Intereses Totales (Incluye Comisión):              - €{intereses_acumulados + comision_apertura:,.2f}
    Intereses:                           - €{intereses_acumulados:,.2f}
    Comisión de apertura:                - €{comision_apertura:,.2f}


EBIT:                                                €{ingresos_esperados - total_costs_sin_deuda - (intereses_acumulados + comision_apertura):,.2f}
"""

    st.code(reporte, language="plaintext")

    st.markdown("<h1 style='text-align: center;'>Análisis Cashflow</h1>", unsafe_allow_html=True)
    # Crear DataFrame del Cashflow Statement con los meses como columnas
    cashflow_statement = pd.DataFrame({
    "Tipo de Flujo": ["Inflows (€)", "Outflows (€)", "Net Cashflow (€)"],
    **{f"Mes {mes}": [inflows[mes - 1], outflows[mes - 1], net_cashflow[mes - 1]] for mes in range(1, meses_totales + 1)}
    })

    # Calcular el total de cada fila (suma de los valores por mes)
    cashflow_statement["Total (€)"] = cashflow_statement.iloc[:, 1:].sum(axis=1)

    # Mostrar la tabla en Streamlit
    st.dataframe(
        cashflow_statement.set_index("Tipo de Flujo").style.format("{:,.2f} €"),
        use_container_width=True
    )

#GRAFICOS

    st.markdown("<h1 style='text-align: center;'>Gráficos CashflowA</h1>", unsafe_allow_html=True)
    
    coste_adquisicion = [acq_cost if mes == 0 else 0 for mes in range(meses_totales)]
    hardcost_mes = [
    hard_costs / (meses_totales - 1) if 0 <= mes < meses_totales - 1 else 0
    for mes in range(meses_totales)
    ]
    softcost_mes = [
    soft_costs_con_fee / (meses_totales - 1) if 0 <= mes < meses_totales - 1 else 0
    for mes in range(meses_totales)
]
    repago_deuda = [0] * (meses_totales - 1) + [deuda_acumulada]
    repago_intereses = [0] * (meses_totales - 1) + [intereses_acumulados + comision_apertura]

    # Crear DataFrame para el gráfico
    outflows_desglosado = pd.DataFrame({
        "Mes": list(range(1, meses_totales + 1)),
        "Coste de Adquisición": coste_adquisicion,
        "Hard Costs": hardcost_mes,
        "Soft Costs (con fees)": softcost_mes,
        "Repago de Deuda": repago_deuda,
        "Repago de Intereses (Incluye Comisión Apertura)": repago_intereses
    })

    # Calcular el total por mes
    outflows_desglosado["Total Outflow (€)"] = outflows_desglosado.iloc[:, 1:].sum(axis=1)

    # Crear el gráfico de barras apiladas
    fig_out, ax = plt.subplots(figsize=(12, 6))
    bars = outflows_desglosado.set_index("Mes").iloc[:, :-1].plot(
        kind="bar",
        stacked=True,
        ax=ax,
        colormap="viridis"
    )

    # Añadir números del total por mes encima de las barras
    for i, total in enumerate(outflows_desglosado["Total Outflow (€)"]):
        ax.text(i, total + total * 0.01, f"{total:,.0f}", ha="center", fontsize=7, color="black", rotation=90)

    # Personalizar el gráfico
    ax.set_title("Outflows Mensuales Desglosados", fontsize=16)
    ax.set_xlabel("Mes", fontsize=12)
    ax.set_ylabel("Monto (€)", fontsize=12)
    ax.legend(title="Categoría", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig_out)

    #INFLOWS
    # Crear datos desglosados para inflows
    equity_mes = [equity if mes == 0 else 0 for mes in range(meses_totales)]
    deuda_disposiciones = [deuda_mes[mes] if mes < meses_totales - 1 else 0 for mes in range(meses_totales)]
    ingresos_por_ventas = [0] * (meses_totales - 1) + [ingresos_esperados]

    # Crear DataFrame para el gráfico
    inflows_desglosado = pd.DataFrame({
        "Mes": list(range(1, meses_totales + 1)),
        "Equity del Promotor": equity_mes,
        "Deuda (Disposiciones)": deuda_disposiciones,
        "Ingresos por Ventas": ingresos_por_ventas
    })

    # Calcular el total por mes
    inflows_desglosado["Total Inflow (€)"] = inflows_desglosado.iloc[:, 1:].sum(axis=1)

    # Crear el gráfico de barras apiladas
    fig_in, ax = plt.subplots(figsize=(12, 6))
    bars = inflows_desglosado.set_index("Mes").iloc[:, :-1].plot(
        kind="bar",
        stacked=True,
        ax=ax,
        colormap="viridis"
    )

    # Añadir números del total por mes encima de las barras
    for i, total in enumerate(inflows_desglosado["Total Inflow (€)"]):
        ax.text(i, total + total * 0.01, f"{total:,.0f}", ha="center", fontsize=7, color="black", rotation=90)

    # Personalizar el gráfico
    ax.set_title("Inflows Mensuales Desglosados", fontsize=16)
    ax.set_xlabel("Mes", fontsize=12)
    ax.set_ylabel("Monto (€)", fontsize=12)
    ax.legend(title="Categoría", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig_in)

    #DISPOSICIONES E INTERESES

    # Mostrar detalle de disposiciones y los intereses generados por mes
    # Crear DataFrame para el detalle de disposiciones e intereses
    detalle_disposiciones_intereses = pd.DataFrame({
        "Mes": list(range(1, meses_totales + 1)),
        "Disposiciones de Deuda (€)": deuda_mes,
        "Intereses Generados (€)": intereses_por_disposicion,
        "Comisión de Apertura (€)": [0] * (meses_totales - 1) + [comision_apertura]
    })

    # Calcular el total por mes
    detalle_disposiciones_intereses["Total (€)"] = detalle_disposiciones_intereses.iloc[:, 1:].sum(axis=1)

    # Mostrar la tabla en Streamlit
    st.markdown("<h2 style='text-align: center;'>Detalle de Disposiciones, Intereses y Comisión</h2>", unsafe_allow_html=True)
    st.table(detalle_disposiciones_intereses.style.format({
        "Disposiciones de Deuda (€)": "€{:,.2f}",
        "Intereses Generados (€)": "€{:,.2f}",
        "Comisión de Apertura (€)": "€{:,.2f}",
        "Total (€)": "€{:,.2f}"
    }))

    # Crear el gráfico de barras apiladas
    fig_dis, ax = plt.subplots(figsize=(12, 6))
    custom_colors = {
    "Disposiciones de Deuda (€)": "#1f77b4",  # Azul
    "Intereses Generados (€)": "#d62728",     # Rojo
    "Comisión de Apertura (€)": "#2ca02c"     # Verde
    }

    bars = detalle_disposiciones_intereses.set_index("Mes").iloc[:, :-1].plot(
    kind="bar",
    stacked=True,
    ax=ax,
    color=[custom_colors[col] for col in detalle_disposiciones_intereses.columns[1:-1]]
    )

    # Personalizar el gráfico
    ax.set_title("Detalle de Disposiciones, Intereses y Comisión Mensuales", fontsize=16)
    ax.set_xlabel("Mes", fontsize=12)
    ax.set_ylabel("Monto (€)", fontsize=12)
    ax.legend(title="Categoría", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig_dis)

