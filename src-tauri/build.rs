fn main() {
    // Before tauri_build::build() runs, ensure the correct sidecar binary
    // is in binaries/ with the target-triple suffix.
    //
    // Release builds (cargo tauri build): copy the real PyInstaller binary
    // so Tauri bundles the actual executable with _internal/.
    //
    // Dev builds (cargo tauri dev): leave the shell wrapper in place — it
    // resolves to the PyInstaller output or falls back to venv Python.
    let target_triple = std::env::var("TARGET").unwrap();
    let profile = std::env::var("PROFILE").unwrap_or_default();
    let manifest_dir = std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let binaries_dir = manifest_dir.join("binaries");

    // On Windows targets, both the PyInstaller output and the Tauri sidecar
    // name need the .exe extension.
    let exe_suffix = if target_triple.contains("windows") {
        ".exe"
    } else {
        ""
    };

    let pyinstaller_binary = manifest_dir
        .parent()
        .unwrap()
        .join(format!("backend/dist/parsec-sidecar/parsec-sidecar{exe_suffix}"));

    let sidecar_with_triple =
        binaries_dir.join(format!("parsec-sidecar-{target_triple}{exe_suffix}"));

    if profile == "release" && pyinstaller_binary.exists() {
        // Production build: copy the real PyInstaller binary
        println!(
            "cargo:warning=Bundling PyInstaller binary: {}",
            pyinstaller_binary.display()
        );
        std::fs::copy(&pyinstaller_binary, &sidecar_with_triple)
            .expect("Failed to copy PyInstaller binary to binaries/");

        // Ensure executable permission
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            if let Ok(metadata) = std::fs::metadata(&sidecar_with_triple) {
                let mut perms = metadata.permissions();
                perms.set_mode(0o755);
                std::fs::set_permissions(&sidecar_with_triple, perms).ok();
            }
        }
    } else if profile == "release" && !pyinstaller_binary.exists() {
        println!(
            "cargo:warning=PyInstaller binary not found at {}. Run ./backend/build_sidecar.sh first.",
            pyinstaller_binary.display()
        );
    }
    // Dev mode: do nothing — the committed shell wrapper is already named
    // parsec-sidecar-aarch64-apple-darwin and works as-is.

    // Tell Cargo to re-run if the PyInstaller binary or binaries dir changes
    println!(
        "cargo:rerun-if-changed={}",
        pyinstaller_binary.display()
    );
    println!("cargo:rerun-if-changed=binaries/");

    tauri_build::build();
}
