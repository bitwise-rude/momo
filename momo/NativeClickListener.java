package com.example.helloworld;

import android.view.View;

// Bridges the button click python -> java
public class NativeClickListener implements View.OnClickListener {
    private final int handle;

    public NativeClickListener(int handle) {
        this.handle = handle;
    }

    @Override
    public void onClick(View v) {
        nativeOnClick(handle);
    }

    private native void nativeOnClick(int handle);
}
