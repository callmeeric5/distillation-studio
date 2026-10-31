use crate::game::{Delivery, GameState, Outcome};
use crate::logger;
use crate::protocol::{Command, MAX_LINE_BYTES, parse_command};
use serde_json::json;
use std::collections::{HashMap, VecDeque};
use std::io::{self, BufRead, BufReader, Write};
use std::net::{IpAddr, SocketAddr, TcpListener, TcpStream};
use std::sync::mpsc::{self, Sender};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

type ClientSenders = Arc<Mutex<HashMap<String, Sender<String>>>>;

pub fn run(address: &str, world_file: &str) -> Result<(), String> {
    let game = GameState::load(world_file)?;
    let listener = TcpListener::bind(address)
        .map_err(|error| format!("could not listen on {address}: {error}"))?;
    logger::info(
        "server_started",
        json!({"address": address, "world_file": world_file}),
    );
    serve(listener, Arc::new(Mutex::new(game))).map_err(|error| error.to_string())
}

pub fn serve(listener: TcpListener, game: Arc<Mutex<GameState>>) -> io::Result<()> {
    let clients: ClientSenders = Arc::new(Mutex::new(HashMap::new()));
    let connection_history: Arc<Mutex<HashMap<IpAddr, VecDeque<Instant>>>> =
        Arc::new(Mutex::new(HashMap::new()));

    for incoming in listener.incoming() {
        match incoming {
            Ok(stream) => {
                let peer = stream.peer_addr()?;
                check_rapid_connections(peer.ip(), &connection_history);
                logger::info("client_connected", json!({"peer": peer.to_string()}));
                let game = Arc::clone(&game);
                let clients = Arc::clone(&clients);
                thread::spawn(move || handle_connection(stream, peer, game, clients));
            }
            Err(error) => logger::error("accept_failed", json!({"error": error.to_string()})),
        }
    }
    Ok(())
}

fn handle_connection(
    stream: TcpStream,
    peer: SocketAddr,
    game: Arc<Mutex<GameState>>,
    clients: ClientSenders,
) {
    let reader_stream = match stream.try_clone() {
        Ok(stream) => stream,
        Err(error) => {
            logger::error(
                "stream_clone_failed",
                json!({"peer": peer.to_string(), "error": error.to_string()}),
            );
            return;
        }
    };
    let (sender, receiver) = mpsc::channel::<String>();
    thread::spawn(move || {
        let mut writer = stream;
        for message in receiver {
            if writeln!(writer, "{message}")
                .and_then(|_| writer.flush())
                .is_err()
            {
                break;
            }
        }
    });
    let _ = sender.send("OK hello proto=1".to_string());
    logger::info(
        "response_sent",
        json!({"peer": peer.to_string(), "response": "OK hello proto=1"}),
    );

    let mut reader = BufReader::new(reader_stream);
    let mut username: Option<String> = None;
    let mut command_times = VecDeque::new();
    loop {
        let mut bytes = Vec::new();
        match reader.read_until(b'\n', &mut bytes) {
            Ok(0) => break,
            Ok(_) => {}
            Err(error) => {
                logger::warn(
                    "read_failed",
                    json!({"peer": peer.to_string(), "error": error.to_string()}),
                );
                break;
            }
        }
        while matches!(bytes.last(), Some(b'\n' | b'\r')) {
            bytes.pop();
        }
        if bytes.len() > MAX_LINE_BYTES {
            send_response(&sender, username.as_deref(), "ERR 400 LINE_TOO_LONG");
            continue;
        }
        let line = match String::from_utf8(bytes) {
            Ok(line) => line,
            Err(_) => {
                send_response(&sender, username.as_deref(), "ERR 400 INVALID_UTF8");
                continue;
            }
        };
        check_command_flood(&mut command_times, username.as_deref(), peer);
        logger::info(
            "command_received",
            json!({"player": username, "peer": peer.to_string(), "command": line}),
        );

        let command = match parse_command(&line) {
            Ok(command) => command,
            Err(message) => {
                send_response(&sender, username.as_deref(), &format!("ERR 400 {message}"));
                continue;
            }
        };

        let outcome = match (&username, command) {
            (None, Command::Connect(name)) => {
                let outcome = game.lock().unwrap().connect(&name);
                if outcome.response == "OK connected" {
                    clients.lock().unwrap().insert(name.clone(), sender.clone());
                    username = Some(name);
                }
                outcome
            }
            (None, _) => Outcome {
                response: "ERR 400 NOT_CONNECTED".to_string(),
                deliveries: Vec::new(),
                close: false,
            },
            (Some(name), command) => game.lock().unwrap().handle(name, command),
        };

        send_response(&sender, username.as_deref(), &outcome.response);
        log_state_change(username.as_deref(), &line, &outcome);
        dispatch(&clients, outcome.deliveries);
        if outcome.close {
            break;
        }
    }

    if let Some(name) = username {
        clients.lock().unwrap().remove(&name);
        let deliveries = game.lock().unwrap().disconnect(&name);
        dispatch(&clients, deliveries);
        logger::info(
            "client_disconnected",
            json!({"player": name, "peer": peer.to_string()}),
        );
    } else {
        logger::info("client_disconnected", json!({"peer": peer.to_string()}));
    }
}

fn send_response(sender: &Sender<String>, username: Option<&str>, response: &str) {
    let _ = sender.send(response.to_string());
    logger::info(
        "response_sent",
        json!({"player": username, "response": response}),
    );
}

fn dispatch(clients: &ClientSenders, deliveries: Vec<Delivery>) {
    for delivery in deliveries {
        let sender = clients.lock().unwrap().get(&delivery.recipient).cloned();
        if let Some(sender) = sender
            && sender.send(delivery.message.clone()).is_err()
        {
            clients.lock().unwrap().remove(&delivery.recipient);
            logger::warn(
                "event_send_failed",
                json!({"player": delivery.recipient, "event": delivery.message}),
            );
        }
    }
}

fn log_state_change(username: Option<&str>, command: &str, outcome: &Outcome) {
    if !outcome.response.starts_with("OK") {
        return;
    }
    let name = command.split_whitespace().next().unwrap_or_default();
    if matches!(
        name.to_ascii_uppercase().as_str(),
        "MOVE" | "GROUP" | "TAKE" | "DROP" | "TALK" | "ATTACK" | "DEFEND" | "FLEE" | "QUEST"
    ) {
        logger::info(
            "world_state_changed",
            json!({"player": username, "command": command, "result": outcome.response}),
        );
    }
}

fn check_command_flood(history: &mut VecDeque<Instant>, username: Option<&str>, peer: SocketAddr) {
    let now = Instant::now();
    history.push_back(now);
    loop {
        match history.front() {
            Some(time) if now.duration_since(*time) > Duration::from_secs(1) => {
                history.pop_front();
            }
            _ => break,
        }
    }
    if history.len() == 21 {
        logger::warn(
            "command_flood",
            json!({"player": username, "peer": peer.to_string(), "commands_per_second": history.len()}),
        );
    }
}

fn check_rapid_connections(ip: IpAddr, histories: &Arc<Mutex<HashMap<IpAddr, VecDeque<Instant>>>>) {
    let now = Instant::now();
    let mut histories = histories.lock().unwrap();
    let history = histories.entry(ip).or_default();
    history.push_back(now);
    loop {
        match history.front() {
            Some(time) if now.duration_since(*time) > Duration::from_secs(5) => {
                history.pop_front();
            }
            _ => break,
        }
    }
    if history.len() == 11 {
        logger::warn(
            "rapid_connections",
            json!({"ip": ip.to_string(), "connections_in_five_seconds": history.len()}),
        );
    }
}
