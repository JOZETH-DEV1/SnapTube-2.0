import sys
import json
import os
from ytmusicapi import setup

print("==========================================")
print("🔗 VINCULACIÓN CON CUENTA DE YOUTUBE (Vía Cookie / Headers)")
print("==========================================")
print("¡Exacto! El inicio de sesión es mediante tus cookies/headers.")
print("Sigue estos pasos en tu computadora o navegador de escritorio:")
print("1. Abre music.youtube.com y entra a tu cuenta.")
print("2. Presiona F12 (o abre las herramientas de desarrollador).")
print("3. Ve a la pestaña 'Network' (Red) y recarga la página.")
print("4. Escribe 'browse' en la cajita de filtro/búsqueda de la red.")
print("5. Haz clic en el primer archivo 'browse' de la lista.")
print("6. Ve a 'Headers' -> 'Request Headers' y haz clic en 'Copy Raw' (o copia todo el bloque).")
print("7. Pega todo ese texto aquí abajo y presiona ENTER, luego presiona CTRL+D.")
print("")
print("Esperando que pegues tus headers/cookies...")
try:
    setup(filepath="oauth.json")
    
    # FIX YTMUSICAPI BUG: Add dummy authorization header to force Browser Auth mode
    if os.path.exists("oauth.json"):
        with open("oauth.json", "r") as f:
            data = json.load(f)
        if "authorization" not in data:
            data["authorization"] = "SAPISIDHASH 1"
            with open("oauth.json", "w") as f:
                json.dump(data, f)
                
    print("\n✅ ¡Vinculación exitosa! Ahora reinicia la app con 'python app.py'")
except Exception as e:
    print("\n❌ Hubo un error:", e)
