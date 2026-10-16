# Sustituto de pyperclip para el navegador: sin acceso al portapapeles.
_clipboard = ""


def copy(text):
    global _clipboard
    _clipboard = text


def paste():
    return _clipboard
