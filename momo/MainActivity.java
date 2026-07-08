package com.example.helloworld;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

public class MainActivity extends Activity {

    // --- native methods ---
    public native void initPython(Object context, String filesDir);
    public native String runScript(String scriptName);

    static {
        System.loadLibrary("python3.14");
        System.loadLibrary("native-lib");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 1. extract assets first
        extractPythonIfNeeded();

        // 2. init python ONCE — passing context + filesDir from Java
        //    TODO FOR ME: never hardcode /data/data/... paths in C
        initPython(getApplicationContext(), getFilesDir().getAbsolutePath());

        // 3. run script and show result
        TextView tv = new TextView(this);
        tv.setTextSize(20f);
        try {
            String result = runScript("main.py");
            tv.setText(result);
        } catch (Exception e) {
            tv.setText("Error: " + e.toString());
        }
        setContentView(tv);
    }


    private void extractPythonIfNeeded() {
        File outDir = new File(getFilesDir(), "python");
        if (outDir.exists() && outDir.list() != null && outDir.list().length > 0) {
            return;
        }
        outDir.mkdirs();
        try {
            copyAssetFolder("python", outDir);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void copyAssetFolder(String assetPath, File outDir) throws Exception {
        String[] list = getAssets().list(assetPath);
        if (list == null || list.length == 0) {
            copyFile(assetPath, new File(outDir, new File(assetPath).getName()));
            return;
        }
        outDir.mkdirs();
        for (String child : list) {
            String childAssetPath = assetPath + "/" + child;
            File childOutDir = new File(outDir, child);
            String[] sub = getAssets().list(childAssetPath);
            if (sub != null && sub.length > 0) {
                copyAssetFolder(childAssetPath, childOutDir);
            } else {
                copyFile(childAssetPath, childOutDir);
            }
        }
    }

    private void copyFile(String assetPath, File outFile) throws Exception {
        outFile.getParentFile().mkdirs();
        InputStream in = getAssets().open(assetPath);
        FileOutputStream out = new FileOutputStream(outFile);
        byte[] buf = new byte[4096];
        int len;
        while ((len = in.read(buf)) != -1) {
            out.write(buf, 0, len);
        }
        in.close();
        out.close();
    }
}

