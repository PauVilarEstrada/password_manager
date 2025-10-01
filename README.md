# Password Manager (CLI)

This project provides a terminal-based password manager that lets you store, browse, edit, and delete credentials for websites or applications. All interactions happen through a guided command-line menu.

## Project Contents

- `codline.py`: Main CLI application.
- `password_manager.json`: Credentials database created automatically on first run (per user). A legacy `password_manager.txt` file will be migrated and renamed to `password_manager.bak` the first time you run the updated tool.

## Requirements

- Python 3.9 or newer.

You can verify the installed version with:

```bash
python --version
```

## Running the CLI

1. Open a terminal in the project root.
2. Run the application:
   ```bash
   python codline.py
   ```
3. Authenticate with the administrator credentials when prompted:
   - **User:** `admin`
   - **Password:** `1234`
4. Follow the on-screen menu to add, list, modify, or delete credentials.

### Storage location

By default the JSON database is stored at:

- **Linux/macOS:** `~/.password_manager/password_manager.json`
- **Windows:** `C:\Users\<User>\.password_manager\password_manager.json`

You can override the storage path by setting the `PASSWORD_MANAGER_DATA` environment variable to an absolute or relative path before running the script. Example:

```bash
export PASSWORD_MANAGER_DATA="/path/to/custom/location.json"
python codline.py
```

## Features

- Administrator login with three attempts before exit.
- Passwords stored as both SHA-256 hashes and symmetrically encrypted values so they can be shown after admin validation.
- Interactive filters and sorting when listing credentials.
- Migration from the previous plain-text format to the new JSON structure.

## Security Notice

This application is designed for educational purposes. Passwords are encrypted with a reversible XOR scheme derived from the administrator password and should not be considered secure for production use. For real-world deployments, integrate a proven key management solution and stronger cryptography.
