#!/usr/bin/env python3
"""
APK 补丁构建脚本
1. 替换 assets/index.html
2. 打包 pdf.js 本地文件
3. zipalign + apksigner 签名
"""
import sys, os, zipfile, shutil, subprocess

ASSETS = {
    'assets/index.html': 'index.html',
    'assets/pdf.min.mjs': 'pdf.min.mjs',
    'assets/pdf.worker.min.mjs': 'pdf.worker.min.mjs',
    'assets/pdf-lib.min.js': 'pdf-lib.min.js',
}

def find_build_tools():
    for var in ['ANDROID_SDK_ROOT', 'ANDROID_HOME']:
        sdk = os.environ.get(var, '')
        if sdk:
            bt = os.path.join(sdk, 'build-tools')
            if os.path.isdir(bt):
                versions = sorted(os.listdir(bt))
                if versions:
                    return os.path.join(bt, versions[-1])
    return None

def main():
    apk_in = sys.argv[1] if len(sys.argv) > 1 else 'pdf-editor.apk'
    apk_out = sys.argv[2] if len(sys.argv) > 2 else 'pdf-editor-optimized.apk'
    bt_dir = find_build_tools()
    
    # 1. Read original APK (skip META-INF)
    with zipfile.ZipFile(apk_in, 'r') as zin:
        entries = []
        for item in zin.infolist():
            if item.filename.startswith('META-INF/'):
                continue
            entries.append((item, zin.read(item.filename)))
    
    # 2. Write patched APK
    tmp_raw = 'pdf-editor-raw.apk'
    with zipfile.ZipFile(tmp_raw, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item, data in entries:
            if item.filename in ASSETS:
                continue  # Will be added fresh
            # DEX must be stored uncompressed for Android
            if item.filename.endswith('.dex'):
                zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, data)
        for arcname, local in ASSETS.items():
            if os.path.exists(local):
                zout.write(local, arcname, compress_type=zipfile.ZIP_DEFLATED)
                print(f"  + {arcname} ({os.path.getsize(local)} bytes)")
            else:
                print(f"  ! WARNING: {local} not found")
    
    print(f"Raw APK: {os.path.getsize(tmp_raw)} bytes")
    
    # 3. zipalign (BEFORE signing!)
    if bt_dir:
        zipalign = os.path.join(bt_dir, 'zipalign')
        apksigner = os.path.join(bt_dir, 'apksigner')
        tmp_aligned = 'pdf-editor-aligned.apk'
        
        if os.path.exists(zipalign):
            subprocess.run([zipalign, '-f', '-p', '4', tmp_raw, tmp_aligned], check=True)
            print("zipalign OK")
            
            # Verify alignment
            result = subprocess.run([zipalign, '-c', '-p', '4', tmp_aligned],
                                  capture_output=True, text=True)
            if 'Verification succesful' in result.stdout or 'Verification successful' in result.stdout:
                print("Alignment verification: PASS ✅")
            else:
                print("Alignment verification: FAIL ❌")
                print(result.stdout)
                sys.exit(1)
            
            # Generate keystore if needed
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
                print("Keystore generated")
            
            # Sign (v2 only, match original APK)
            subprocess.run([
                apksigner, 'sign',
                '--ks', ks, '--ks-key-alias', 'pdfeditor',
                '--ks-pass', 'pass:android', '--key-pass', 'pass:android',
                '--v1-signing-enabled', 'false',
                '--v2-signing-enabled', 'true',
                '--v3-signing-enabled', 'false',
                '--out', apk_out, tmp_aligned
            ], check=True)
            print("apksigner OK")
            
            # Verify signing
            subprocess.run([apksigner, 'verify', apk_out], check=True)
            print("Signature verification: PASS ✅")
            
            # Cleanup
            os.remove(tmp_raw)
            os.remove(tmp_aligned)
            print(f"\nFinal APK: {apk_out} ({os.path.getsize(apk_out)} bytes)")
        else:
            print("ERROR: zipalign not found")
            sys.exit(1)
    else:
        print("ERROR: Android SDK not found")
        sys.exit(1)

if __name__ == '__main__':
    main()
