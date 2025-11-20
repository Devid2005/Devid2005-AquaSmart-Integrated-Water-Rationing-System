import pandas as pd
import numpy as np
import datetime


def nivel_embalse_dia():
    return np.random.uniform(0.3, 0.7)

def simular_consumo():
    np.random.seed(42)
    dias_simulacion = 10

    def estacionalidad(mes):
        if mes in [1, 2, 8]:
            return 1.15
        elif mes in [4, 10, 11]:
            return 0.9
        else:
            return 1.0

    def actividad_reducida():
        return np.random.rand() < 0.1

    def consumo_base(tipo_sector, personas):
        if tipo_sector == 'residencial':
            return np.random.randint(100, 300) * personas
        elif tipo_sector == 'comercial':
            return np.random.randint(20000, 100000)
        elif tipo_sector == 'industrial':
            return np.random.randint(100000, 800000)
        return 0

    zonas_mixtas = {
        0: ['residencial', 'industrial'],
        1: ['residencial', 'comercial', 'industrial']
    }

    data_unidades = []

    for zona_id, sectores in zonas_mixtas.items():
        for tipo_sector in sectores:
            unidades_por_grupo = np.random.randint(3, 10)
            for unidad in range(unidades_por_grupo):
                personas = np.random.randint(10_000,100_000) if tipo_sector == 'residencial' else None
                unidades_prod = np.random.randint(1, 5) if tipo_sector == 'industrial' else None
                for dia in range(dias_simulacion):
                    unidad_id = f"zona{zona_id}{tipo_sector}{dia}_{unidad}"
                    fecha = datetime.date(2025, 1, 1) + datetime.timedelta(days=dia)
                    mes = fecha.month
                    estacional = estacionalidad(mes)
                    consumo = consumo_base(tipo_sector, personas)
                    consumo *= estacional
                    reduccion = actividad_reducida()
                    if reduccion:
                        consumo *= np.random.uniform(0.6, 0.8)
                    if tipo_sector == 'residencial':
                        consumo = max(consumo, 50 * personas)

                    data_unidades.append({
                        'unidad_id': unidad_id,
                        'fecha': fecha,
                        'unidad': unidad,
                        'zona_id': zona_id,
                        'tipo_sector': tipo_sector,
                        'habitantes': personas,
                        'unidades_productivas': unidades_prod,
                        'actividad_reducida': reduccion,
                        'estacionalidad': estacional,
                        'consumo_litros_dia': consumo
                    })

    df_unidades = pd.DataFrame(data_unidades)

    residencial = df_unidades[df_unidades['tipo_sector'] == 'residencial']
    industrial = df_unidades[df_unidades['tipo_sector'] == 'industrial']

    total_consumo_residencial = residencial['consumo_litros_dia'].sum()
    total_habitantes = residencial['habitantes'].sum()
    total_consumo_industrial = industrial['consumo_litros_dia'].sum()
    total_unidades_industriales = industrial['unidades_productivas'].sum()

    if total_habitantes > 0 and total_unidades_industriales > 0:
        promedio_residencial = total_consumo_residencial / total_habitantes
        promedio_industrial = total_consumo_industrial / total_unidades_industriales
        cumple_restriccion_9 = promedio_residencial <= promedio_industrial
    else:
        cumple_restriccion_9 = False

    if not cumple_restriccion_9:
        return None, False, False

    return df_unidades, True, True


# Intentar generar simulación válida
for intento in range(10):
    resultado, r9, r10 = simular_consumo()
    if r9 and r10:
        df_simulacion_final = resultado
        print(f"Simulación válida generada en el intento {intento+1}.")
        break
else:
    raise Exception("No se pudo generar una simulación válida.")
# Agregar métricas
df_grupo = df_simulacion_final.groupby(['fecha', 'zona_id', 'tipo_sector']).agg({
    'consumo_litros_dia': 'sum',
    'habitantes': 'sum',
    'unidades_productivas': 'sum'
}).reset_index()

df_grupo = df_grupo.rename(columns={'consumo_litros_dia': 'consumo_total_litros'})

df_grupo['promedio_por_persona'] = df_grupo.apply(
    lambda row: row['consumo_total_litros'] / row['habitantes']
    if row['tipo_sector'] == 'residencial' and row['habitantes'] > 0 else None,
    axis=1
)

df_grupo['promedio_por_unidad_industrial'] = df_grupo.apply(
    lambda row: row['consumo_total_litros'] / row['unidades_productivas']
    if row['tipo_sector'] == 'industrial' and row['unidades_productivas'] > 0 else None,
    axis=1
)

df_simulacion_completa = pd.merge(
    df_simulacion_final,
    df_grupo,
    on=['fecha', 'zona_id', 'tipo_sector'],
    how='left'
)

# Función para exportar parámetros
def guardar_parametros_txt(df, archivo='parametros_simulacion.txt'):
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    if df['fecha'].isnull().any():
        raise ValueError("Valores inválidos en 'fecha' tras conversión.")

    habit_col = (
        'habitantes_y' if 'habitantes_y' in df.columns else
        'habitantes_x' if 'habitantes_x' in df.columns else
        'habitantes' if 'habitantes' in df.columns else
        None
    )
    if habit_col is None:
        raise ValueError("No se encontró ninguna versión válida de 'habitantes'.")

    zonas = sorted(df['zona_id'].unique())
    dias = sorted(df['fecha'].dt.day.unique())
    sectores = sorted(df['tipo_sector'].unique())

    sector_idx = {s: i for i, s in enumerate(sectores)}
    zona_idx = {z: i for i, z in enumerate(zonas)}

    c = [[[0.0 for _ in sectores] for _ in dias] for _ in zonas]
    r = [0.0 for _ in dias]
    h = [0 for _ in zonas]
    for _, row in df_grupo.iterrows():
        z = zona_idx[row['zona_id']]
        d = row['fecha'].day - 1
        t = sector_idx[row['tipo_sector']]
        c[z][d][t] = row['consumo_total_litros']
        r[d] = nivel_embalse_dia()* 1_000_000_000

    df_hab = df_grupo.groupby('zona_id')['habitantes'].max().reset_index()

    for _, row in df_hab.iterrows():
        z = zona_idx[row['zona_id']]
        h[z] = row['habitantes']

    p = 1_300_000_000
    n_0 = 0.40
    e = 0.85
    m = 300_000_000_000

    with open(archivo, 'w') as f:
        f.write("// Parámetros simulados para modelo de racionamiento de agua\n\n")

        f.write("c = [\n")
        for z in c:
            f.write("  [\n")
            for d in z:
                f.write("    [" + ", ".join(f"{val:.2f}" for val in d) + "],\n")
            f.write("  ],\n")
        f.write("];\n\n")

        f.write(f"p = {p};\n")
        f.write(f"n_0 = {n_0 * m};\n")
        f.write(f"e = {e};\n")
        f.write(f"m = {m};\n\n")

        f.write("r = [" + ", ".join(f"{val:.2f}" for val in r) + "];\n")
        f.write("h = [" + ", ".join(f"{val:.2f}" for val in h) + "];\n")

    print(f"Archivo exportado correctamente a: {archivo}")

# Ejecutar exportación
guardar_parametros_txt(df_simulacion_completa, 'path/parametros_simulados.txt')

