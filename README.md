Auto deploy desconectado por el momento.

para correr el proyecto:

git clone https://github.com/SantiBetancur/VitaBot_PY_20261.git

cd /VitaBot_PY_20261/

Instalar el CLI de catalyst y el SDK de python

npm install -g zcatalyst-cli
python3 -m pip install zcatalyst-sdk

descargar dependencias para la aplicacion de slate react + vue

cd /VitaBotClientApp/
npm install
Iniciar el proyecto completo (slate app y funciones)

catalyst serve

Iniciar solo slate

catalyst serve --only slate


