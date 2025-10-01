"""Administrador de contraseñas con experiencia visual en terminal.

Este módulo ofrece un flujo completamente en español que combina efectos
de color ANSI, tablas de texto y diálogos guiados para gestionar de forma
segura credenciales de servicios. Las contraseñas se almacenan con hash
SHA-256 y, adicionalmente, se cifran con una clave derivada de la propia
contraseña de administración (``1234``) para poder mostrarlas en texto
plano únicamente tras la autenticación.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from getpass import getpass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Optional


# === Configuración y rutas === #


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "password_manager.json"
LEGACY_FILE = BASE_DIR / "password_manager.txt"

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
BLUE = "\033[94m"


def clear_screen() -> None:
    """Limpia la terminal para ofrecer una sensación pulida."""

    os.system("cls" if os.name == "nt" else "clear")


def highlight(text: str, colour: str = CYAN, *, bold: bool = False) -> str:
    """Envuelve texto con códigos ANSI opcionales."""

    prefix = colour
    if bold:
        prefix += BOLD
    return f"{prefix}{text}{RESET}"


def banner_line(text: str, colour: str = MAGENTA) -> str:
    """Renderiza una línea centrada dentro de un marco decorativo."""

    width = 68
    content_width = width - 2
    message = text[:content_width]
    padding = max((content_width - len(message)) // 2, 0)
    left_spaces = " " * padding
    right_spaces = " " * (content_width - padding - len(message))
    return (
        highlight("╔" + "═" * content_width + "╗", colour)
        + "\n"
        + highlight(f"║{left_spaces}{message}{right_spaces}║", colour)
        + "\n"
        + highlight("╚" + "═" * content_width + "╝", colour)
    )


def pause(message: str = "Pulse Enter para continuar...") -> None:
    """Pausa la ejecución hasta recibir confirmación."""

    input(highlight(message, DIM))


# === Utilidades criptográficas === #


def hash_text(value: str) -> str:
    """Calcula SHA-256 para el texto proporcionado."""

    return sha256(value.encode("utf-8")).hexdigest()


def _derive_xor_key(password: str) -> bytes:
    """Deriva una clave simétrica a partir de la contraseña."""

    return sha256(password.encode("utf-8")).digest()


def encrypt_password(raw_password: str, admin_password: str) -> str:
    """Cifra la contraseña con un XOR contra la clave derivada."""

    key = _derive_xor_key(admin_password)
    data = raw_password.encode("utf-8")
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_password(encrypted_password: str, admin_password: str) -> str:
    """Descifra la contraseña generada con ``encrypt_password``."""

    key = _derive_xor_key(admin_password)
    payload = base64.urlsafe_b64decode(encrypted_password.encode("utf-8"))
    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(payload))
    return decrypted.decode("utf-8")


# === Persistencia === #


@dataclass
class Entry:
    """Representa un registro de credenciales."""

    site: str
    username: str
    password_hash: str
    password_encrypted: str
    created_at: str
    updated_at: str

    @classmethod
    def build(
        cls,
        site: str,
        username: str,
        password: str,
        admin_password: str,
    ) -> "Entry":
        """Crea un registro preparado para guardarse."""

        timestamp = datetime.utcnow().isoformat()
        return cls(
            site=site.strip(),
            username=username.strip(),
            password_hash=hash_text(password),
            password_encrypted=encrypt_password(password, admin_password),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update_password(self, password: str, admin_password: str) -> None:
        """Actualiza todos los campos relacionados con la contraseña."""

        self.password_hash = hash_text(password)
        self.password_encrypted = encrypt_password(password, admin_password)
        self.updated_at = datetime.utcnow().isoformat()

    def update_login(self, *, site: Optional[str] = None, username: Optional[str] = None) -> None:
        """Actualiza metadatos del registro."""

        if site is not None:
            self.site = site.strip()
        if username is not None:
            self.username = username.strip()
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        """Convierte la entrada en una estructura serializable."""

        return {
            "site": self.site,
            "username": self.username,
            "password_hash": self.password_hash,
            "password_encrypted": self.password_encrypted,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Entry":
        """Crea una instancia a partir de un diccionario."""

        return cls(
            site=str(payload.get("site", "")).strip(),
            username=str(payload.get("username", "")).strip(),
            password_hash=str(payload.get("password_hash", "")),
            password_encrypted=str(payload.get("password_encrypted", "")),
            created_at=str(payload.get("created_at", datetime.utcnow().isoformat())),
            updated_at=str(payload.get("updated_at", datetime.utcnow().isoformat())),
        )


def load_entries() -> List[Entry]:
    """Lee los registros existentes del archivo JSON."""

    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as handle:
        try:
            raw_entries = json.load(handle)
        except json.JSONDecodeError as exc:
            print(highlight("⚠️  Error al interpretar el archivo de datos.", RED, bold=True))
            print(highlight(str(exc), RED))
            return []
    return [Entry.from_dict(item) for item in raw_entries if isinstance(item, dict)]


def save_entries(entries: Iterable[Entry]) -> None:
    """Persistente los registros con sangría para legibilidad."""

    payload = [entry.to_dict() for entry in entries]
    with DATA_FILE.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def ensure_storage(admin_password: str) -> None:
    """Crea o migra el almacenamiento desde la versión antigua."""

    if DATA_FILE.exists():
        return

    if not LEGACY_FILE.exists():
        save_entries([])
        return

    migrated: List[Entry] = []
    lines = LEGACY_FILE.read_text(encoding="utf-8").splitlines()
    for chunk in range(0, len(lines), 4):
        try:
            site = lines[chunk].split(":", 1)[1].strip()
            username = lines[chunk + 1].split(":", 1)[1].strip()
            password = lines[chunk + 2].split(":", 1)[1].strip()
        except (IndexError, ValueError):
            continue
        migrated.append(Entry.build(site, username, password, admin_password))

    save_entries(migrated)
    LEGACY_FILE.rename(LEGACY_FILE.with_suffix(".bak"))


# === Vista === #


def print_welcome() -> None:
    """Muestra el banner principal de bienvenida."""

    clear_screen()
    art = [
        highlight("      ██████╗  █████╗ ███████╗████████╗", BLUE, bold=True),
        highlight("     ██╔════╝ ██╔══██╗██╔════╝╚══██╔══╝", CYAN, bold=True),
        highlight("     ██║  ███╗███████║█████╗     ██║   ", GREEN, bold=True),
        highlight("     ██║   ██║██╔══██║██╔══╝     ██║   ", YELLOW, bold=True),
        highlight("     ╚██████╔╝██║  ██║███████╗   ██║   ", MAGENTA, bold=True),
        highlight("      ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ", RED, bold=True),
    ]
    print("\n".join(art))
    print()
    print(banner_line("Administrador de Contraseñas"))
    print(highlight("Seguridad y estilo unidos en tu terminal", ITALIC + CYAN))
    print()


def format_table(rows: List[List[str]], headers: List[str]) -> str:
    """Crea una tabla ASCII agradable con bordes redondeados."""

    if not rows:
        return highlight("╭───────────────────────────────────────╮\n│   No hay registros para mostrar.      │\n╰───────────────────────────────────────╯", DIM)

    column_widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            column_widths[idx] = max(column_widths[idx], len(cell))

    def format_row(parts: List[str], left: str, sep: str, right: str) -> str:
        cells = [f" {part.ljust(column_widths[idx])} " for idx, part in enumerate(parts)]
        return left + sep.join(cells) + right

    top = format_row(headers, "╭", "┬", "╮")
    middle = format_row(["─" * width for width in column_widths], "├", "┼", "┤")
    bottom = format_row(["─" * width for width in column_widths], "╰", "┴", "╯")

    header_row = format_row(headers, "│", "│", "│")
    header_row = highlight(header_row, MAGENTA, bold=True)
    body = [header_row]
    body.append(highlight(middle, DIM))
    for row in rows:
        body.append(format_row(row, "│", "│", "│"))

    return "\n".join([highlight(top, DIM)] + body + [highlight(bottom, DIM)])


def prompt_choice(options: List[str], *, exit_label: str = "Salir") -> int:
    """Pregunta por una opción del menú."""

    for idx, option in enumerate(options, start=1):
        print(highlight(f" {idx}. {option}", CYAN))
    print(highlight(f" 0. {exit_label}", RED, bold=True))

    while True:
        choice = input(highlight("Seleccione una opción: ", YELLOW, bold=True))
        if choice.isdigit():
            value = int(choice)
            if 0 <= value <= len(options):
                return value
        print(highlight("Opción inválida, inténtelo de nuevo.", RED))


# === Lógica de aplicación === #


def authenticate() -> str:
    """Solicita las credenciales de administración."""

    attempts = 3
    while attempts:
        username = input(highlight("Usuario administrador: ", GREEN, bold=True)).strip()
        password = getpass(highlight("Contraseña: ", GREEN, bold=True))
        if username == ADMIN_USERNAME and hash_text(password) == ADMIN_PASSWORD_HASH:
            print(highlight("✔ Acceso concedido", GREEN, bold=True))
            pause("Bienvenido, presione Enter para comenzar...")
            return password
        attempts -= 1
        print(highlight(f"Credenciales incorrectas. Intentos restantes: {attempts}", RED))

    print(highlight("Demasiados intentos fallidos. Cerrando...", RED, bold=True))
    sys.exit(1)


def add_entry(entries: List[Entry], admin_password: str) -> None:
    """Agrega un nuevo registro."""

    clear_screen()
    print(banner_line("Nuevo registro", colour=GREEN))
    site = input(highlight("Sitio o aplicación: ", CYAN, bold=True)).strip()
    username = input(highlight("Usuario / correo: ", CYAN, bold=True)).strip()
    password = getpass(highlight("Contraseña del servicio: ", CYAN, bold=True))

    if not site or not username or not password:
        print(highlight("Todos los campos son obligatorios.", RED))
        pause()
        return

    entries.append(Entry.build(site, username, password, admin_password))
    save_entries(entries)
    print(highlight("Registro creado correctamente.", GREEN))
    pause()


def choose_entry(entries: List[Entry]) -> Optional[Entry]:
    """Permite seleccionar un registro por índice."""

    if not entries:
        print(highlight("No hay registros disponibles.", RED))
        pause()
        return None

    for idx, entry in enumerate(entries, start=1):
        print(highlight(f" {idx}. {entry.site} ({entry.username})", CYAN))

    while True:
        choice = input(highlight("Seleccione un número o presione Enter para cancelar: ", YELLOW))
        if not choice:
            return None
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(entries):
                return entries[index]
        print(highlight("Selección inválida.", RED))


def view_entries(entries: List[Entry], admin_password: str) -> None:
    """Muestra los registros con opciones de ordenado y filtrado."""

    clear_screen()
    print(banner_line("Tus credenciales", colour=BLUE))

    if not entries:
        print(highlight("Aún no has guardado contraseñas.", DIM))
        pause()
        return

    sort_options = ["Sitio", "Usuario", "Fecha de creación"]
    sort_choice = prompt_choice(sort_options, exit_label="Volver")
    if sort_choice == 0:
        return

    key_funcs = [
        lambda entry: entry.site.lower(),
        lambda entry: entry.username.lower(),
        lambda entry: entry.created_at,
    ]
    ordered = sorted(entries, key=key_funcs[sort_choice - 1])

    search_term = input(highlight("Filtro opcional (palabra clave): ", YELLOW)).strip().lower()
    if search_term:
        ordered = [
            entry
            for entry in ordered
            if search_term in entry.site.lower() or search_term in entry.username.lower()
        ]

    rows = []
    for entry in ordered:
        decrypted = decrypt_password(entry.password_encrypted, admin_password)
        rows.append(
            [
                entry.site,
                entry.username,
                decrypted,
                datetime.fromisoformat(entry.updated_at).strftime("%Y-%m-%d %H:%M"),
            ]
        )

    headers = ["Sitio", "Usuario", "Contraseña", "Actualizado"]
    print(format_table(rows, headers))
    pause()


def edit_entry(entries: List[Entry], admin_password: str) -> None:
    """Permite editar un registro existente."""

    clear_screen()
    print(banner_line("Editar registro", colour=YELLOW))
    entry = choose_entry(entries)
    if entry is None:
        return

    new_site = input(highlight(f"Nuevo sitio (Enter para mantener '{entry.site}'): ", CYAN)) or None
    new_username = input(highlight(f"Nuevo usuario (Enter para mantener '{entry.username}'): ", CYAN)) or None
    new_password = getpass(highlight("Nueva contraseña (Enter para mantener la actual): ", CYAN))

    if new_site or new_username:
        entry.update_login(site=new_site or None, username=new_username or None)
    if new_password:
        entry.update_password(new_password, admin_password)

    save_entries(entries)
    print(highlight("Registro actualizado correctamente.", GREEN))
    pause()


def delete_entry(entries: List[Entry]) -> None:
    """Elimina un registro tras confirmación."""

    clear_screen()
    print(banner_line("Eliminar registro", colour=RED))
    entry = choose_entry(entries)
    if entry is None:
        return

    confirmation = input(highlight("¿Seguro que deseas eliminarlo? (s/N): ", RED, bold=True)).strip().lower()
    if confirmation == "s":
        entries.remove(entry)
        save_entries(entries)
        print(highlight("Registro eliminado.", GREEN))
    else:
        print(highlight("Operación cancelada.", YELLOW))
    pause()


def main() -> None:
    """Punto de entrada del programa."""

    print_welcome()
    admin_password = authenticate()
    ensure_storage(admin_password)

    entries = load_entries()

    while True:
        clear_screen()
        print_welcome()
        print(highlight("Menú principal", MAGENTA, bold=True))
        choice = prompt_choice(
            [
                "Añadir nueva credencial",
                "Ver y ordenar contraseñas",
                "Editar un registro",
                "Eliminar un registro",
            ],
            exit_label="Salir",
        )

        if choice == 0:
            print(highlight("Gracias por utilizar el gestor. ¡Hasta pronto!", CYAN))
            break
        if choice == 1:
            add_entry(entries, admin_password)
        elif choice == 2:
            view_entries(entries, admin_password)
        elif choice == 3:
            edit_entry(entries, admin_password)
        elif choice == 4:
            delete_entry(entries)

        entries = load_entries()


if __name__ == "__main__":  # pragma: no cover - punto de entrada interactivo
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(highlight("Aplicación interrumpida por el usuario.", RED))

