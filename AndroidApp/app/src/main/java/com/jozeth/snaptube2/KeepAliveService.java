package com.jozeth.snaptube2;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

public class KeepAliveService extends Service {
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // En Android moderno esto podria requerir un Notification Channel,
        // pero por ahora solo le decimos al OS que este servicio es "STICKY" 
        // para que intente mantener el proceso vivo.
        return START_STICKY;
    }
}