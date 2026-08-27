package com.jozeth.snaptube2;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.os.Binder;
import android.os.Build;
import android.os.IBinder;
import android.support.v4.media.MediaMetadataCompat;
import android.support.v4.media.session.MediaSessionCompat;
import android.support.v4.media.session.PlaybackStateCompat;
import androidx.core.app.NotificationCompat;
import androidx.media.app.NotificationCompat.MediaStyle;

public class WebAudioService extends Service {
    private static final String CHANNEL_ID = "SnapTubeAudioChannel";
    private MediaPlayer mediaPlayer;
    private MediaSessionCompat mediaSession;
    private final IBinder binder = new LocalBinder();
    
    private String currentTitle = "SnapTube";
    private String currentArtist = "Loading...";

    public class LocalBinder extends Binder {
        WebAudioService getService() { return WebAudioService.this; }
    }

    @Override
    public IBinder onBind(Intent intent) { return binder; }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && intent.getAction() != null) {
            String action = intent.getAction();
            if (action.equals("ACTION_NEXT") && MainActivity.instance != null) {
                MainActivity.instance.runOnUiThread(() -> MainActivity.instance.webView.evaluateJavascript("playNextSong();", null));
            } else if (action.equals("ACTION_PREV") && MainActivity.instance != null) {
                MainActivity.instance.runOnUiThread(() -> MainActivity.instance.webView.evaluateJavascript("playPreviousSong();", null));
            } else if (action.equals("ACTION_PAUSE")) {
                pause();
            } else if (action.equals("ACTION_PLAY")) {
                resume();
            }
        }
        androidx.media.session.MediaButtonReceiver.handleIntent(mediaSession, intent);
        return START_STICKY;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        
        // Fix ANR: Must call startForeground immediately
        Intent intent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE);
        androidx.core.app.NotificationCompat.Builder builder = new androidx.core.app.NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("SnapTube")
            .setContentText("Listo para reproducir")
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setContentIntent(pendingIntent);
        startForeground(1, builder.build());
        
        mediaPlayer = new MediaPlayer();
        mediaPlayer.setAudioAttributes(
            new AudioAttributes.Builder()
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .build()
        );
        
        mediaPlayer.setOnCompletionListener(mp -> {
            // Tell MainActivity to play next
            if (MainActivity.instance != null) {
                MainActivity.instance.runOnUiThread(() -> {
                    MainActivity.instance.webView.evaluateJavascript("playNextSong();", null);
                });
            }
        });
        
        mediaPlayer.setOnErrorListener((mp, what, extra) -> {
            System.err.println("MediaPlayer Error: " + what + " " + extra);
            return true; // True indicates we handled the error
        });

        mediaSession = new MediaSessionCompat(this, "WebAudioService");
        mediaSession.setCallback(new MediaSessionCompat.Callback() {
            @Override
            public void onPlay() { resume(); }
            @Override
            public void onPause() { pause(); }
            @Override
            public void onSkipToNext() {
                if (MainActivity.instance != null) {
                    MainActivity.instance.runOnUiThread(() -> MainActivity.instance.webView.evaluateJavascript("playNextSong();", null));
                }
            }
            @Override
            public void onSkipToPrevious() {
                if (MainActivity.instance != null) {
                    MainActivity.instance.runOnUiThread(() -> MainActivity.instance.webView.evaluateJavascript("playPreviousSong();", null));
                }
            }
        });
        mediaSession.setActive(true);
    }

    public void playUrl(String url, String title, String artist) {
        try {
            this.currentTitle = title;
            this.currentArtist = artist;
            mediaPlayer.reset();
            mediaPlayer.setDataSource(url);
            mediaPlayer.prepareAsync();
            mediaPlayer.setOnPreparedListener(mp -> {
                mp.start();
                updateNotification(PlaybackStateCompat.STATE_PLAYING);
            });
        } catch (Exception e) { e.printStackTrace(); }
    }
    
    public void pause() {
        if (mediaPlayer.isPlaying()) {
            mediaPlayer.pause();
            updateNotification(PlaybackStateCompat.STATE_PAUSED);
        }
    }
    
    public void resume() {
        if (!mediaPlayer.isPlaying()) {
            mediaPlayer.start();
            updateNotification(PlaybackStateCompat.STATE_PLAYING);
        }
    }

    private void updateNotification(int state) {
        mediaSession.setPlaybackState(new PlaybackStateCompat.Builder()
            .setActions(PlaybackStateCompat.ACTION_PLAY | PlaybackStateCompat.ACTION_PAUSE | PlaybackStateCompat.ACTION_SKIP_TO_NEXT | PlaybackStateCompat.ACTION_SKIP_TO_PREVIOUS)
            .setState(state, PlaybackStateCompat.PLAYBACK_POSITION_UNKNOWN, 1.0f)
            .build());

        mediaSession.setMetadata(new MediaMetadataCompat.Builder()
            .putString(MediaMetadataCompat.METADATA_KEY_TITLE, currentTitle)
            .putString(MediaMetadataCompat.METADATA_KEY_ARTIST, currentArtist)
            .build());

        Intent intent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE);


        Intent prevIntent = new Intent(this, WebAudioService.class).setAction("ACTION_PREV");
        PendingIntent pPrev = PendingIntent.getService(this, 1, prevIntent, PendingIntent.FLAG_IMMUTABLE);
        
        Intent nextIntent = new Intent(this, WebAudioService.class).setAction("ACTION_NEXT");
        PendingIntent pNext = PendingIntent.getService(this, 2, nextIntent, PendingIntent.FLAG_IMMUTABLE);
        
        Intent playPauseIntent = new Intent(this, WebAudioService.class).setAction(state == PlaybackStateCompat.STATE_PLAYING ? "ACTION_PAUSE" : "ACTION_PLAY");
        PendingIntent pPlayPause = PendingIntent.getService(this, 3, playPauseIntent, PendingIntent.FLAG_IMMUTABLE);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(currentTitle)
            .setContentText(currentArtist)
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setContentIntent(pendingIntent)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .addAction(android.R.drawable.ic_media_previous, "Previous", pPrev)
            .addAction(
                state == PlaybackStateCompat.STATE_PLAYING ? android.R.drawable.ic_media_pause : android.R.drawable.ic_media_play,
                "Play/Pause",
                pPlayPause
            )
            .addAction(android.R.drawable.ic_media_next, "Next", pNext)
            .setStyle(new MediaStyle()
                .setShowActionsInCompactView(0, 1, 2)
                .setMediaSession(mediaSession.getSessionToken()));
            
        startForeground(1, builder.build());
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "SnapTube Audio", NotificationManager.IMPORTANCE_LOW);
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) manager.createNotificationChannel(channel);
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (mediaPlayer != null) { mediaPlayer.release(); mediaPlayer = null; }
        mediaSession.release();
    }
}
