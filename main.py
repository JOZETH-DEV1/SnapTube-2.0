import flet as ft
import yt_dlp
import os
import threading
import traceback

DOWNLOAD_DIR = "/storage/emulated/0/Download/Musica"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def main(page: ft.Page):
    try:
        # Forzar modo landscape
        page.set_allowed_device_orientations([
            ft.DeviceOrientation.LANDSCAPE_LEFT,
            ft.DeviceOrientation.LANDSCAPE_RIGHT
        ])

        page.title = "Snaptube Local"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 20
        page.scroll = "adaptive"

        search_input = ft.TextField(hint_text="Buscar cancion o artista...", expand=True, border_radius=20)
        results_column = ft.Column(scroll="adaptive", spacing=10)

        # Para guardar las tareas de descarga
        active_downloads = {}

        def show_warning(e):
            dlg = ft.AlertDialog(
                title=ft.Text("Advertencia Legal"),
                content=ft.Text("Los videos descargados son solo para uso personal. Queda estrictamente prohibido resubirlos o distribuirlos."),
                actions=[ft.TextButton("Entendido", on_click=lambda e: close_dlg(dlg))],
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        def close_dlg(dlg):
            dlg.open = False
            page.update()

        def download_video(video_id, url, title, format_type):
            progress_bar = active_downloads[video_id]['progress']
            status_text = active_downloads[video_id]['status']
            
            class MyLogger:
                def debug(self, msg):
                    if "[download]" in msg and "%" in msg:
                        try:
                            pct_str = msg.split("%")[0].split()[-1]
                            pct = float(pct_str)
                            progress_bar.value = pct / 100
                            status_text.value = f"Descargando: {pct}%"
                            page.update()
                        except: pass
                def warning(self, msg): pass
                def error(self, msg): pass

            if format_type == "audio":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
                    'logger': MyLogger()
                }
            else:
                ydl_opts = {
                    'format': 'bestvideo[height<=720]+bestaudio/best',
                    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                    'merge_output_format': 'mp4',
                    'logger': MyLogger()
                }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                status_text.value = "Descarga completada!"
                status_text.color = ft.Colors.GREEN
            except Exception as e:
                status_text.value = "Error en la descarga"
                status_text.color = ft.Colors.RED
            
            page.update()

        def start_download(video_id, url, title, format_type):
            threading.Thread(target=download_video, args=(video_id, url, title, format_type)).start()
            show_warning(None)

        def on_search(e):
            if not search_input.value: return
            
            results_column.controls.clear()
            results_column.controls.append(ft.ProgressRing())
            page.update()

            ydl_opts = {'format': 'bestaudio/best', 'extract_flat': True, 'quiet': True}
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(f"ytsearch15:{search_input.value}", download=False)
                    
                results_column.controls.clear()
                
                for entry in result['entries']:
                    vid_id = entry.get('id')
                    url = entry.get('url')
                    title = entry.get('title')
                    channel = entry.get('uploader')
                    thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                    prog_bar = ft.ProgressBar(value=0, visible=True)
                    stat_text = ft.Text("", size=12, color=ft.Colors.PINK)
                    active_downloads[vid_id] = {'progress': prog_bar, 'status': stat_text}

                    card = ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Row([
                                    ft.Image(src=thumb, width=100, height=75, fit=ft.ImageFit.COVER, border_radius=10),
                                    ft.Column([
                                        ft.Text(title, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, width=200),
                                        ft.Text(channel, size=12, color=ft.Colors.GREY_400),
                                    ])
                                ]),
                                ft.Row([
                                    ft.ElevatedButton("MP3", icon="music_note", on_click=lambda e, i=vid_id, u=url, t=title: start_download(i, u, t, "audio")),
                                    ft.ElevatedButton("MP4", icon="video_file", on_click=lambda e, i=vid_id, u=url, t=title: start_download(i, u, t, "video")),
                                ]),
                                prog_bar,
                                stat_text
                            ])
                        )
                    )
                    results_column.controls.append(card)
            except Exception as ex:
                results_column.controls.clear()
                results_column.controls.append(ft.Text("Error al buscar. Verifica tu internet.", color=ft.Colors.RED))
            
            page.update()

        search_btn = ft.IconButton(icon="search", on_click=on_search, icon_color=ft.Colors.PINK)
        
        header = ft.Row([
            ft.Icon("library_music", color=ft.Colors.PINK, size=30),
            ft.Text("Snaptube Local", size=24, weight=ft.FontWeight.BOLD)
        ], alignment=ft.MainAxisAlignment.CENTER)

        page.add(
            header,
            ft.Row([search_input, search_btn]),
            results_column
        )

    except Exception as e:
        page.add(ft.Text(f"CRASH: {traceback.format_exc()}", color=ft.Colors.RED, size=12))

ft.app(target=main)
