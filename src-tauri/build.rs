fn main() {
    tauri_build::build();

    // Ensure the sidecar binary is available with the target-triple suffix in
    // the output directory. `tauri_build::build()` copies the sidecar as just
    // `parsec-sidecar`, but at runtime `ShellExt::sidecar()` looks for
    // `parsec-sidecar-{target_triple}`. Bridge the gap by copying (or symlinking).
    let target_triple = std::env::var("TARGET").unwrap();
    let out_dir = std::path::PathBuf::from(std::env::var("OUT_DIR").unwrap());
    // OUT_DIR is deep inside target/debug/build/parsec-xxx/out
    // Walk up to find target/debug/
    let mut target_debug = out_dir.clone();
    while target_debug.file_name().map(|n| n != "debug" && n != "release").unwrap_or(false) {
        target_debug = target_debug.parent().unwrap().to_path_buf();
    }

    let src = target_debug.join("parsec-sidecar");
    let dst = target_debug.join(format!("parsec-sidecar-{target_triple}"));

    if src.exists() && !dst.exists() {
        std::fs::copy(&src, &dst).ok();
        // Preserve executable permission
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            if let Ok(metadata) = std::fs::metadata(&dst) {
                let mut perms = metadata.permissions();
                perms.set_mode(0o755);
                std::fs::set_permissions(&dst, perms).ok();
            }
        }
    }
}
