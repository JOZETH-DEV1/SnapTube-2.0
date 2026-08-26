from ytmusicapi import setup
print("==========================================")
print("🔗 VINCULACIÓN CON CUENTA DE YOUTUBE / GOOGLE")
print("==========================================")
print("Sigue las instrucciones que aparecerán abajo para vincular tu cuenta.")
print("Esto permitirá que la app lea tu algoritmo real de YouTube Music.")
print("")
setup(filepath="oauth.json")
print("✅ ¡Vinculación exitosa! Ahora reinicia la app con 'python app.py'")
