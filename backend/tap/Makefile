.PHONY: install build run-server run-client run-client-gui lint clean

install:
	cargo fetch

build:
	cargo build --all-targets --features gui

run-server:
	cargo run --bin server -- data/world.json 127.0.0.1:4242

run-client:
	cargo run --bin cli -- 127.0.0.1:4242

run-client-gui:
	cargo run --features gui --bin gui

lint:
	cargo fmt --check
	cargo clippy --all-targets --all-features -- -D warnings

clean:
	cargo clean
