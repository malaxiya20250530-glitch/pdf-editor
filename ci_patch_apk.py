#!/usr/bin/env python3
"""Patch APK: replace assets/index.html, add bundled pdf.js, re-sign."""
import sys, os, zipfile, shutil, subprocess, struct

def main():
    apk_src = sys.argv[1] if len(sys.argv) > 1 else 'pdf-editor.apk'
    apk_out = sys.argv[2] if len(sys.argv) > 2 else 'pdf-editor-optimized.apk'

    # 1. Copy APK
    shutil.copy(apk_src, 'pdf-editor-tmp.apk')
    
    # 2. Replace assets using Python zipfile
    assets_to_add = {
        'assets/index.html': 'index.html',
        'assets/pdf.min.mjs': 'pdf.min.mjs', 
        'assets/pdf.worker.min.mjs': 'pdf.worker.min.mjs',
        'assets/pdf-lib.min.js': 'pdf-lib.min.js',
    }
    
    tmp_apk = 'pdf-editor-tmp.apk'
    
    # Read original APK
    with zipfile.ZipFile(tmp_apk, 'r') as zin:
        entries = []
        for item in zin.infolist():
            if item.filename.startswith('META-INF/'):
                continue  # Skip old signatures
            entries.append((item, zin.read(item.filename)))
    
    # Write new APK
    with zipfile.ZipFile(apk_out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item, data in entries:
            # Check if this is an asset we're replacing
            if item.filename in assets_to_add:
                continue  # Will be added fresh
            # Preserve DEX uncompressed
            if item.filename in ('classes.dex', 'classes2.dex', 'classes3.dex'):
                zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, data)
        
        # Add new/updated assets
        for arcname, local_path in assets_to_add.items():
            if os.path.exists(local_path):
                print(f"Adding {arcname} ({os.path.getsize(local_path)} bytes)")
                zout.write(local_path, arcname, compress_type=zipfile.ZIP_DEFLATED)
            else:
                print(f"WARNING: {local_path} not found, skipping")
    
    os.remove(tmp_apk)
    print(f"APK created: {apk_out} ({os.path.getsize(apk_out)} bytes)")
    
    # 3. zipalign
    sdk_root = os.environ.get('ANDROID_SDK_ROOT', os.environ.get('ANDROID_HOME', ''))
    build_tools = None
    if sdk_root:
        bt_dir = os.path.join(sdk_root, 'build-tools')
        if os.path.isdir(bt_dir):
            versions = sorted(os.listdir(bt_dir))
            if versions:
                build_tools = os.path.join(bt_dir, versions[-1])
    
    if build_tools:
        zipalign = os.path.join(build_tools, 'zipalign')
        apksigner = os.path.join(build_tools, 'apksigner')
        aligned_apk = 'pdf-editor-aligned-tmp.apk'
        
        if os.path.exists(zipalign):
            subprocess.run([zipalign, '-f', '-p', '4', apk_out, aligned_apk], check=True)
            shutil.move(aligned_apk, apk_out)
            print("zipalign done")
        
        if os.path.exists(apksigner):
            # Generate keystore
            ks = 'build.keystore'
            if not os.path.exists(ks):
                subprocess.run([
                    'keytool', '-genkey', '-v', '-noprompt',
                    '-alias', 'pdfeditor',
                    '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
                    '-keystore', ks,
                    '-storepass', 'android', '-keypass', 'android',
                    '-dname', 'CN=PDF Editor, OU=Dev, O=PDFEditor, L=Unknown, ST=Unknown, C=CN'
                ], check=True)
            
            signed_apk = 'pdf-editor-signed-tmp.apk'
            subprocess.run([
                apksigner, 'sign',
                '--ks', ks,
                '--ks-key-alias', 'pdfeditor',
                '--ks-pass', 'pass:android',
                '--key-pass', 'pass:android',
                '--out', signed_apk,
                apk_out
            ], check=True)
            shutil.move(signed_apk, apk_out)
            print("apksigner sign done")
            
            subprocess.run([apksigner, 'verify', '--verbose', apk_out], check=True)
        else:
            print("WARNING: apksigner not found, APK not signed")
    else:
        print("WARNING: Android SDK not found, APK not aligned/signed")
    
    print(f"Final APK: {apk_out} ({os.path.getsize(apk_out)} bytes)")

if __name__ == '__main__':
    main()
