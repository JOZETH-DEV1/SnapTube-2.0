import sys
from ytmusicapi import setup

print("==========================================")
print("🔗 VINCULACIÓN CON CUENTA DE YOUTUBE (Vía Cookie / Headers)")
print("==========================================")
print("¡Exacto! El inicio de sesión es mediante tus cookies/headers.")
print("Sigue estos pasos en tu computadora o navegador de escritorio:")
print("1. Abre music.youtube.com y entra a tu cuenta.")
print("2. Presiona F12 (o abre las herramientas de desarrollador).")
print("3. Ve a la pestaña 'Network' (Red) y recarga la página.")
print("4. Haz clic en el primer archivo de la lista (music.youtube.com).")
print("5. Busca la sección 'Request Headers' (Encabezados de solicitud), haz clic derecho y selecciona 'Copiar valor' o 'Copy Request Headers'.")
print("6. Pega todo ese texto aquí abajo y presiona ENTER, luego presiona CTRL+D.")
print("")
print("Esperando que pegues tus headers/cookies...")
try:
    setup(filepath="oauth.json")
    print("\n✅ ¡Vinculación exitosa! Ahora reinicia la app con 'python app.py'")
except Exception as e:
    print("\n❌ Hubo un error:", e)
