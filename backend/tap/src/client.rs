use std::io::{self, BufRead, BufReader, Write};
use std::net::TcpStream;
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread;

pub struct ClientConnection {
    pub commands: Sender<String>,
    pub messages: Receiver<String>,
}

pub fn connect(address: &str) -> io::Result<ClientConnection> {
    let stream = TcpStream::connect(address)?;
    let reader_stream = stream.try_clone()?;
    let (command_tx, command_rx) = mpsc::channel::<String>();
    let (message_tx, message_rx) = mpsc::channel::<String>();

    let reader_messages = message_tx.clone();
    thread::spawn(move || {
        let reader = BufReader::new(reader_stream);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    if reader_messages.send(line).is_err() {
                        break;
                    }
                }
                Err(error) => {
                    let _ = reader_messages.send(format!("CLIENT ERROR read failed: {error}"));
                    break;
                }
            }
        }
        let _ = reader_messages.send("CLIENT INFO connection closed".to_string());
    });

    thread::spawn(move || {
        let mut writer = stream;
        for command in command_rx {
            if writeln!(writer, "{command}")
                .and_then(|_| writer.flush())
                .is_err()
            {
                let _ = message_tx.send("CLIENT ERROR send failed".to_string());
                break;
            }
        }
    });

    Ok(ClientConnection {
        commands: command_tx,
        messages: message_rx,
    })
}
