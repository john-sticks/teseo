# Sistema Teseo (REF — Riesgo en Encuentros Futbolísticos)

Sistema de inteligencia policial para la gestión de seguridad en el fútbol argentino. Desarrollado en Django, desplegado en Render.

---

## Dominio de negocio

Teseo centraliza la información de seguridad relacionada con el fútbol argentino para su análisis y seguimiento operativo:

- **Partidos y riesgo**: evaluación de nivel de riesgo (BAJO/MEDIO/ALTO/CRÍTICO) por encuentro y torneo
- **Incidentes**: registro georreferenciado de hechos de violencia, destrucción, invasiones de cancha, etc.
- **Ranking de conflictividad**: ranking de clubes por cantidad de incidentes y nivel de riesgo promedio
- **Inteligencia de hinchadas**: facciones, referentes, territorios geográficos controlados, antecedentes por club
- **Derecho de admisión**: personas con prohibición de ingreso a estadios (estado, fechas, motivo)
- **Planes operacionales**: PDFs de protocolos y planes de seguridad con control de versión y vencimiento
- **Monitoreo de redes sociales**: alertas por RSS/redes sobre palabras clave de riesgo (violencia, disturbios, barras bravas, etc.)

---

## Torneos cubiertos

- LPF (Liga Profesional de Fútbol)
- Ascenso (Primera Nacional)
- Copa Argentina
- Copa Sudamericana
- Copa Libertadores

---

## Stack tecnológico

| Componente | Tecnología |
|------------|-----------|
| Framework | Django 4.2.7 |
| Base de datos | SQLite3 |
| Servidor WSGI | Gunicorn |
| Static files | WhiteNoise |
| Deploy | Render (render.com) |
| Lenguaje | Python 3.11 |

---

## Aplicaciones Django

| App | Responsabilidad |
|-----|----------------|
| `dashboard` | Core: partidos, incidentes, ranking, sincronización, auditoría |
| `clubes` | Clubes, facciones de hinchadas, referentes, territorios, antecedentes |
| `derecho_admision` | Prohibiciones de ingreso a estadios |
| `operacionales` | Documentos PDF operativos (planes, protocolos) |
| `redes_monitoring` | Alertas y tendencias de redes sociales / RSS |

---

## Modelos principales

### dashboard
- **Torneo**: nombre, activo, fechas
- **Encuentro**: torneo, fecha/hora, clubes, estadio, nivel_riesgo, relato_hecho, external_id, raw_data
- **Incidente**: encuentro, tipo, descripción, latitud/longitud, fecha, external_id
- **RankingConflictividad**: club, torneo, cantidad_conflictos, nivel_riesgo_promedio
- **Club** (sync): external_id, nombre, escudo_url, estadio, barras, torneo
- **DerechoAdmision** (sync): external_id, club, nombre/apellido, motivo, estado, fechas
- **OperacionalDoc** (sync): file_id, nombre, url, spreadsheet_id, torneo
- **AuditoriaAcceso**: usuario, tipo_accion, ip, user_agent, url, fecha, exitoso, detalles (JSON)
- **SesionUsuario**: usuario, session_key, ip, última actividad, activa
- **PerfilUsuario**: usuario (1:1), rol (ADMINISTRADOR/VISITA), permisos granulares

### clubes
- **Club**: nombre, estadio, ciudad, provincia, colores, presidente, escudo (ImageField)
- **FaccionHinchas**: club, nombre, tipo (BARRA_BRAVA/HINCHADA/GRUPO/BANDA/OTRO), cantidad_estimada
- **ReferenteHinchas**: faccion, nombre, apodo, teléfono, activo
- **TerritorioHinchas**: faccion, nombre, dirección, coordenadas lat/lng
- **AntecedenteClub**: club, tipo, descripción, fecha, sanción, monto

### derecho_admision
- **DerechoAdmision**: club, motivo, fecha_imposicion, fecha_vencimiento, estado (VIGENTE/LEVANTADO/SUSPENDIDO)

### operacionales
- **OperacionalVigente**: nombre, tipo, archivo_pdf, fecha_vigencia, versión, activo

### redes_monitoring
- **AlertaRedes**: título, url, fuente, nivel_riesgo, keywords (JSON), clubes_mencionados (JSON), procesado
- **TendenciasKeyword**: keyword, frecuencia, fecha

---

## Fuentes de datos externas

### Google Sheets (sincronización CSV)
Los datos operativos se gestionan desde planillas de Google Sheets y se sincronizan vía exportación CSV pública.

Estructura de IDs por torneo en `settings.py`:
```python
GOOGLE_SHEETS_IDS = {
    'LPF': {
        'encuentros': '1-lYFhNHfLT7qnj6SxKqhUQ-fHYjdDAAT',
        'ranking': '1d1I_ljiyIP6UQ84dNxldg19yhUQ3iIFN',
        # ...
    },
    'ASCENSO': { ... },
    'COPA_ARGENTINA': { ... },
    # ...
}
```

Credenciales para escritura: `credentials/just-coda-473000-f4-c4748e7930d6.json` (gspread + oauth2client).

### RSS / Redes Sociales
- Feed RSS configurado en `settings.RSS_FEED_URL` (`rss.app`)
- Keywords monitoreados: violencia, pelea, hinchada, barra brava, incidente, disturbio, policía, estadio, clásico, etc.
- Extrae: título, descripción, URL, fecha, fuente (Twitter/Facebook/Instagram/YouTube/TikTok/Medio), nivel de riesgo calculado

---

## Autenticación y roles

Sistema propio Django (no integrado con Cerberus ni con el resto de la plataforma).

| Rol | Acceso |
|-----|--------|
| ADMINISTRADOR | Acceso completo: puede ver relato_hecho, editar datos, sincronizar, exportar |
| VISITA | Solo lectura, sin acceso a narrativas de incidentes |

Auditoría completa de todas las acciones con IP, user agent, timestamp y resultado.

---

## Rutas principales

```
/                          Bienvenida
/dashboard/                Dashboard principal
/encuentro/<id>/           Detalle de partido
/mapa/                     Mapa de incidentes (georreferenciado)
/sincronizar/              Sincronizar con Google Sheets
/exportar/                 Exportar datos
/clubes/                   Listado de clubes
/clubes/club/<id>/         Detalle de club (facciones, territorios, antecedentes)
/clubes/mapa-territorios/  Mapa geográfico de territorios de hinchadas
/derecho_admision/         Listado de prohibiciones
/operacionales/            Documentos operativos con control de vencimiento
/redes_monitoring/         Alertas de redes sociales y tendencias
/gestion-usuarios/         CRUD de usuarios
/auditoria/                Log de auditoría
/admin/                    Django Admin
```

---

## Despliegue (Render)

```yaml
# render.yaml
services:
  - type: web
    name: ref-system
    env: python
    buildCommand: "./build.sh"
    startCommand: "./start.sh"
    envVars:
      - PYTHON_VERSION: 3.11.0
      - DEBUG: False
      - ALLOWED_HOSTS: "ref-ya68.onrender.com,127.0.0.1,localhost"
      - DATABASE_URL: "sqlite:///db.sqlite3"
```

**build.sh**: instala dependencias → migraciones → crea usuario admin → collectstatic  
**start.sh**: verifica DB → setup_production si no existe → inicia Gunicorn en `$PORT`

Usuario admin por defecto en producción: `admin / RefAdmin2025!` (cambiar después del primer deploy).

---

## Variables de entorno relevantes

```bash
SECRET_KEY=<generar con python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=ref-ya68.onrender.com,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3   # o PostgreSQL en producción escalada
```

---

## Relación con el resto de la plataforma

Teseo es **independiente** del resto del sistema distribuido (Argo, Cerberus, Pegasus, Prometheus, etc.):

- No comparte base de datos (usa SQLite propio vs. MySQL compartido del resto)
- No usa Cerberus para autenticación (tiene su propio Django auth)
- No está en el servidor remoto vía Tailscale (corre en Render)
- Fue incorporado al repositorio como sistema separado

**Posibles puntos de integración futuros:**
- Migrar auth a Cerberus (JWT) para SSO con el resto de la plataforma
- Migrar DB a MySQL compartido del servidor remoto
- Mover despliegue al servidor remoto vía Docker + Tailscale
- Conectar incidentes de Teseo con datos de delitos de Pegasus/Prometheus

---

## Comandos de gestión Django

```bash
python manage.py setup_production      # Configuración inicial de producción
python manage.py sync_google_sheets    # Sincronización manual con Google Sheets
python manage.py migrate               # Aplicar migraciones
python manage.py collectstatic         # Recopilar archivos estáticos
```
