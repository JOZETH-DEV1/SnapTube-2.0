#!/bin/bash
echo "======================================"
echo "🚀 Instalando Snaptube Local en Termux"
echo "======================================"
sleep 1

# Actualizar e instalar dependencias del sistema
echo "[1/4] Actualizando sistema..."
pkg update -y && pkg upgrade -y
echo "[2/4] Instalando Python y FFmpeg (necesario para extraer audio)..."
pkg install python ffmpeg git -y

# Clonar o actualizar el repositorio
echo "[3/4] Descargando la aplicación..."
cd ~
if [ -d "SnapTube-2.0" ]; then
    cd SnapTube-2.0
    git pull
else
    git clone https://github.com/JOZETH-DEV1/SnapTube-2.0.git
    cd SnapTube-2.0
fi

# Instalar librerías de Python
echo "[4/4] Instalando dependencias de Python..."
pip install flask yt-dlp

echo "======================================"
echo "✅ Instalación Completada!"
echo "======================================"
echo "Para arrancar la app, solo escribe esto:"
echo "cd ~/SnapTube-2.0 && python app.py"
echo ""
echo "Luego abre tu navegador en: http://localhost:5000"
