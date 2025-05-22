# Proyecto
> En el SRC estan todas las carpets de la Pag Web:

Core:Posee los Objetos que vamos a utilizar

web-> templates : Son los html, seria correcto crearle uan carpeta para cada uno(el home y el layaout no es necesario)

Web-> controllers : va a estar todos nuestors .py de los html

web -> handlers : es mas que nada una carpeta de verificacion para ver si estas Iniciado sesion o no, o si tener permisos para estar en cierta ventana(no tocar por ahora)


Comando para Iniciar la aplicacion
Flask run

Comando para resetear la base de datos
Flask reset-db

## Instalación
Este proyecto utiliza las siguientes dependencias
Para instalar las dependencias, ejecuta el siguiente comando:

```bash
pip install -r requirements.txt

## Ngrok

Instalar ngrok, y crearse una cuenta, descargarlo y ponerlo dentro de una carpeta
Posicionarse Dentro de la carpeta en powerShel o Cmd y colocar "ngrok config add-authtoken "Tu token"  (que lo sacas de "token de autorizacion(pagina de ngrok)
Abrir la pagina web con "Flask run" y luego pocicionados en la carpeta de Ngrok y colocas "ngrok http 5000" en la terminal cmd, para luego presionar el link que te da
en Forwarding, ejemploe -> Forwarding                   https://87d2-200-114-209-238.ngrok-free.app -> http://localhost:5000 , te mostrar una ventana de aviso, le das a 
"visitar sitio" y ya estas en https