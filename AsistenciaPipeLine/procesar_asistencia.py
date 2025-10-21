import pandas as pd
from pathlib import Path
from datetime import datetime, time

# ===== Rutas =====
IN_PATH  = r'C:\Users\MarioSoler\OneDrive - Relay Human Cloud\ML\AsistenciaPipeLine\Entrada\Asistencia_Deducciones_PEGAR.xlsx'
OUT_DIR  = Path(r'C:\Users\MarioSoler\OneDrive - Relay Human Cloud\ML\AsistenciaPipeLine\Salida')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ===== Columnas =====
COL_ID     = 'Identidad'
COL_FICHA  = 'Num. Ficha'
COL_NOMBRE = 'Nombre Empleado'
COL_DEPTO  = 'Departamento'
COL_GER    = 'Gerecia'          
COL_TERM   = 'Terminal'
COL_FECHA  = 'Fecha'
COL_HORA   = 'Hora de Marcaje'

KEEP_COLS = [COL_ID, COL_FICHA, COL_NOMBRE, COL_DEPTO, COL_GER, COL_TERM, COL_FECHA]

# ===== Config de jornada programada =====
ENTRADA_PROG = time(7, 30)
SALIDA_PROG  = time(16, 30)

# ===== Cargar =====
df = pd.read_excel(IN_PATH)

# Validar columnas
faltantes = [c for c in [*KEEP_COLS, COL_HORA] if c not in df.columns]
if faltantes:
    raise ValueError(f'Faltan columnas en el Excel: {faltantes}')

# ===== Parsear fecha y hora =====
df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors='coerce').dt.date

def parse_time_series(s: pd.Series) -> pd.Series:
    fmts = ['%H:%M:%S', '%H:%M', '%I:%M:%S %p', '%I:%M %p', '%H%M%S', '%H%M']
    def one(v):
        if pd.isna(v):
            return None
        v = str(v).strip()
        for f in fmts:
            try:
                return datetime.strptime(v, f).time()
            except Exception:
                pass
        t = pd.to_datetime(v, errors='coerce')
        return None if pd.isna(t) else t.time()
    return s.map(one)

df[COL_HORA] = parse_time_series(df[COL_HORA])

# ===== Calcular entrada y salida reales =====
df['__dt'] = pd.to_datetime(df[COL_FECHA].astype(str) + ' ' + df[COL_HORA].astype(str), errors='coerce')

g = df.groupby([COL_ID, COL_FECHA])['__dt']
resumen = pd.DataFrame({
    'hora_entrada': g.min().dt.time,
    'hora_salida' : g.max().dt.time
}).reset_index()

# ===== Unir =====
df_final = df.merge(resumen, on=[COL_ID, COL_FECHA], how='left')
df_final = df_final[KEEP_COLS + ['hora_entrada', 'hora_salida']]

# ===== Añadir programadas =====
df_final['hora_entrada_prog'] = ENTRADA_PROG
df_final['hora_salida_prog']  = SALIDA_PROG

# ===== Métricas de desfase =====
def _mins_diff(t1: time, t2: time) -> int | None:
    if pd.isna(t1) or pd.isna(t2):
        return None
    d1 = datetime.combine(datetime.today(), t1)
    d2 = datetime.combine(datetime.today(), t2)
    return int((d1 - d2).total_seconds() // 60)

df_final['mins_tarde'] = df_final.apply(
    lambda r: max(0, _mins_diff(r['hora_entrada'], r['hora_entrada_prog'])) 
              if pd.notna(r['hora_entrada']) else None, axis=1)

df_final['mins_temprano'] = df_final.apply(
    lambda r: max(0, _mins_diff(r['hora_salida_prog'], r['hora_salida'])) 
              if pd.notna(r['hora_salida']) else None, axis=1)

def _neg_outside(row):
    if pd.isna(row['mins_tarde']) and pd.isna(row['mins_temprano']):
        return None
    t = (row['mins_tarde'] or 0) + (row['mins_temprano'] or 0)
    return -t

df_final['minutos_fuera_prog'] = df_final.apply(_neg_outside, axis=1)

def _estado(row):
    tarde = (row['mins_tarde'] or 0) > 0 if pd.notna(row['mins_tarde']) else False
    temprano = (row['mins_temprano'] or 0) > 0 if pd.notna(row['mins_temprano']) else False
    if pd.isna(row['hora_entrada']) and pd.isna(row['hora_salida']):
        return 'Sin marcajes'
    if tarde and temprano:
        return 'Llegó tarde y se fue temprano'
    if tarde:
        return 'Llegó tarde'
    if temprano:
        return 'Se fue temprano'
    return 'OK'

df_final['estado_entrada_salida'] = df_final.apply(_estado, axis=1)

# ===== Formatear todas las horas como '%I:%M %p' =====
def fmt(t):
    return t.strftime('%I:%M %p') if pd.notna(t) else None

for col in ['hora_entrada', 'hora_salida', 'hora_entrada_prog', 'hora_salida_prog']:
    df_final[col] = df_final[col].map(fmt)

# ===== Eliminar duplicados =====
df_final = df_final.drop_duplicates(keep='first')

# ===== Guardar =====
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
csv_path  = OUT_DIR / f'Asistencia_limpia_{ts}.csv'
xlsx_path = OUT_DIR / f'Asistencia_limpia_{ts}.xlsx'

df_final.to_csv(csv_path, index=False, encoding='utf-8-sig')
df_final.to_excel(xlsx_path, index=False, engine='openpyxl')

print("✅ Archivo procesado correctamente.")
print(f"📄 CSV:  {csv_path}")
print(f"📊 Excel: {xlsx_path}")
