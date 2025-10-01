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

## Versión CMD (CLI)
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



*Seguridad: Esta aplicación guarda las contraseñas en texto plano. Se recomienda usar en entornos de prueba o educativos. Para un uso serio, considera cifrar las contraseñas antes de almacenarlas.*

*Dependencias: Ambas versiones requieren Python. La versión visual también requiere tkinter, que viene con la mayoría de las instalaciones de Python.*
