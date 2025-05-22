# Proyecto
> En el SRC estan todas las carpets de la Pag Web:

Core:Posee los Objetos que vamos a utilizar

web-> templates : Son los html, seria correcto crearle uan carpeta para cada uno(el home y el layaout no es necesario)

Web-> controllers : va a estar todos nuestors .py de los html

web -> handlers : es mas que nada una carpeta de verificacion para ver si estas Iniciado sesion o no, o si tener permisos para estar en cierta ventana(no tocar por ahora)

#   Comandos en CMDR o terminal de VisualStudio

Comando para Iniciar la aplicacion
Flask run

Comando para resetear la base de datos
Flask reset-db

# Todo esto en CMDR

Para ver donde estas parado en cmdr y ver todas las ramas

git branch -a 

Para ir a una rama es 

git checkout <nombre>

Para empezar a crear rama lo que tiene que hacer es posicionarse en DEVELOPMENT

git branch feature/<nombreDeLaRama>   -> Esto te lo crea, pero luego con el CHECKOUT vas a tener que ir a posicionarte en ella para empezar a trabajar

Luego de haber terminado en tu RAMA, lo que podes hacer es MERGEAR, lo que va a traer las cosas de TU rama al development

git merge feature/<nombreDeLaRama>   -> Posicionado en DEVELOPMENT

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