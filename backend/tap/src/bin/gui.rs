use eframe::egui;
use serde::Deserialize;
use std::collections::HashMap;

#[derive(Default, Deserialize)]
struct RoomDetails {
    id: String,
    name: String,
    description: String,
    exits: HashMap<String, String>,
}

#[derive(Default, Deserialize)]
struct LookData {
    room: RoomDetails,
    players: Vec<String>,
    items: Vec<String>,
    npcs: Vec<String>,
}

struct TapApp {
    address: String,
    username: String,
    connection: Option<tap::client::ClientConnection>,
    authenticated: bool,
    room: RoomDetails,
    room_players: Vec<String>,
    items: Vec<String>,
    npcs: Vec<String>,
    inventory: Vec<String>,
    server_players: usize,
    hp: i64,
    chat_scope: String,
    chat_input: String,
    group_input: String,
    raw_command: String,
    chat_lines: Vec<String>,
    log_lines: Vec<String>,
}

impl Default for TapApp {
    fn default() -> Self {
        Self {
            address: "127.0.0.1:4242".to_string(),
            username: String::new(),
            connection: None,
            authenticated: false,
            room: RoomDetails::default(),
            room_players: Vec::new(),
            items: Vec::new(),
            npcs: Vec::new(),
            inventory: Vec::new(),
            server_players: 0,
            hp: 100,
            chat_scope: "GLOBAL".to_string(),
            chat_input: String::new(),
            group_input: String::new(),
            raw_command: String::new(),
            chat_lines: Vec::new(),
            log_lines: Vec::new(),
        }
    }
}

impl TapApp {
    fn connect(&mut self) {
        match tap::client::connect(&self.address) {
            Ok(connection) => {
                if self.username.trim().is_empty() {
                    self.log_lines.push("Choose a username first.".to_string());
                    return;
                }
                let _ = connection
                    .commands
                    .send(format!("CONNECT {}", self.username.trim()));
                self.connection = Some(connection);
                self.log_lines
                    .push(format!("Connecting to {}...", self.address));
            }
            Err(error) => self.log_lines.push(format!("Connection failed: {error}")),
        }
    }

    fn send(&self, command: impl Into<String>) {
        if let Some(connection) = &self.connection {
            let _ = connection.commands.send(command.into());
        }
    }

    fn refresh(&self) {
        self.send("LOOK");
        self.send("INVENTORY");
        self.send("STATUS");
        self.send("WHO");
    }

    fn poll_messages(&mut self) {
        let messages: Vec<String> = self
            .connection
            .as_ref()
            .map(|connection| connection.messages.try_iter().collect())
            .unwrap_or_default();
        for message in messages {
            self.process_message(message);
        }
    }

    fn process_message(&mut self, message: String) {
        if message == "OK connected" {
            self.authenticated = true;
            self.refresh();
        }
        if let Some(count) = message.strip_prefix("OK players=") {
            self.server_players = count.parse().unwrap_or(0);
        }
        if message.starts_with("EVT ") && message.contains(" CHAT ") {
            self.chat_lines.push(message);
            return;
        }
        if let Some(json_text) = message.strip_prefix("OK ") {
            if let Ok(value) = serde_json::from_str::<serde_json::Value>(json_text) {
                if value.get("room").is_some() {
                    if let Ok(look) = serde_json::from_value::<LookData>(value) {
                        self.room = look.room;
                        self.room_players = look.players;
                        self.items = look.items;
                        self.npcs = look.npcs;
                    }
                } else if let Some(array) = value.as_array() {
                    if array.iter().all(serde_json::Value::is_string) {
                        self.inventory = array
                            .iter()
                            .filter_map(|item| item.as_str().map(str::to_string))
                            .collect();
                    }
                } else {
                    let hp = value
                        .get("hp")
                        .or_else(|| value.get("attacker_hp"))
                        .and_then(serde_json::Value::as_i64);
                    if let Some(hp) = hp {
                        self.hp = hp;
                    }
                }
            }
        }
        self.log_lines.push(message);
        if self.log_lines.len() > 500 {
            self.log_lines.drain(0..100);
        }
    }

    fn connection_screen(&mut self, ui: &mut egui::Ui) {
        ui.heading("The Answer Protocol");
        ui.label("Connect to a TAP server");
        ui.horizontal(|ui| {
            ui.label("Server");
            ui.text_edit_singleline(&mut self.address);
        });
        ui.horizontal(|ui| {
            ui.label("Username");
            ui.text_edit_singleline(&mut self.username);
        });
        if ui.button("Connect").clicked() {
            self.connect();
        }
        ui.separator();
        for line in self.log_lines.iter().rev().take(8).rev() {
            ui.label(line);
        }
    }

    fn world_panel(&mut self, ui: &mut egui::Ui) {
        ui.heading(&self.room.name);
        ui.label(format!("{} ({})", self.room.description, self.room.id));
        ui.label(format!(
            "HP: {}   Players here: {}   Players online: {}",
            self.hp,
            self.room_players.len(),
            self.server_players
        ));
        ui.separator();

        ui.label("Exits");
        let mut exits: Vec<(String, String)> = self
            .room
            .exits
            .iter()
            .map(|(direction, room)| (direction.clone(), room.clone()))
            .collect();
        exits.sort();
        ui.horizontal_wrapped(|ui| {
            for (direction, destination) in exits {
                if ui.button(format!("{direction} → {destination}")).clicked() {
                    self.send(format!("MOVE {direction}"));
                    self.send("LOOK");
                }
            }
        });

        ui.separator();
        ui.columns(3, |columns| {
            columns[0].label("Items");
            for item in self.items.clone() {
                columns[0].horizontal(|ui| {
                    ui.label(&item);
                    if ui.small_button("Take").clicked() {
                        self.send(format!("TAKE {item}"));
                        self.send("LOOK");
                        self.send("INVENTORY");
                    }
                });
            }

            columns[1].label("NPCs");
            for npc in self.npcs.clone() {
                columns[1].label(&npc);
                columns[1].horizontal_wrapped(|ui| {
                    if ui.small_button("Talk").clicked() {
                        self.send(format!("TALK {npc}"));
                    }
                    if ui.small_button("Attack").clicked() {
                        self.send(format!("ATTACK {npc}"));
                        self.send("STATUS");
                        self.send("LOOK");
                    }
                    if ui.small_button("Quest").clicked() {
                        self.send(format!("QUEST {npc}"));
                        self.send("INVENTORY");
                    }
                });
            }

            columns[2].label("Inventory");
            for item in self.inventory.clone() {
                columns[2].horizontal(|ui| {
                    ui.label(&item);
                    if ui.small_button("Drop").clicked() {
                        self.send(format!("DROP {item}"));
                        self.send("LOOK");
                        self.send("INVENTORY");
                    }
                });
            }
        });
    }

    fn action_panel(&mut self, ui: &mut egui::Ui) {
        ui.horizontal_wrapped(|ui| {
            if ui.button("Look").clicked() {
                self.refresh();
            }
            if ui.button("Status").clicked() {
                self.send("STATUS");
            }
            if ui.button("Defend").clicked() {
                self.send("DEFEND");
                self.send("STATUS");
            }
            if ui.button("Flee").clicked() {
                self.send("FLEE");
                self.refresh();
            }
            if ui.button("Quests").clicked() {
                self.send("QUESTS");
            }
            if ui.button("Who").clicked() {
                self.send("WHO");
            }
            if ui.button("Quit").clicked() {
                self.send("QUIT");
                self.authenticated = false;
                self.connection = None;
            }
        });

        ui.horizontal(|ui| {
            ui.label("Group player/leader");
            ui.text_edit_singleline(&mut self.group_input);
            if ui.button("Create").clicked() {
                self.send("GROUP CREATE");
            }
            if ui.button("Invite").clicked() {
                self.send(format!("GROUP INVITE {}", self.group_input.trim()));
            }
            if ui.button("Join").clicked() {
                self.send(format!("GROUP JOIN {}", self.group_input.trim()));
            }
            if ui.button("Leave").clicked() {
                self.send("GROUP LEAVE");
            }
        });

        ui.horizontal(|ui| {
            egui::ComboBox::from_id_salt("chat_scope")
                .selected_text(&self.chat_scope)
                .show_ui(ui, |ui| {
                    for scope in ["GLOBAL", "ROOM", "GROUP"] {
                        ui.selectable_value(&mut self.chat_scope, scope.to_string(), scope);
                    }
                });
            let submitted = ui.text_edit_singleline(&mut self.chat_input).lost_focus()
                && ui.input(|input| input.key_pressed(egui::Key::Enter));
            if (ui.button("Send chat").clicked() || submitted) && !self.chat_input.trim().is_empty()
            {
                self.send(format!(
                    "CHAT {} {}",
                    self.chat_scope,
                    self.chat_input.trim()
                ));
                self.chat_input.clear();
            }
        });

        ui.horizontal(|ui| {
            ui.label("Raw TAP command");
            ui.text_edit_singleline(&mut self.raw_command);
            if ui.button("Send").clicked() && !self.raw_command.trim().is_empty() {
                self.send(self.raw_command.trim().to_string());
                self.raw_command.clear();
            }
        });
    }
}

impl eframe::App for TapApp {
    fn update(&mut self, context: &egui::Context, _frame: &mut eframe::Frame) {
        self.poll_messages();
        context.request_repaint_after(std::time::Duration::from_millis(50));

        if !self.authenticated {
            egui::CentralPanel::default().show(context, |ui| {
                self.connection_screen(ui);
            });
            return;
        }

        // Panels keep chat and protocol logs visible even when the room controls grow.
        egui::TopBottomPanel::bottom("chat_panel")
            .resizable(true)
            .default_height(180.0)
            .min_height(100.0)
            .show(context, |ui| {
                ui.heading("Chat");
                egui::ScrollArea::vertical()
                    .auto_shrink([false, false])
                    .stick_to_bottom(true)
                    .show(ui, |ui| {
                        for line in &self.chat_lines {
                            ui.label(line);
                        }
                    });
            });

        egui::SidePanel::left("world_and_actions")
            .resizable(true)
            .default_width(520.0)
            .min_width(360.0)
            .show(context, |ui| {
                egui::ScrollArea::vertical()
                    .auto_shrink([false, false])
                    .show(ui, |ui| {
                        self.world_panel(ui);
                        ui.separator();
                        self.action_panel(ui);
                    });
            });

        egui::CentralPanel::default().show(context, |ui| {
            ui.horizontal(|ui| {
                ui.heading("Protocol log");
                if ui.small_button("Clear").clicked() {
                    self.log_lines.clear();
                }
            });
            ui.separator();
            egui::ScrollArea::vertical()
                .auto_shrink([false, false])
                .stick_to_bottom(true)
                .show(ui, |ui| {
                    for line in &self.log_lines {
                        ui.label(line);
                    }
                });
        });
    }
}

fn main() -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([1050.0, 760.0]),
        ..Default::default()
    };
    eframe::run_native(
        "TAP Adventure",
        options,
        Box::new(|_creation_context| Ok(Box::new(TapApp::default()))),
    )
}
