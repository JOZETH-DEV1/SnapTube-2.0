package com.jozeth.snaptube2;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

public class KeepAliveService extends Service {
    private static final String CHANNEL_ID = "SnapTube2_Channel";
    private static final int NOTIF_ID = 1;

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
    
    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        
        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }
        
        Notification notification = builder
            .setContentTitle("SnapTube 2.0")
            .setContentText("Motor de audio en segundo plano activo")
            .setSmallIcon(android.R.drawable.ic_media_play)
            .build();
            
        startForeground(NOTIF_ID, notification);
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "SnapTube Background Service",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Mantiene la aplicación viva en segundo plano");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }
}
