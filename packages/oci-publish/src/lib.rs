use oci_client::{client::ClientConfig, secrets::RegistryAuth, Client, Reference};
use oci_wasm::{WasmClient, WasmConfig};
use pyo3::prelude::*;
use std::path::PathBuf;
use tokio;

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(publish, m)?)?;
    Ok(())
}

#[pyfunction]
fn publish(
    skill_path: PathBuf,
    registry: String,
    repository: String,
    skill_name: String,
    tag: String,
    username: String,
    token: String,
) {
    tokio::runtime::Runtime::new().unwrap().block_on(async {
        let repository = format!("{repository}/{skill_name}");
        let image = Reference::with_tag(registry, repository, tag);
        let (config, component_layer) = WasmConfig::from_component(skill_path, None)
            .await
            .expect("Skill must be a valid Wasm component.");
    
        let auth = RegistryAuth::Basic(username, token);
        let client = Client::new(ClientConfig::default());
        let client = WasmClient::new(client);
    
        client
            .push(&image, &auth, component_layer, config, None)
            .await
            .expect("Could not publish skill, please check command arguments.");
    });
}