fn main() {
    println!("cargo:rerun-if-env-changed=MUJOCO_DIR");
    println!("cargo:rerun-if-changed=examples/xl330_mujoco_plant.c");
    println!("cargo:rerun-if-changed=examples/xl330_mujoco_plant.h");
    if std::env::var("CARGO_FEATURE_MUJOCO_PLANT").is_err() {
        return;
    }
    let dir = std::env::var("MUJOCO_DIR").unwrap_or_else(|_| {
        "/home/ubuntu/.local/lib/python3.12/site-packages/mujoco".to_string()
    });
    let include = format!("{dir}/include");
    let header = format!("{include}/mujoco/mujoco.h");
    let lib = format!("{dir}/libmujoco.so.3.3.7");
    if !std::path::Path::new(&header).is_file() || !std::path::Path::new(&lib).is_file() {
        panic!(
            "mujoco-plant needs MUJOCO_DIR with include/mujoco/mujoco.h and libmujoco.so.3.3.7 (looked in {dir})"
        );
    }
    cc::Build::new()
        .file("examples/xl330_mujoco_plant.c")
        .include(&include)
        .include("examples")
        .flag("-std=c11")
        .compile("xl330_mujoco_plant");
    println!("cargo:rustc-link-search=native={dir}");
    println!("cargo:rustc-link-arg=-Wl,-rpath,{dir}");
    println!("cargo:rustc-link-arg=-l:libmujoco.so.3.3.7");
}
