fn main() {
    let arguments: Vec<String> = std::env::args().collect();
    let world_file = arguments
        .get(1)
        .map(String::as_str)
        .unwrap_or("data/world.json");
    let address = arguments
        .get(2)
        .map(String::as_str)
        .unwrap_or("127.0.0.1:4242");

    if let Err(error) = tap::server::run(address, world_file) {
        tap::logger::error("server_stopped", serde_json::json!({"error": error}));
        std::process::exit(1);
    }
}
