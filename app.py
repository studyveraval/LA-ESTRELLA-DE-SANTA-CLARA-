import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Cotizador - La Estrella de Santa Clara",
    page_icon="🏢",
    layout="centered",
)


# Cargar base de datos desde el Excel subido
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("BASEDATA2.0.xlsx")
    except Exception as e:
        st.error(
            "❌ No se encontró el archivo 'BASEDATA2.0.xlsx'. Asegúrate de haberlo subido al repositorio."
        )
        return None

    # Normalizar nombres de columnas
    columnas_map = {col: str(col).strip().lower() for col in df.columns}
    df = df.rename(columns=columnas_map)

    # Identificar columnas automáticamente
    col_mz = next((c for c in df.columns if "mz" in c or "manzana" in c), None)
    col_num = next(
        (c for c in df.columns if "num" in c or "numero" in c or "lote" in c),
        None,
    )
    col_ubi = next(
        (c for c in df.columns if "ubi" in c or "ubicacion" in c), None
    )
    col_met = next(
        (c for c in df.columns if "met" in c or "m2" in c or "area" in c), None
    )

    if not all([col_mz, col_num, col_ubi, col_met]):
        st.error(
            "⚠️ El archivo Excel debe tener las columnas: Mz, Numero, Ubicacion, Metraje."
        )
        return None

    # Estandarizar valores para búsquedas
    df["mz_search"] = df[col_mz].astype(str).str.strip().str.upper()
    df["num_search"] = df[col_num].astype(str).str.strip().str.upper()
    df["ubicacion_clean"] = df[col_ubi].astype(str).str.strip()
    df["metraje_clean"] = pd.to_numeric(df[col_met], errors="coerce").fillna(0)

    return df


df_lotes = cargar_datos()

# Interfaz principal
st.title("🔎 Cotizador - La Estrella de Santa Clara")
st.write(
    "Ingresa los datos del cliente, lote y el tipo de cambio del día para generar la cotización."
)

# Formulario de entrada
col_cliente, col_mz, col_num, col_tc = st.columns([2, 1, 1, 1])
with col_cliente:
    nombre_cliente = st.text_input(
        "Nombre cliente (Opcional):", placeholder="Ej. Juan Pérez"
    ).strip()
with col_mz:
    mz_input = (
        st.text_input("Manzana (Mz):", placeholder="Ej. A").strip().upper()
    )
with col_num:
    num_input = (
        st.text_input("Número / Lote:", placeholder="Ej. 12").strip().upper()
    )
with col_tc:
    tipo_cambio = st.number_input(
        "Tipo Cambio (S/):", value=3.75, step=0.01, format="%.2f"
    )

if st.button("🔍 Buscar y Cotizar", type="primary", use_container_width=True):
    if not mz_input or not num_input:
        st.warning("⚠️ Por favor ingresa la Manzana y el Número de lote.")
    elif df_lotes is None:
        st.error("No se pudo consultar el archivo Excel.")
    else:
        # Búsqueda en el DataFrame
        resultado = df_lotes[
            (df_lotes["mz_search"] == mz_input)
            & (df_lotes["num_search"] == num_input)
        ]

        if resultado.empty:
            st.error(
                f"❌ No se encontró la Mz. {mz_input} - Lote {num_input} en la base de datos."
            )
        else:
            lote = resultado.iloc[0]
            ubicacion = lote["ubicacion_clean"]
            metraje = float(lote["metraje_clean"])

            # Criterio de precio por m²
            ubi_lower = ubicacion.lower()
            if "esquina" in ubi_lower or "avenida" in ubi_lower:
                precio_m2 = 1000
            elif "pasadizo" in ubi_lower or "interior" in ubi_lower:
                precio_m2 = 900
            else:
                precio_m2 = 900

            # CÁLCULOS EN DÓLARES (USD)
            precio_lista_usd = metraje * precio_m2
            precio_10_desc_usd = precio_lista_usd * 0.90
            precio_20_desc_usd = precio_lista_usd * 0.80

            precio_5_desc_usd = precio_lista_usd * 0.95
            inicial_40_usd = precio_5_desc_usd * 0.40
            saldo_financiar_usd = precio_5_desc_usd - inicial_40_usd
            cuota_24_usd = saldo_financiar_usd / 24

            # CÁLCULOS EN SOLES (PEN)
            tc = tipo_cambio
            precio_lista_pen = precio_lista_usd * tc
            precio_10_desc_pen = precio_10_desc_usd * tc
            precio_20_desc_pen = precio_20_desc_usd * tc

            precio_5_desc_pen = precio_5_desc_usd * tc
            inicial_40_pen = inicial_40_usd * tc
            saldo_financiar_pen = saldo_financiar_usd * tc
            cuota_24_pen = cuota_24_usd * tc

            # RESUMEN DEL LOTE
            st.markdown("---")
            st.subheader(f"📍 Manzana {mz_input} — Lote {num_input}")

            m1, m2, m3 = st.columns(3)
            m1.metric("Ubicación", ubicacion)
            m2.metric("Precio / m²", f"${precio_m2:,.2f} USD")
            m3.metric("Área Total", f"{metraje:,.2f} m²")

            # TABLA DE PRECIOS AL CONTADO
            st.markdown("### 💵 Precios al Contado / Lista")
            c1, c2, c3 = st.columns(3)
            c1.metric(
                "Precio Lista",
                f"${precio_lista_usd:,.2f} USD",
                f"S/ {precio_lista_pen:,.2f}",
            )
            c2.metric(
                "Con 10% Desc.",
                f"${precio_10_desc_usd:,.2f} USD",
                f"S/ {precio_10_desc_pen:,.2f}",
            )
            c3.metric(
                "Con 20% Desc.",
                f"${precio_20_desc_usd:,.2f} USD",
                f"S/ {precio_20_desc_pen:,.2f}",
            )

            # PLAN FRACCIONADO
            st.markdown("### 📅 Plan Fraccionado (5% Desc. + 24 Cuotas)")
            st.info(
                f"""
            * **Precio Total (5% Desc.):** ${precio_5_desc_usd:,.2f} USD / **S/ {precio_5_desc_pen:,.2f}**  
            * **Cuota Inicial (40%):** ${inicial_40_usd:,.2f} USD / **S/ {inicial_40_pen:,.2f}**  
            * **Saldo a Financiar:** ${saldo_financiar_usd:,.2f} USD / **S/ {saldo_financiar_pen:,.2f}**  

            #### 💳 **24 Cuotas Mensuales de: ${cuota_24_usd:,.2f} USD  |  S/ {cuota_24_pen:,.2f}**
            *(Calculado a un T.C. referencial de S/ {tc:.2f})*
            """
            )

            # CONSTRUCCIÓN DEL MENSAJE PARA WHATSAPP
            saludo = (
                f"Estimado(a) *{nombre_cliente}*,"
                if nombre_cliente
                else "Estimado(a) cliente,"
            )

            mensaje_wa = f"""{saludo}
Le envío la cotización detallada para el lote de su interés en *Proyectó La Estrella de Santa Clara*:

📌 *DATOS DEL LOTE:*
• *Ubicación:* Manzana {mz_input} - Lote {num_input} ({ubicacion})
• *Área Total:* {metraje:,.2f} m²
• *Precio por m²:* ${precio_m2:,.2f} USD

💵 *OPCIONES AL CONTADO:*
• *Precio Lista:* ${precio_lista_usd:,.2f} USD (aprox. S/ {precio_lista_pen:,.2f})
• *Con 10% Descuento:* ${precio_10_desc_usd:,.2f} USD (aprox. S/ {precio_10_desc_pen:,.2f})
• *Con 20% Descuento (Promocional):* ${precio_20_desc_usd:,.2f} USD (aprox. S/ {precio_20_desc_pen:,.2f})

📅 *OPCIÓN FINANCIADA (5% Desc.):*
• *Precio Final:* ${precio_5_desc_usd:,.2f} USD (S/ {precio_5_desc_pen:,.2f})
• *Cuota Inicial (40%):* ${inicial_40_usd:,.2f} USD (S/ {inicial_40_pen:,.2f})
• *Saldo a financiar:* ${saldo_financiar_usd:,.2f} USD (S/ {saldo_financiar_pen:,.2f})
• *Financiamiento:* 24 cuotas mensuales de *${cuota_24_usd:,.2f} USD* (aprox. *S/ {cuota_24_pen:,.2f}*)

*(T.C. referencial: S/ {tc:.2f})*

Quedo a su entera disposición si desea coordinar una visita a la parcela o resolver cualquier consulta. ¡Aproveche esta gran oportunidad! 🏡✨"""

            st.markdown("---")
            st.markdown("### 📲 Mensaje listo para enviar por WhatsApp")
            st.write("Copia el texto del recuadro para enviarlo por WhatsApp:")
            st.code(mensaje_wa, language="markdown")
