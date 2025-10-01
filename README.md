*ESPAÑOL*


# Administrador de Contraseñas

Este proyecto es un administrador de contraseñas que permite almacenar, visualizar, modificar y eliminar contraseñas para diferentes sitios web o aplicaciones. Hay dos versiones disponibles:

1. **Versión no visual (consola/CLI)**
2. **Versión visual (interfaz gráfica/GUI con `tkinter`)**

## Contenido del Proyecto

- `password_manager.txt`: Archivo donde se guardan las contraseñas y usuarios/ correos electrónicos.
- `codline.py`: Script de la versión no visual.
- `Visual/`: Carpeta que contiene la versión visual.

## Requisitos Previos

Asegúrate de tener Python instalado. Puedes verificarlo ejecutando:
```bash
python --version
````

Para la versión visual (tkinter), tkinter generalmente viene preinstalado con Python. Si tienes problemas, asegúrate de tener una instalación completa de Python o instala tkinter usando el siguiente comando en algunas distribuciones de Linux:
```bash
sudo apt-get install python3-tk
````

## Versión No Visual (CLI)
La versión no visual se ejecuta en la terminal y permite:

1. Añadir usuarios/correos y contraseñas sin autenticación de administrador.
2. Ver usuarios/correos y contraseñas con filtros, solicitando autenticación de administrador.
3. Modificar o eliminar usuarios/correos y contraseñas, solicitando autenticación de administrador.
**Cómo Ejecutar:**
Abre una terminal en la raíz del proyecto.
Ejecuta
```bash
python codline.py
````
4. Sigue las instrucciones en pantalla para interactuar con el menú.

**Credenciales de Administrador:**
`Usuario: aadmin`
`Contraseña: admin`

## Versión Visual (GUI)
Ubicación:
Carpeta: Visual/ Archivo: Visual/codlineVisual.py
La versión visual tiene una interfaz gráfica de usuario (GUI) creada con tkinter que permite:

1. Añadir usuarios/correos y contraseñas mediante cuadros de diálogo.
2. Ver usuarios/correos y contraseñas en una ventana con un área de texto desplazable, solicitando autenticación de administrador.
3. Modificar o eliminar usuarios/correos y contraseñas, solicitando autenticación de administrador, a través de una interfaz gráfica.
**Cómo Ejecutar:**
*Abre una terminal y navega a la carpeta Visual:*
````bash
cd Visual
````
Ejecuta:
````bash
python codlineVisual.py
````
**Credenciales de Administrador:**
`Usuario: adminEMP`
`Contraseña: 123456abc987`

## Formato de Almacenamiento en password_manager.txt
Las entradas de usuarios/correos y contraseñas se guardan en el archivo password_manager.txt con el siguiente formato:

Sitio web / Aplicación: https://www.instagram.com/
Usuario / Correo: example_user
Contraseña: example_password

----------------------------------------------------------------------
Sitio web / Aplicación: https://github.com/
Usuario / Correo: another_user
Contraseña: another_password



*Seguridad: Esta aplicación guarda las contraseñas en texto plano. Se recomienda usar en entornos de prueba o educativos. Para un uso serio, considera cifrar las contraseñas antes de almacenarlas.*

*Dependencias: Ambas versiones requieren Python. La versión visual también requiere tkinter, que viene con la mayoría de las instalaciones de Python.*
