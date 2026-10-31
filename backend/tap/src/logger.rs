use chrono::Utc;
use serde_json::{Value, json};
use std::sync::{Mutex, OnceLock};

static LOG_LOCK: OnceLock<Mutex<()>> = OnceLock::new();

pub fn info(event: &str, fields: Value) {
    write("INFO", event, fields);
}

pub fn warn(event: &str, fields: Value) {
    write("WARN", event, fields);
}

pub fn error(event: &str, fields: Value) {
    write("ERROR", event, fields);
}

fn write(level: &str, event: &str, fields: Value) {
    let _guard = LOG_LOCK.get_or_init(|| Mutex::new(())).lock();
    let record = json!({
        "timestamp": Utc::now().to_rfc3339(),
        "level": level,
        "event": event,
        "fields": fields,
    });
    if level == "ERROR" {
        eprintln!("{record}");
    } else {
        println!("{record}");
    }
}
