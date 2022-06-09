from pathlib import Path
from pythonforandroid.toolchain import ToolchainCL

def after_apk_build(toolchain: ToolchainCL):
    manifest_file = Path(toolchain._dist.dist_dir) / "src" / "main" / "AndroidManifest.xml"
    old_manifest = manifest_file.read_text(encoding="utf-8")
    new_manifest = old_manifest.replace(
        'android:hardwareAccelerated="true"',
        'android:hardwareAccelerated="true" android:requestLegacyExternalStorage="true"',
    )
    manifest_file.write_text(new_manifest, encoding="utf-8")