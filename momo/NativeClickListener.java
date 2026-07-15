package com.example.helloworld;

import android.view.View;

/**
 * Importand Bridge between a button's OnClick() function and the native code
 */

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
