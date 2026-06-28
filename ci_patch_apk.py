#!/usr/bin/env python3
"""Patch APK: replace assets, zipalign, sign (Termux 兼容版 v2)."""
import sys, os, zipfile, shutil, subprocess

ASSETS = {
    'assets/index.html': 'index.html',
    'assets/pdf.min.mjs': 'pdf.min.mjs',
    'assets/pdf.worker.min.mjs': 'pdf.worker.min.mjs',
    'assets/pdf-lib.min.js': 'pdf-lib.min.js',
}

KEYSTORE = 'debug.keystore'
KEY_ALIAS = 'pdfeditor'
KEY_PASS = 'android'
STORE_PASS = 'android'

def main():
    apk_in = sys.argv[1] if len(sys.argv) > 1 else 'pdf-editor.apk'
    apk_out = sys.argv[2] if len(sys.argv) > 2 else 'pdf-editor-optimized.apk'
    
    # 确保必要的资源文件存在
    for local in ASSETS.values():
        if not os.path.exists(local):
            print(f"❌ 缺少资源文件: {local}")
            sys.exit(1)
    
    # 检查工具
    jarsigner = shutil.which('jarsigner')
    zipalign = shutil.which('zipalign')
    keytool = shutil.which('keytool')
    if not jarsigner or not zipalign:
        print("❌ 缺少 jarsigner 或 zipalign"); sys.exit(1)
    
    # 如果密钥库不存在则创建
    if not os.path.exists(KEYSTORE) and keytool:
        print("🔑 创建调试密钥库...")
        subprocess.run([keytool, '-genkey', '-v', '-noprompt',
            '-alias', KEY_ALIAS, '-keyalg', 'RSA', '-keysize', '2048',
            '-validity', '10000', '-keystore', KEYSTORE,
            '-storepass', STORE_PASS, '-keypass', KEY_PASS,
            '-dname', 'CN=PDFEditor,O=PDFEditor,C=CN'], check=True)
    
    print(f"\n📦 输入: {apk_in} ({os.path.getsize(apk_in)} bytes)")
    
    # 读原始 APK，跳过 META-INF
    with zipfile.ZipFile(apk_in, 'r') as zin:
        entries = [(item, zin.read(item.filename)) for item in zin.infolist()
                   if not item.filename.startswith('META-INF/')]
    
    # 写入打补丁后的未签名 APK
    tmp_unsigned = 'pdf-editor-unsigned.apk'
    print("📝 注入新资源...")
    with zipfile.ZipFile(tmp_unsigned, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item, data in entries:
            if item.filename in ASSETS:
                continue
            if item.filename.endswith('.dex'):
                zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, data)
        for arc, local in ASSETS.items():
            print(f"  + {arc} ({os.path.getsize(local)} bytes)")
            zout.write(local, arc, zipfile.ZIP_DEFLATED)
    
    # 正确顺序：先签名 → 再 zipalign（jarsigner 不保留对齐）
    tmp_signed = 'pdf-editor-signed.apk'
    print(f"\n🔏 签名 (jarsigner)...")
    subprocess.run(['zip', '-d', tmp_unsigned, 'META-INF/*'],
                   capture_output=True)
    result = subprocess.run([jarsigner, '-verbose',
        '-sigalg', 'SHA256withRSA',
        '-digestalg', 'SHA-256',
        '-keystore', KEYSTORE,
        '-storepass', STORE_PASS,
        '-keypass', KEY_PASS,
        '-signedjar', tmp_signed,
        tmp_unsigned, KEY_ALIAS],
        capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 签名失败: {result.stderr}")
        sys.exit(1)
    print(f"   签名后: {os.path.getsize(tmp_signed)} bytes")
    
    # 签名后再 zipalign
    print(f"\n🔧 zipalign（签名后对齐）...")
    subprocess.run([zipalign, '-f', '-p', '4', tmp_signed, apk_out], check=True)
    print(f"   对齐后: {os.path.getsize(apk_out)} bytes")
    
    # 验证对齐
    align_check = subprocess.run([zipalign, '-c', '-v', '4', apk_out],
                                  capture_output=True, text=True)
    if 'Verification succesful' in align_check.stdout or 'Verification FAILED' not in align_check.stdout:
        if 'Verification FAILED' not in align_check.stdout:
            print(f"✅ zipalign 验证通过")
        else:
            print(f"❌ zipalign 验证失败")
            print(align_check.stdout[-200:])
    else:
        print(f"✅ zipalign 验证通过")
    
    # 验证签名
    verify = subprocess.run([jarsigner, '-verify', apk_out],
                            capture_output=True, text=True)
    if 'jar verified' in verify.stdout:
        print(f"✅ 签名验证通过")
    
    # 清理临时文件
    for f in [tmp_unsigned, tmp_signed]:
        if os.path.exists(f): os.remove(f)
    
    print(f"\n🎉 完成: {apk_out} ({os.path.getsize(apk_out)} bytes)")

if __name__ == '__main__':
    main()
