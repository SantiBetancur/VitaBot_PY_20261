# VitaBot Client App

Aplicación React + Vite para el chatbot VitaBot con integración a Zoho Catalyst.

## Configuración de Entornos

La aplicación detecta automáticamente el entorno basado en la variable `VITE_ENVIRONMENT` en el archivo `.env`:

### Archivo .env

```env
VITE_ENVIRONMENT=development
VITE_APP_DOMAIN_PRODUCTION=https://vitabotclientapp-ycwjmrpr.onslate.com
VITE_BACKEND_URL_PRODUCTION=https://vitabotproject-920088613.development.catalystserverless.com
VITE_APP_DOMAIN_DEV=http://localhost:3001
VITE_BACKEND_URL_DEV=http://localhost:3000
```

### Comandos Disponibles

```bash
# Desarrollo (lee VITE_ENVIRONMENT del .env)
npm run dev

# Desarrollo forzado a producción
npm run dev:prod

# Build para desarrollo
npm run build

# Build forzado a producción
npm run build:prod

# Preview del build
npm run preview
```

### Configuración Automática

La aplicación automáticamente:
- Configura el proxy del servidor de desarrollo según `VITE_ENVIRONMENT`
- Usa las URLs apropiadas en el código React
- Muestra en consola qué configuración está usando

### Cambio de Entorno

Para cambiar entre desarrollo y producción:

1. **Cambia la variable en .env:**
   ```env
   VITE_ENVIRONMENT=production  # o 'development'
   ```

2. **O usa los comandos específicos:**
   ```bash
   npm run dev:prod    # Para desarrollo con configuración de producción
   npm run build:prod  # Para build de producción
   ```

## Tecnologías

- React 18
- Vite
- React Markdown con soporte para tablas (remark-gfm)
- ESLint
