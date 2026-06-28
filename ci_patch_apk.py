#!/usr/bin/env python3
"""Patch APK: replace assets, zipalign, sign."""
import sys, os, zipfile, shutil, subprocess

ASSETS = {
    'assets/index.html': 'index.html',
    'assets/pdf.min.mjs': 'pdf.min.mjs',
    'assets/pdf.worker.min.mjs': 'pdf.worker.min.mjs',
    'assets/pdf-lib.min.js': 'pdf-lib.min.js',
}

def main():
    apk_in = sys.argv[1] if len(sys.argv) > 1 else 'pdf-editor.apk'
    apk_out = sys.argv[2] if len(sys.argv) > 2 else 'pdf-editor-optimized.apk'
    
    # Find build tools
    sdk_root = os.environ.get('ANDROID_SDK_ROOT') or os.environ.get('ANDROID_HOME') or ''
    bt_dir = None
    if sdk_root:
        d = os.path.join(sdk_root, 'build-tools')
        if os.path.isdir(d):
            vs = sorted(os.listdir(d))
            if vs: bt_dir = os.path.join(d, vs[-1])
    
    # Read original, skip META-INF
    with zipfile.ZipFile(apk_in, 'r') as zin:
        entries = [(item, zin.read(item.filename)) for item in zin.infolist()
                   if not item.filename.startswith('META-INF/')]
    
    # Write patched
    tmp = 'pdf-editor-tmp.apk'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item, data in entries:
            if item.filename in ASSETS: continue
            if item.filename.endswith('.dex'):
                zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, data)
        for arc, local in ASSETS.items():
            if os.path.exists(local):
                print(f"  + {arc} ({os.path.getsize(local)} bytes)")
                zout.write(local, arc, zipfile.ZIP_DEFLATED)
    
    # zipalign + sign
    if bt_dir:
        zalign = os.path.join(bt_dir, 'zipalign')
        signer = os.path.join(bt_dir, 'apksigner')
        aligned = 'pdf-editor-aligned.apk'
        
        if os.path.exists(zalign):
            subprocess.run([zalign, '-f', '-p', '4', tmp, aligned], check=True)
        if os.path.exists(signer):
            ks = 'build.keystore'
            if not os.path.exists(ks):
                subprocess.run(['keytool', '-genkey', '-v', '-noprompt',
                    '-alias', 'pdfeditor', '-keyalg', 'RSA', '-keysize', '2048',
                    '-validity', '10000', '-keystore', ks,
                    '-storepass', 'android', '-keypass', 'android',
                    '-dname', 'CN=PDFEditor,O=PDFEditor,C=CN'], check=True)
            subprocess.run([signer, 'sign', '--ks', ks, '--ks-key-alias', 'pdfeditor',
                '--ks-pass', 'pass:android', '--key-pass', 'pass:android',
                '--v1-signing-enabled', 'false', '--v2-signing-enabled', 'true',
                '--v3-signing-enabled', 'false', '--out', apk_out, aligned], check=True)
            subprocess.run([signer, 'verify', apk_out], check=True)
            print(f"Done: {apk_out} ({os.path.getsize(apk_out)} bytes)")
        
        for f in [tmp, aligned]: 
            if os.path.exists(f): os.remove(f)
    else:
        shutil.move(tmp, apk_out)

if __name__ == '__main__':
    main()
