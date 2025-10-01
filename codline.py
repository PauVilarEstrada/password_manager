"""Administrador de contraseñas con interfaz de terminal mejorada.

Este módulo proporciona una experiencia de línea de comandos amigable para
gestionar credenciales. Las contraseñas de los servicios se almacenan como
hash y, además, se cifran con la clave del administrador para poder mostrarse
en texto plano una vez que se valida el acceso con ``admin`` y ``1234``.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from datetime import datetime
from getpass import getpass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional


def _resolve_data_file() -> Path:
    """Obtiene la ruta del fichero JSON respetando variables de entorno."""

    env_path = os.environ.get("PASSWORD_MANAGER_DATA")
    if env_path:
        return Path(env_path).expanduser().resolve()

    return (Path.home() / ".password_manager" / "password_manager.json").resolve()


DATA_FILE = _resolve_data_file()
BASE_DIR = Path(__file__).resolve().parent


def _legacy_file_candidates() -> Iterator[Path]:
    """Proporciona posibles ubicaciones del antiguo fichero de texto."""

    yield DATA_FILE.with_suffix(".txt")
    yield BASE_DIR / "password_manager.txt"
    yield Path.cwd() / "password_manager.txt"


LEGACY_FILE_CANDIDATES = tuple(dict.fromkeys(path for path in _legacy_file_candidates()))

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = sha256("1234".encode("utf-8")).hexdigest()


# === Utilidades de estilo === #


RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
DIM = "\033[2m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"


def clear_screen() -> None:
    """Limpia la terminal para ofrecer una experiencia más cuidada."""

    os.system("cls" if os.name == "nt" else "clear")


def highlight(text: str, colour: str = CYAN, *, bold: bool = False) -> str:
    """Devuelve texto con formato ANSI opcionalmente en negrita."""

    prefix = colour
    if bold:
        prefix += BOLD
    return f"{prefix}{text}{RESET}"


def print_header() -> None:
    """Muestra el encabezado principal del gestor."""

    banner = "═" * 56
    title = highlight("Administrador de Contraseñas", colour=MAGENTA, bold=True)
    print(f"{banner}\n{title.center(56)}\n{banner}")


def pause(message: str = "Presione Enter para continuar...") -> None:
    """Detiene la ejecución hasta que la persona usuaria confirme."""

    input(highlight(message, colour=DIM))


# === Funciones criptográficas básicas === #


def hash_text(text: str) -> str:
    """Calcula el hash SHA-256 de un texto en formato hexadecimal."""

    return sha256(text.encode("utf-8")).hexdigest()


def _derive_xor_key(password: str) -> bytes:
    """Deriva una clave a partir de la contraseña del administrador."""

    return sha256(password.encode("utf-8")).digest()


def encrypt_password(raw_password: str, admin_password: str) -> str:
    """Cifra la contraseña usando un XOR con la clave derivada."""

    key = _derive_xor_key(admin_password)
    data = raw_password.encode("utf-8")
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_password(encrypted_password: str, admin_password: str) -> str:
    """Descifra la contraseña cifrada con ``encrypt_password``."""

    key = _derive_xor_key(admin_password)
    data = base64.urlsafe_b64decode(encrypted_password.encode("utf-8"))
    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return decrypted.decode("utf-8")


# === Persistencia de datos === #


Entry = Dict[str, str]


def load_entries() -> List[Entry]:
    """Lee los registros almacenados en el fichero JSON."""

    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        if not isinstance(data, list):  # type: ignore[unreachable]
            raise ValueError("El formato del archivo es inválido.")
        return [entry for entry in data if isinstance(entry, dict)]
    except json.JSONDecodeError as exc:  # pragma: no cover - difícil de forzar en pruebas
        print(highlight("Error al leer el archivo de datos.", RED, bold=True))
        print(highlight(str(exc), RED))
        return []


def save_entries(entries: Iterable[Entry]) -> None:
    """Guarda los registros en disco con sangría para lectura sencilla."""

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as fp:
        json.dump(list(entries), fp, indent=2, ensure_ascii=False)


def build_entry(site: str, username: str, password: str, admin_password: str) -> Entry:
    """Crea la estructura de un registro listo para almacenar."""

    now = datetime.utcnow().isoformat()
    return {
        "site": site.strip(),
        "username": username.strip(),
        "password_hash": hash_text(password),
        "password_encrypted": encrypt_password(password, admin_password),
        "created_at": now,
        "updated_at": now,
    }


def _find_legacy_file() -> Optional[Path]:
    """Devuelve la ruta del fichero de texto antiguo si existe."""

    for candidate in LEGACY_FILE_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def ensure_storage(admin_password: str) -> None:
    """Crea o migra el almacenamiento inicial si es necesario."""

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists():
        return

    legacy_file = _find_legacy_file()
    if legacy_file is None:
        save_entries([])
        return

    entries: List[Entry] = []
    with legacy_file.open("r", encoding="utf-8") as fp:
        lines = [line.strip() for line in fp.readlines() if line.strip()]

    for i in range(0, len(lines), 3):
        try:
            site = lines[i].replace("Sitio web / Aplicación: ", "")
            username = lines[i + 1].replace("Usuario / Correo: ", "")
            password = lines[i + 2].replace("Contraseña: ", "")
        except IndexError:
            continue
        entries.append(build_entry(site, username, password, admin_password))

    save_entries(entries)
    try:
        legacy_file.rename(legacy_file.with_suffix(".bak"))
    except OSError:
        pass


# === Lógica de autenticación === #


def authenticate(username: str, password: str) -> bool:
    """Comprueba si las credenciales corresponden al administrador."""

    return username == ADMIN_USERNAME and hash_text(password) == ADMIN_PASSWORD_HASH


def prompt_admin_login() -> Optional[str]:
    """Solicita acceso al administrador con un máximo de intentos."""

    clear_screen()
    print_header()
    print(highlight("Se requiere iniciar sesión para continuar.\n", YELLOW, bold=True))

    for attempt in range(3, 0, -1):
        username = input("Usuario: ").strip()
        password = getpass("Contraseña: ")

        if authenticate(username, password):
            print(highlight("\nAcceso concedido.\n", GREEN, bold=True))
            pause()
            return password

        print(highlight("Credenciales incorrectas.", RED, bold=True))
        if attempt - 1:
            print(highlight(f"Intentos restantes: {attempt - 1}", RED))
        print()

    print(highlight("Se agotaron los intentos. Saliendo...", RED, bold=True))
    pause()
    return None


# === Utilidades de visualización === #


def format_datetime(value: str) -> str:
    """Transforma una fecha ISO a un formato legible."""

    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value


def draw_table(headers: List[str], rows: List[List[str]]) -> None:
    """Imprime una tabla ASCII con bordes limpios."""

    if not rows:
        print(highlight("No hay registros para mostrar.", YELLOW, bold=True))
        return

    column_widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            column_widths[idx] = max(column_widths[idx], len(cell))

    border = "╔" + "╦".join("═" * (width + 2) for width in column_widths) + "╗"
    separator = "╠" + "╬".join("═" * (width + 2) for width in column_widths) + "╣"
    footer = "╚" + "╩".join("═" * (width + 2) for width in column_widths) + "╝"

    def format_row(row: List[str]) -> str:
        cells = [f" {cell.ljust(width)} " for cell, width in zip(row, column_widths)]
        return "║" + "║".join(cells) + "║"

    print(border)
    print(format_row(headers))
    print(separator)
    for row in rows:
        print(format_row(row))
    print(footer)


def collect_filter(entries: List[Entry]) -> List[Entry]:
    """Solicita filtros y ordenación a la persona usuaria."""

    print(highlight("Opciones de ordenación:", MAGENTA, bold=True))
    print("1. Sitio web / Aplicación (A-Z)")
    print("2. Usuario / Correo (A-Z)")
    print("3. Fecha de creación (más recientes primero)")
    print("4. Fecha de actualización (más recientes primero)")

    option = input("Elija una opción (Enter para omitir): ").strip()
    filtered = entries[:]

    if option == "1":
        filtered.sort(key=lambda item: item["site"].lower())
    elif option == "2":
        filtered.sort(key=lambda item: item["username"].lower())
    elif option == "3":
        filtered.sort(key=lambda item: item["created_at"], reverse=True)
    elif option == "4":
        filtered.sort(key=lambda item: item["updated_at"], reverse=True)

    term = input("Filtrar por texto (sitio, usuario o contraseña) [Enter para todos]: ").strip().lower()
    if term:
        filtered = [
            entry
            for entry in filtered
            if term in entry["site"].lower()
            or term in entry["username"].lower()
        ]

    return filtered


# === Acciones del gestor === #


def add_entry(admin_password: str) -> None:
    """Añade una nueva credencial al gestor."""

    clear_screen()
    print_header()
    print(highlight("Añadir nueva credencial", MAGENTA, bold=True))
    print()

    site = input("Sitio web / Aplicación: ").strip()
    username = input("Usuario / Correo: ").strip()
    password = getpass("Contraseña: ")

    if not site or not username or not password:
        print(highlight("Todos los campos son obligatorios.", RED, bold=True))
        pause()
        return

    entries = load_entries()
    entries.append(build_entry(site, username, password, admin_password))
    save_entries(entries)

    print(highlight("Credencial almacenada correctamente.", GREEN, bold=True))
    pause()


def list_entries(admin_password: str) -> None:
    """Muestra las credenciales guardadas con diferentes vistas."""

    clear_screen()
    print_header()
    entries = load_entries()

    if not entries:
        print(highlight("Aún no hay credenciales guardadas.", YELLOW, bold=True))
        pause()
        return

    filtered = collect_filter(entries)

    rows: List[List[str]] = []
    for idx, entry in enumerate(filtered, start=1):
        try:
            password_plain = decrypt_password(entry["password_encrypted"], admin_password)
        except Exception:  # pragma: no cover - protección adicional
            password_plain = highlight("Error al descifrar", RED)

        rows.append(
            [
                str(idx),
                entry["site"],
                entry["username"],
                password_plain,
                format_datetime(entry["updated_at"]),
            ]
        )

    draw_table(["#", "Sitio", "Usuario", "Contraseña", "Actualizado"], rows)
    pause()


def select_entry(entries: List[Entry]) -> Optional[int]:
    """Permite escoger un registro por su índice."""

    if not entries:
        print(highlight("No hay registros disponibles.", YELLOW, bold=True))
        pause()
        return None

    for idx, entry in enumerate(entries, start=1):
        print(
            f"{highlight(str(idx), colour=CYAN, bold=True)} - "
            f"{entry['site']} ({entry['username']})"
        )

    try:
        selection = int(input("Seleccione un registro (0 para cancelar): "))
    except ValueError:
        print(highlight("Entrada no válida.", RED, bold=True))
        pause()
        return None

    if selection == 0:
        return None

    if 1 <= selection <= len(entries):
        return selection - 1

    print(highlight("Selección fuera de rango.", RED, bold=True))
    pause()
    return None


def edit_entry(admin_password: str) -> None:
    """Permite modificar un registro existente."""

    clear_screen()
    print_header()
    print(highlight("Editar credencial", MAGENTA, bold=True))
    entries = load_entries()
    index = select_entry(entries)
    if index is None:
        return

    entry = entries[index]
    print()

    new_site = input(f"Nuevo sitio [{entry['site']}]: ").strip()
    new_username = input(f"Nuevo usuario [{entry['username']}]: ").strip()
    new_password = getpass("Nueva contraseña (dejar en blanco para mantener): ")

    if new_site:
        entry["site"] = new_site
    if new_username:
        entry["username"] = new_username
    if new_password:
        entry["password_hash"] = hash_text(new_password)
        entry["password_encrypted"] = encrypt_password(new_password, admin_password)

    entry["updated_at"] = datetime.utcnow().isoformat()
    save_entries(entries)

    print(highlight("Credencial actualizada correctamente.", GREEN, bold=True))
    pause()


def delete_entry() -> None:
    """Elimina un registro existente."""

    clear_screen()
    print_header()
    print(highlight("Eliminar credencial", MAGENTA, bold=True))
    entries = load_entries()
    index = select_entry(entries)
    if index is None:
        return

    entry = entries.pop(index)
    save_entries(entries)

    print(highlight(
        f"Se eliminó la credencial de {entry['site']} ({entry['username']}).",
        GREEN,
        bold=True,
    ))
    pause()


# === Programa principal === #


def main_menu(admin_password: str) -> None:
    """Controla el flujo principal del administrador."""

    ensure_storage(admin_password)

    while True:
        clear_screen()
        print_header()
        print("Seleccione una opción:\n")
        print("1. Añadir credencial")
        print("2. Ver credenciales")
        print("3. Modificar credencial")
        print("4. Eliminar credencial")
        print("5. Salir")

        option = input("Opción elegida: ").strip()

        if option == "1":
            add_entry(admin_password)
        elif option == "2":
            list_entries(admin_password)
        elif option == "3":
            edit_entry(admin_password)
        elif option == "4":
            delete_entry()
        elif option == "5":
            clear_screen()
            print(highlight("¡Hasta pronto!", GREEN, bold=True))
            break
        else:
            print(highlight("Opción no válida.", RED, bold=True))
            pause()


def main() -> None:
    """Punto de entrada del script."""

    admin_password = prompt_admin_login()
    if admin_password is None:
        sys.exit(1)

    main_menu(admin_password)


if __name__ == "__main__":
    main()
