package com.ross.floatbutton;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.IBinder;
import android.view.Gravity;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;

public class FloatingService extends Service {
    private WindowManager windowManager;
    private View floatingView;
    private WindowManager.LayoutParams params;
    private static final String CHANNEL_ID = "FloatingServiceChannel";

    private String getPrefSuffix() {
        return getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE
                ? "_landscape"
                : "_portrait";
    }

    private void savePosition() {
        SharedPreferences prefs = getSharedPreferences("FloatingButtonPrefs", MODE_PRIVATE);
        String suffix = getPrefSuffix();
        prefs.edit()
                .putInt("x" + suffix, params.x)
                .putInt("y" + suffix, params.y)
                .apply();
    }

    private void updatePositionFromPrefs() {
        SharedPreferences prefs = getSharedPreferences("FloatingButtonPrefs", MODE_PRIVATE);
        String suffix = getPrefSuffix();
        params.x = prefs.getInt("x" + suffix, prefs.getInt("x", 100));
        params.y = prefs.getInt("y" + suffix, prefs.getInt("y", 100));
        windowManager.updateViewLayout(floatingView, params);
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        updatePositionFromPrefs();
    }

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
        floatingView = new View(this);
        floatingView.setHapticFeedbackEnabled(true);

        GradientDrawable shape = new GradientDrawable();
        shape.setShape(GradientDrawable.OVAL);
        shape.setColor(0x8000FF00);
        floatingView.setBackground(shape);

        int layoutType = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;

        params = new WindowManager.LayoutParams(
                150, 150, layoutType,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);

        params.gravity = Gravity.TOP | Gravity.LEFT;

        SharedPreferences prefs = getSharedPreferences("FloatingButtonPrefs", MODE_PRIVATE);
        String suffix = getPrefSuffix();
        params.x = prefs.getInt("x" + suffix, prefs.getInt("x", 100));
        params.y = prefs.getInt("y" + suffix, prefs.getInt("y", 100));

        floatingView.setOnTouchListener(new View.OnTouchListener() {
            private int initialX, initialY;
            private float initialTouchX, initialTouchY;
            private static final int CLICK_THRESHOLD = 10;
            private static final int LONG_PRESS_TIMEOUT = 500;
            private final android.os.Handler longPressHandler = new android.os.Handler(android.os.Looper.getMainLooper());
            private boolean isLongPressed = false;

            private final Runnable longPressRunnable = () -> {
                isLongPressed = true;
                floatingView.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
                runTermuxCommand("on_float_button_long_press.sh", true);
            };

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        isLongPressed = false;
                        longPressHandler.postDelayed(longPressRunnable, LONG_PRESS_TIMEOUT);
                        v.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);
                        initialX = params.x;
                        initialY = params.y;
                        initialTouchX = event.getRawX();
                        initialTouchY = event.getRawY();
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        float dX = Math.abs(event.getRawX() - initialTouchX);
                        float dY = Math.abs(event.getRawY() - initialTouchY);
                        if (dX > CLICK_THRESHOLD || dY > CLICK_THRESHOLD) {
                            if (!isLongPressed) {
                                longPressHandler.removeCallbacks(longPressRunnable);
                            }
                            params.x = initialX + (int) (event.getRawX() - initialTouchX);
                            params.y = initialY + (int) (event.getRawY() - initialTouchY);
                            windowManager.updateViewLayout(floatingView, params);
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        longPressHandler.removeCallbacks(longPressRunnable);
                        if (isLongPressed) {
                            savePositionToEdge();
                            return true;
                        }
                        float deltaX = Math.abs(event.getRawX() - initialTouchX);
                        float deltaY = Math.abs(event.getRawY() - initialTouchY);
                        if (deltaX < CLICK_THRESHOLD && deltaY < CLICK_THRESHOLD) {
                            runTermuxCommand("on_float_button_click.sh", true);
                        } else {
                            savePositionToEdge();
                        }
                        return true;
                }
                return false;
            }

            private void savePositionToEdge() {
                int screenWidth = windowManager.getDefaultDisplay().getWidth();
                int viewWidth = floatingView.getWidth();
                int targetX = (params.x + viewWidth / 2 < screenWidth / 2) ? 0 : screenWidth - viewWidth;

                ValueAnimator animator = ValueAnimator.ofInt(params.x, targetX);
                animator.setDuration(200);
                animator.addUpdateListener(animation -> {
                    params.x = (int) animation.getAnimatedValue();
                    windowManager.updateViewLayout(floatingView, params);
                });
                animator.addListener(new AnimatorListenerAdapter() {
                    @Override
                    public void onAnimationEnd(Animator animation) {
                        savePosition();
                    }
                });
                animator.start();
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

    private void runTermuxCommand(String scriptName, boolean background) {
        // https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent#Setup-Instructions
        Intent intent = new Intent();
        intent.setClassName("com.termux", "com.termux.app.RunCommandService");
        intent.setAction("com.termux.RUN_COMMAND");
        intent.putExtra("com.termux.RUN_COMMAND_PATH", "/data/data/com.termux/files/usr/bin/bash");
        intent.putExtra("com.termux.RUN_COMMAND_ARGUMENTS",
                new String[] {
                        "/data/data/com.termux/files/home/MyScripts/scripts/r/android/termux/" + scriptName });
        intent.putExtra("com.termux.RUN_COMMAND_WORKDIR", "/data/data/com.termux/files/home");
        intent.putExtra("com.termux.RUN_COMMAND_BACKGROUND", background);
        // https://github.com/termux/termux-app/blob/master/termux-shared/src/main/java/com/termux/shared/termux/TermuxConstants.java
        final String VALUE_EXTRA_SESSION_ACTION_SWITCH_TO_NEW_SESSION_AND_OPEN_ACTIVITY = "0";
        final String VALUE_EXTRA_SESSION_ACTION_RUN_IN_BACKGROUND = "2";
        intent.putExtra("com.termux.RUN_COMMAND_SESSION_ACTION", background
                ? VALUE_EXTRA_SESSION_ACTION_RUN_IN_BACKGROUND
                : VALUE_EXTRA_SESSION_ACTION_SWITCH_TO_NEW_SESSION_AND_OPEN_ACTIVITY);
        try {
            startService(intent);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (floatingView != null)
            windowManager.removeView(floatingView);
    }
}
