package com.ross.floatbutton;

import android.animation.ValueAnimator;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;

public class FloatingService extends Service {
    private WindowManager windowManager;
    private View floatingView;
    private LinearLayout menuView;
    private boolean isMenuOpen = false;
    private static final String CHANNEL_ID = "FloatingServiceChannel";

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        // All foreground services are required to show a persistent notification.
        Notification notification = new Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("Floating Button")
                .setContentText("Service is running")
                .setSmallIcon(android.R.drawable.ic_menu_mylocation)
                .build();
        startForeground(1, notification);

        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        floatingView = new ImageView(this);

        GradientDrawable shape = new GradientDrawable();
        shape.setShape(GradientDrawable.OVAL);
        shape.setColor(0x80FFFFFF);
        floatingView.setBackground(shape);

        int layoutType = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;

        final WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                150, 150, layoutType,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);

        params.gravity = Gravity.TOP | Gravity.LEFT;

        final SharedPreferences prefs = getSharedPreferences("FloatingButtonPrefs", MODE_PRIVATE);
        params.x = prefs.getInt("x", 100);
        params.y = prefs.getInt("y", 100);

        floatingView.setOnTouchListener(new View.OnTouchListener() {
            private int initialX, initialY;
            private float initialTouchX, initialTouchY;
            private static final int CLICK_THRESHOLD = 10;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialX = params.x;
                        initialY = params.y;
                        initialTouchX = event.getRawX();
                        initialTouchY = event.getRawY();
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        float dX = Math.abs(event.getRawX() - initialTouchX);
                        float dY = Math.abs(event.getRawY() - initialTouchY);
                        if (dX > CLICK_THRESHOLD || dY > CLICK_THRESHOLD) {
                            if (isMenuOpen) closeMenu();
                            params.x = initialX + (int) (event.getRawX() - initialTouchX);
                            params.y = initialY + (int) (event.getRawY() - initialTouchY);
                            windowManager.updateViewLayout(floatingView, params);
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        float deltaX = Math.abs(event.getRawX() - initialTouchX);
                        float deltaY = Math.abs(event.getRawY() - initialTouchY);
                        if (deltaX < CLICK_THRESHOLD && deltaY < CLICK_THRESHOLD) {
                            toggleMenu();
                        } else {
                            int screenWidth = windowManager.getDefaultDisplay().getWidth();
                            int viewWidth = floatingView.getWidth();
                            int targetX = (params.x + viewWidth / 2 < screenWidth / 2) ? 0 : screenWidth - viewWidth;

                            ValueAnimator animator = ValueAnimator.ofInt(params.x, targetX);
                            animator.setDuration(200);
                            animator.addUpdateListener(animation -> {
                                params.x = (int) animation.getAnimatedValue();
                                windowManager.updateViewLayout(floatingView, params);
                                prefs.edit().putInt("x", params.x).putInt("y", params.y).apply();
                            });
                            animator.start();
                        }
                        return true;
                }
                return false;
            }
        });

        windowManager.addView(floatingView, params);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Ensures the service restarts automatically if killed by the system.
        return START_STICKY;
    }

    private void createNotificationChannel() {
        NotificationChannel serviceChannel = new NotificationChannel(
                CHANNEL_ID,
                "Floating Service Channel",
                NotificationManager.IMPORTANCE_LOW);
        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.createNotificationChannel(serviceChannel);
    }

    private void toggleMenu() {
        if (isMenuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    private void openMenu() {
        if (menuView != null) return;

        menuView = new LinearLayout(this);
        menuView.setOrientation(LinearLayout.VERTICAL);
        menuView.setBackgroundColor(Color.parseColor("#CC000000"));
        menuView.setPadding(20, 20, 20, 20);

        Button btn1 = new Button(this);
        btn1.setText("Dump UI");
        btn1.setOnClickListener(v -> {
            runTermuxCommand("dump_ui.sh");
            closeMenu();
        });
        menuView.addView(btn1);

        Button btn2 = new Button(this);
        btn2.setText("Voice Input");
        btn2.setOnClickListener(v -> {
            runTermuxCommand("voice_input.sh");
            closeMenu();
        });
        menuView.addView(btn2);

        WindowManager.LayoutParams floatParams = (WindowManager.LayoutParams) floatingView.getLayoutParams();

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);

        params.gravity = Gravity.TOP | Gravity.LEFT;
        params.x = floatParams.x;
        params.y = floatParams.y + floatingView.getHeight();

        windowManager.addView(menuView, params);
        isMenuOpen = true;
    }

    private void closeMenu() {
        if (menuView != null) {
            windowManager.removeView(menuView);
            menuView = null;
            isMenuOpen = false;
        }
    }

    private void runTermuxCommand(String scriptName) {
        // https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent#Setup-Instructions
        Intent intent = new Intent();
        intent.setClassName("com.termux", "com.termux.app.RunCommandService");
        intent.setAction("com.termux.RUN_COMMAND");
        intent.putExtra("com.termux.RUN_COMMAND_PATH", "/data/data/com.termux/files/usr/bin/bash");
        intent.putExtra("com.termux.RUN_COMMAND_ARGUMENTS",
                new String[] {
                        "/data/data/com.termux/files/home/MyScripts/scripts/r/android/termux/" + scriptName });
        intent.putExtra("com.termux.RUN_COMMAND_WORKDIR", "/data/data/com.termux/files/home");
        intent.putExtra("com.termux.RUN_COMMAND_BACKGROUND", false);
        intent.putExtra("com.termux.RUN_COMMAND_SESSION_ACTION", "2"); // VALUE_EXTRA_SESSION_ACTION_SWITCH_TO_NEW_SESSION_AND_DONT_OPEN_ACTIVITY
        try {
            startService(intent);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        closeMenu();
        if (floatingView != null)
            windowManager.removeView(floatingView);
    }
}
