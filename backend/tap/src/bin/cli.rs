use std::io::{self, Write};
use std::thread;
use std::time::Duration;

fn main() {
    let address = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "127.0.0.1:4242".to_string());
    let connection = match tap::client::connect(&address) {
        Ok(connection) => connection,
        Err(error) => {
            eprintln!("Could not connect to {address}: {error}");
            std::process::exit(1);
        }
    };

    if let Ok(greeting) = connection.messages.recv_timeout(Duration::from_secs(3)) {
        println!("{greeting}");
    }
    print!("Username: ");
    let _ = io::stdout().flush();
    let mut username = String::new();
    if io::stdin().read_line(&mut username).is_err() {
        return;
    }
    let _ = connection
        .commands
        .send(format!("CONNECT {}", username.trim()));

    let messages = connection.messages;
    thread::spawn(move || {
        for message in messages {
            println!("{message}");
            print!("> ");
            let _ = io::stdout().flush();
        }
    });

    println!("Enter TAP commands. Type QUIT to leave.");
    loop {
        print!("> ");
        let _ = io::stdout().flush();
        let mut input = String::new();
        if io::stdin().read_line(&mut input).is_err() {
            break;
        }
        let command = input.trim();
        if command.is_empty() {
            continue;
        }
        if connection.commands.send(command.to_string()).is_err() {
            break;
        }
        if command.eq_ignore_ascii_case("QUIT") {
            break;
        }
    }
}
