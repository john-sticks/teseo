# 🎨 SISTEMA DE CLASES CSS REF

## 📋 **GUÍA DE USO DE CLASES REUTILIZABLES**

Este documento explica cómo usar todas las clases CSS del sistema REF. **NO modifiques la estructura HTML**, solo aplica las clases que necesites.

---

## 🚀 **CÓMO USAR**

### 1. **Incluir el archivo CSS**
```html
<link rel="stylesheet" href="{% static 'css/components.css' %}">
```

### 2. **Aplicar clases en el HTML**
```html
<!-- Antes -->
<div class="card">
    <div class="card-header">Título</div>
    <div class="card-body">Contenido</div>
</div>

<!-- Después -->
<div class="ref-card">
    <div class="ref-card-header">Título</div>
    <div class="ref-card-body">Contenido</div>
</div>
```

---

## 🧩 **COMPONENTES DISPONIBLES**

### 🔐 **LOGIN**
```html
<body class="ref-login-container">
    <div class="ref-login-card ref-fade-in">
        <div class="ref-login-logo">
            <i class="fas fa-shield-alt"></i>
        </div>
        <h2 class="ref-login-title">Título</h2>
        <input class="ref-login-input" placeholder="Usuario">
        <button class="ref-login-btn">Ingresar</button>
        <div class="ref-login-footer">Footer</div>
    </div>
</body>
```

### 🧭 **NAVEGACIÓN**
```html
<!-- Top Header -->
<div class="ref-top-header">
    <span class="ref-system-title">Sistema REF</span>
    <button class="ref-hamburger-menu">☰</button>
</div>

<!-- Sidebar -->
<div class="ref-sidebar">
    <div class="ref-sidebar-header">
        <div class="ref-logo-container">
            <span class="ref-logo-r">R</span>
            <span class="ref-logo-text">REF</span>
        </div>
    </div>
    <a href="#" class="ref-nav-item">
        <i class="fas fa-home"></i>
        <span>Dashboard</span>
    </a>
</div>

<!-- Main Navbar -->
<div class="ref-main-navbar">
    <a href="#" class="ref-nav-link active">
        <i class="fas fa-home"></i> Dashboard
    </a>
</div>

<!-- Tournament Filters -->
<div class="ref-tournament-filters">
    <a href="#" class="ref-tournament-btn active">LPF</a>
    <a href="#" class="ref-tournament-btn">ASCENSO</a>
</div>
```

### 🔘 **BOTONES**
```html
<!-- Botones básicos -->
<button class="ref-btn ref-btn-primary">Primario</button>
<button class="ref-btn ref-btn-secondary">Secundario</button>
<button class="ref-btn ref-btn-success">Éxito</button>
<button class="ref-btn ref-btn-warning">Advertencia</button>
<button class="ref-btn ref-btn-danger">Peligro</button>
<button class="ref-btn ref-btn-info">Información</button>

<!-- Tamaños -->
<button class="ref-btn ref-btn-primary ref-btn-sm">Pequeño</button>
<button class="ref-btn ref-btn-primary ref-btn-lg">Grande</button>
<button class="ref-btn ref-btn-primary ref-btn-xl">Extra Grande</button>

<!-- Botones de acción específicos -->
<button class="ref-btn ref-btn-export">
    <i class="fas fa-download"></i> Exportar
</button>
<button class="ref-btn ref-btn-sync">
    <i class="fas fa-sync"></i> Sincronizar
</button>
<button class="ref-btn ref-btn-edit">
    <i class="fas fa-edit"></i> Editar
</button>
<button class="ref-btn ref-btn-delete">
    <i class="fas fa-trash"></i> Eliminar
</button>
```

### 🏷️ **ETIQUETAS Y BADGES**
```html
<!-- Badges básicos -->
<span class="ref-badge ref-badge-primary">Primario</span>
<span class="ref-badge ref-badge-success">Éxito</span>
<span class="ref-badge ref-badge-warning">Advertencia</span>
<span class="ref-badge ref-badge-danger">Peligro</span>

<!-- Badges de riesgo específicos -->
<span class="ref-badge ref-badge-riesgo-bajo">BAJO</span>
<span class="ref-badge ref-badge-riesgo-medio">MEDIO</span>
<span class="ref-badge ref-badge-riesgo-alto">ALTO</span>
<span class="ref-badge ref-badge-riesgo-critico">CRÍTICO</span>
```

### 📦 **CONTENEDORES Y CARDS**
```html
<!-- Contenedores -->
<div class="ref-container">Contenedor fijo</div>
<div class="ref-container-fluid">Contenedor fluido</div>

<!-- Cards básicas -->
<div class="ref-card">
    <div class="ref-card-header">Título</div>
    <div class="ref-card-body">Contenido</div>
    <div class="ref-card-footer">Footer</div>
</div>

<!-- Cards especiales -->
<div class="ref-card ref-card-stat">Estadística</div>
<div class="ref-card ref-card-alert">Alerta</div>
<div class="ref-card ref-card-danger">Peligro</div>
<div class="ref-card ref-card-success">Éxito</div>
```

### 📊 **TABLAS**
```html
<div class="ref-table-responsive">
    <table class="ref-table ref-table-striped">
        <thead>
            <tr>
                <th>Columna 1</th>
                <th>Columna 2</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Dato 1</td>
                <td>Dato 2</td>
            </tr>
        </tbody>
    </table>
</div>
```

### 📝 **FORMULARIOS**
```html
<form>
    <div class="ref-form-group">
        <label class="ref-form-label">Etiqueta</label>
        <input type="text" class="ref-form-control" placeholder="Texto">
        <select class="ref-form-select">
            <option>Opción 1</option>
        </select>
    </div>
</form>
```

### 🚨 **ALERTAS**
```html
<div class="ref-alert ref-alert-primary">
    <i class="fas fa-info-circle"></i>
    Mensaje primario
</div>

<div class="ref-alert ref-alert-success">
    <i class="fas fa-check-circle"></i>
    Mensaje de éxito
</div>

<div class="ref-alert ref-alert-warning">
    <i class="fas fa-exclamation-triangle"></i>
    Mensaje de advertencia
</div>

<div class="ref-alert ref-alert-danger">
    <i class="fas fa-times-circle"></i>
    Mensaje de error
</div>
```

---

## 🎯 **UTILIDADES Y HELPERS**

### 📏 **ESPACIADO**
```html
<!-- Márgenes -->
<div class="ref-m-0">Sin margen</div>
<div class="ref-m-1">Margen pequeño</div>
<div class="ref-m-2">Margen mediano</div>
<div class="ref-m-3">Margen grande</div>
<div class="ref-m-4">Margen extra grande</div>
<div class="ref-m-5">Margen máximo</div>

<!-- Padding -->
<div class="ref-p-0">Sin padding</div>
<div class="ref-p-1">Padding pequeño</div>
<div class="ref-p-2">Padding mediano</div>
<div class="ref-p-3">Padding grande</div>
<div class="ref-p-4">Padding extra grande</div>
<div class="ref-p-5">Padding máximo</div>
```

### 🎨 **COLORES DE TEXTO**
```html
<p class="ref-text-primary">Texto primario</p>
<p class="ref-text-secondary">Texto secundario</p>
<p class="ref-text-success">Texto éxito</p>
<p class="ref-text-warning">Texto advertencia</p>
<p class="ref-text-danger">Texto peligro</p>
<p class="ref-text-info">Texto información</p>
<p class="ref-text-dark">Texto oscuro</p>
<p class="ref-text-light">Texto claro</p>
```

### 🎨 **COLORES DE FONDO**
```html
<div class="ref-bg-primary">Fondo primario</div>
<div class="ref-bg-secondary">Fondo secundario</div>
<div class="ref-bg-success">Fondo éxito</div>
<div class="ref-bg-warning">Fondo advertencia</div>
<div class="ref-bg-danger">Fondo peligro</div>
<div class="ref-bg-info">Fondo información</div>
<div class="ref-bg-light">Fondo claro</div>
<div class="ref-bg-dark">Fondo oscuro</div>
<div class="ref-bg-white">Fondo blanco</div>
```

### 📐 **ALINEACIÓN DE TEXTO**
```html
<p class="ref-text-center">Centrado</p>
<p class="ref-text-left">Izquierda</p>
<p class="ref-text-right">Derecha</p>
<p class="ref-text-bold">Negrita</p>
<p class="ref-text-normal">Normal</p>
```

### 📱 **DISPLAY Y FLEXBOX**
```html
<!-- Display -->
<div class="ref-d-none">Oculto</div>
<div class="ref-d-block">Bloque</div>
<div class="ref-d-inline">En línea</div>
<div class="ref-d-flex">Flex</div>

<!-- Flexbox -->
<div class="ref-d-flex ref-flex-row ref-justify-content-center ref-align-items-center">
    Contenido centrado
</div>
```

### 🔲 **BORDES**
```html
<div class="ref-border">Con borde</div>
<div class="ref-border-0">Sin borde</div>
<div class="ref-border-top">Borde superior</div>
<div class="ref-border-primary">Borde primario</div>
<div class="ref-border-success">Borde éxito</div>
```

### 🌟 **SOMBRAS**
```html
<div class="ref-shadow-sm">Sombra pequeña</div>
<div class="ref-shadow-md">Sombra mediana</div>
<div class="ref-shadow-lg">Sombra grande</div>
<div class="ref-shadow-none">Sin sombra</div>
```

### 🔄 **BORDES REDONDEADOS**
```html
<div class="ref-rounded-sm">Redondeado pequeño</div>
<div class="ref-rounded-md">Redondeado mediano</div>
<div class="ref-rounded-lg">Redondeado grande</div>
<div class="ref-rounded-xl">Redondeado extra grande</div>
<div class="ref-rounded-circle">Círculo</div>
```

---

## 🎬 **ANIMACIONES**

```html
<div class="ref-fade-in">Aparece con fade</div>
<div class="ref-slide-in">Aparece deslizando</div>
```

---

## 🎯 **ESTADOS ESPECIALES**

```html
<div class="ref-loading">Cargando...</div>
<div class="ref-disabled">Deshabilitado</div>
<div class="ref-active">Activo</div>
<div class="ref-selected">Seleccionado</div>
```

---

## 📱 **RESPONSIVE**

Las clases son automáticamente responsive. En pantallas pequeñas:
- Las tablas se vuelven scrollables
- Los botones se ajustan de tamaño
- Los espaciados se reducen
- El sidebar se adapta

---

## 🎨 **PALETA DE COLORES**

```css
--ref-primary: #359CB2        /* Azul principal (botones y acentos) */
--ref-secondary: #6c757d      /* Gris secundario */
--ref-success: #28a745        /* Verde éxito */
--ref-warning: #ffc107        /* Amarillo advertencia */
--ref-danger: #dc3545         /* Rojo peligro */
--ref-info: #17a2b8           /* Azul información */
--ref-light: #f8f9fa          /* Fondo claro */
--ref-dark: #0F1D29           /* Fondo oscuro principal */
--ref-bg-main: #0F1D29        /* Fondo principal oscuro */
--ref-bg-container: #064669   /* Fondo del contenedor */
--ref-btn-color: #359CB2      /* Color del botón */
```

## 🔤 **TIPOGRAFÍA**

El sistema usa **Inter** (similar a Proxima Nova) como tipografía principal:
- Fuente: `Inter, Proxima Nova, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Se aplica automáticamente a todos los componentes

---

## 💡 **CONSEJOS DE USO**

1. **Siempre usa el prefijo `ref-`** para evitar conflictos
2. **Combina clases** para obtener el efecto deseado
3. **Usa las utilidades** para ajustes rápidos
4. **Mantén la consistencia** usando las mismas clases en toda la app
5. **No modifiques la estructura HTML**, solo las clases

---

## 🔧 **EJEMPLOS PRÁCTICOS**

### Dashboard con estadísticas:
```html
<div class="ref-container-fluid">
    <div class="row">
        <div class="col-md-3">
            <div class="ref-card ref-card-stat">
                <div class="ref-card-body ref-text-center">
                    <i class="fas fa-calendar ref-text-primary ref-icon-lg"></i>
                    <h5 class="ref-text-dark">Próximos Encuentros</h5>
                    <h2 class="ref-text-primary">25</h2>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Tabla con datos:
```html
<div class="ref-table-responsive">
    <table class="ref-table ref-table-striped">
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Local</th>
                <th>Visitante</th>
                <th>Riesgo</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>2024-01-15</td>
                <td>Boca</td>
                <td>River</td>
                <td><span class="ref-badge ref-badge-riesgo-alto">ALTO</span></td>
            </tr>
        </tbody>
    </table>
</div>
```

### Formulario de filtros:
```html
<div class="ref-card">
    <div class="ref-card-header">Filtros</div>
    <div class="ref-card-body">
        <div class="row">
            <div class="col-md-4">
                <div class="ref-form-group">
                    <label class="ref-form-label">Torneo</label>
                    <select class="ref-form-select">
                        <option>LPF</option>
                        <option>ASCENSO</option>
                    </select>
                </div>
            </div>
            <div class="col-md-4">
                <div class="ref-form-group">
                    <label class="ref-form-label">Fecha Desde</label>
                    <input type="date" class="ref-form-control">
                </div>
            </div>
            <div class="col-md-4">
                <div class="ref-form-group">
                    <label class="ref-form-label">Acciones</label>
                    <div class="ref-d-flex ref-gap-2">
                        <button class="ref-btn ref-btn-primary">Filtrar</button>
                        <button class="ref-btn ref-btn-secondary">Limpiar</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

¡Con este sistema puedes estilizar toda la aplicación de forma consistente y rápida! 🚀
