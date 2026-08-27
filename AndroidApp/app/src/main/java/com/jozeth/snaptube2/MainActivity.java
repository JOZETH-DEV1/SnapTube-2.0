package com.jozeth.snaptube2;

import android.annotation.SuppressLint;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    public WebView webView;
    public static MainActivity instance;
    private WebAudioService audioService;
    private boolean isBound = false;

    private ServiceConnection connection = new ServiceConnection() {
        @Override
        public void onServiceConnected(ComponentName className, IBinder service) {
            WebAudioService.LocalBinder binder = (WebAudioService.LocalBinder) service;
            audioService = binder.getService();
            isBound = true;
        }
        @Override
        public void onServiceDisconnected(ComponentName arg0) {
            isBound = false;
        }
    };

    class WebAppInterface {
        Context mContext;
        WebAppInterface(Context c) { mContext = c; }
        
        @JavascriptInterface
        public void playAudio(String url, String title, String artist) {
            if (isBound && audioService != null) {
                audioService.playUrl(url, title, artist);
            }
        }
        
        @JavascriptInterface
        public void pauseAudio() {
            if (isBound && audioService != null) audioService.pause();
        }
        
        @JavascriptInterface
        public void resumeAudio() {
            if (isBound && audioService != null) audioService.resume();
        }
    }

    @SuppressLint({"SetJavaScriptEnabled"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        instance = this;
        
        webView = new WebView(this);
        setContentView(webView);
        
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setMediaPlaybackRequiresUserGesture(false);
        
        webView.addJavascriptInterface(new WebAppInterface(this), "AndroidNative");
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());
        
        webView.loadUrl("http://127.0.0.1:5000");
        
        Intent intent = new Intent(this, WebAudioService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent);
        } else {
            startService(intent);
        }
        bindService(intent, connection, Context.BIND_AUTO_CREATE);
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (isBound) {
            unbindService(connection);
            isBound = false;
        }
        instance = null;
    }
    
    @Override
    public void onBackPressed() {
        // Enviar señal al Javascript para ver si puede "ir atrás" en la UI de una sola página
        webView.evaluateJavascript("if (typeof goBackUI === 'function') { goBackUI(); } else { 'NO_HANDLER'; }", value -> {
            if ("\"NO_HANDLER\"".equals(value) || "\"CANNOT_GO_BACK\"".equals(value) || "null".equals(value)) {
                // Si estamos en la raíz, simplemente mandar la app a segundo plano sin destruirla
                moveTaskToBack(true);
            }
        });
    }
}
