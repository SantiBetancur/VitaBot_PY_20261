Auto deploy desconectado por el momento.

# Para correr el proyecto:

### git clone https://github.com/SantiBetancur/VitaBot_PY_20261.git

### cd /VitaBot_PY_20261/

# Instalar el CLI de catalyst y el SDK de python

### npm install -g zcatalyst-cli
### python3 -m pip install zcatalyst-sdk

# Descargar dependencias para la aplicacion de slate react + vue

### cd /VitaBotClientApp/
### npm install
# Iniciar el proyecto completo (slate app y funciones)

## IMPORTANTE: 
### DEBEN CAMBIAR LA URL ESTÁTICA DE LA CONFIGURACIÓN DE SLATE EN EL ARCHIVO catalyst.json, la ruta que sale es: C:\\Users\\santi\\OneDrive\\Desktop\\PROYECTO DE PRACTICA\\VitaBotClientApp, deben cambiarla por la ruta local del archivo.


#### catalyst serve

# Iniciar solo slate

### catalyst serve --only slate


