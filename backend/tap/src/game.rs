mod combat;
mod quest;
mod social;
mod validation;

use crate::model::{Group, Player, WorldConfig};
use crate::protocol::Command;
use serde_json::json;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub use validation::validate_world;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Delivery {
    pub recipient: String,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Outcome {
    pub response: String,
    pub deliveries: Vec<Delivery>,
    pub close: bool,
}

impl Outcome {
    fn reply(response: impl Into<String>) -> Self {
        Self {
            response: response.into(),
            deliveries: Vec::new(),
            close: false,
        }
    }

    fn error(code: u16, message: &str) -> Self {
        Self::reply(format!("ERR {code} {message}"))
    }
}

#[derive(Debug)]
pub struct GameState {
    pub world: WorldConfig,
    initial_world: WorldConfig,
    pub players: HashMap<String, Player>,
    pub groups: HashMap<String, Group>,
    npc_health: HashMap<String, i32>,
    next_group_id: u64,
}

impl GameState {
    pub fn load(path: impl AsRef<Path>) -> Result<Self, String> {
        let text = fs::read_to_string(path.as_ref())
            .map_err(|error| format!("could not read {}: {error}", path.as_ref().display()))?;
        let world =
            serde_json::from_str(&text).map_err(|error| format!("invalid world JSON: {error}"))?;
        Self::new(world)
    }

    pub fn new(world: WorldConfig) -> Result<Self, String> {
        validate_world(&world)?;
        let npc_health = world
            .npcs
            .iter()
            .map(|(id, npc)| (id.clone(), npc.hp))
            .collect();
        Ok(Self {
            initial_world: world.clone(),
            world,
            players: HashMap::new(),
            groups: HashMap::new(),
            npc_health,
            next_group_id: 1,
        })
    }

    pub fn connect(&mut self, username: &str) -> Outcome {
        if !valid_username(username) {
            return Outcome::error(400, "INVALID_USERNAME");
        }
        if self
            .players
            .keys()
            .any(|name| name.eq_ignore_ascii_case(username))
        {
            return Outcome::error(201, "NAME_IN_USE");
        }
        self.players
            .insert(username.to_string(), Player::new(&self.world.start_room));
        let mut outcome = Outcome::reply("OK connected");
        outcome.deliveries.extend(self.room_deliveries(
            &self.world.start_room,
            Some(username),
            format!("EVT ROOM PRESENCE ENTER {username}"),
        ));
        outcome
            .deliveries
            .extend(self.all_deliveries(format!("EVT STATS players={}", self.players.len())));
        outcome
    }

    pub fn disconnect(&mut self, username: &str) -> Vec<Delivery> {
        let player = match self.players.remove(username) {
            Some(player) => player,
            None => return Vec::new(),
        };
        let mut deliveries = self.room_deliveries(
            &player.room,
            None,
            format!("EVT ROOM PRESENCE LEAVE {username}"),
        );
        deliveries.extend(self.leave_group(username));
        deliveries.extend(self.all_deliveries(format!("EVT STATS players={}", self.players.len())));
        if self.players.is_empty() {
            self.reset_world();
        }
        deliveries
    }

    fn reset_world(&mut self) {
        self.world = self.initial_world.clone();
        self.players.clear();
        self.groups.clear();
        self.npc_health = self
            .world
            .npcs
            .iter()
            .map(|(id, npc)| (id.clone(), npc.hp))
            .collect();
        self.next_group_id = 1;
    }

    pub fn handle(&mut self, username: &str, command: Command) -> Outcome {
        if !self.players.contains_key(username) {
            return Outcome::error(400, "NOT_CONNECTED");
        }
        match command {
            Command::Connect(_) => Outcome::error(400, "ALREADY_CONNECTED"),
            Command::Look => self.look(username),
            Command::Move(direction) => self.move_player(username, &direction),
            Command::Chat {
                channel: scope,
                message,
            } => self.chat(username, &scope, &message),
            Command::Who => Outcome::reply(format!("OK players={}", self.players.len())),
            Command::Group(command) => self.group(username, command),
            Command::Take(item) => self.take(username, &item),
            Command::Drop(item) => self.drop_item(username, &item),
            Command::Inventory => self.inventory(username),
            Command::Talk(npc) => self.talk(username, &npc),
            Command::Attack(npc) => self.attack(username, &npc),
            Command::Defend => self.defend(username),
            Command::Flee => self.flee(username),
            Command::Status => self.status(username),
            Command::Quest(npc) => self.quest(username, &npc),
            Command::Quests => self.quests(username),
            Command::Quit => Outcome {
                response: "OK bye".to_string(),
                deliveries: Vec::new(),
                close: true,
            },
        }
    }

    fn look(&self, username: &str) -> Outcome {
        let player = &self.players[username];
        let room = &self.world.rooms[&player.room];
        let mut players = Vec::new();
        for (name, other) in &self.players {
            if other.room == player.room {
                players.push(name);
            }
        }
        let living_npcs: Vec<&String> = room
            .npcs
            .iter()
            .filter(|id| self.npc_health.get(*id).copied().unwrap_or_default() > 0)
            .collect();
        let data = json!({
            "room": { "id": player.room, "name": room.name, "description": room.description, "exits": room.exits },
            "players": players, "items": room.items, "npcs": living_npcs,
        });
        Outcome::reply(format!("OK {data}"))
    }

    fn move_player(&mut self, username: &str, direction: &str) -> Outcome {
        let old_room = self.players[username].room.clone();
        let direction = direction.to_ascii_lowercase();
        let new_room = match self.world.rooms[&old_room].exits.get(&direction) {
            Some(room) => room.clone(),
            None => return Outcome::error(301, "NO_EXIT"),
        };
        self.players.get_mut(username).unwrap().room = new_room.clone();
        self.players.get_mut(username).unwrap().target = None;
        let mut outcome = Outcome::reply(format!("OK room={new_room}"));
        outcome.deliveries.extend(self.room_deliveries(
            &old_room,
            Some(username),
            format!("EVT ROOM PRESENCE LEAVE {username}"),
        ));
        outcome.deliveries.extend(self.room_deliveries(
            &new_room,
            Some(username),
            format!("EVT ROOM PRESENCE ENTER {username}"),
        ));
        outcome
    }

    fn take(&mut self, username: &str, item_query: &str) -> Outcome {
        let room_id = self.players[username].room.clone();
        let item_id = match self.find_room_item(&room_id, item_query) {
            Some(item) => item,
            None => return Outcome::error(404, "ITEM_NOT_FOUND"),
        };
        if !self.world.items[&item_id].obtainable {
            return Outcome::error(404, "ITEM_NOT_FOUND");
        }
        self.world
            .rooms
            .get_mut(&room_id)
            .unwrap()
            .items
            .retain(|id| id != &item_id);
        self.players
            .get_mut(username)
            .unwrap()
            .inventory
            .push(item_id.clone());
        self.refresh_item_quest(username, &item_id);
        Outcome::reply(format!("OK taken={item_id}"))
    }

    fn drop_item(&mut self, username: &str, item_query: &str) -> Outcome {
        let item_id = match self.find_inventory_item(username, item_query) {
            Some(item) => item,
            None => return Outcome::error(404, "ITEM_NOT_IN_INVENTORY"),
        };
        let room_id = self.players[username].room.clone();
        self.players
            .get_mut(username)
            .unwrap()
            .inventory
            .retain(|id| id != &item_id);
        self.world
            .rooms
            .get_mut(&room_id)
            .unwrap()
            .items
            .push(item_id.clone());
        self.unset_item_quest(username, &item_id);
        Outcome::reply(format!("OK dropped={item_id}"))
    }

    fn inventory(&self, username: &str) -> Outcome {
        Outcome::reply(format!(
            "OK {}",
            serde_json::to_string(&self.players[username].inventory).unwrap()
        ))
    }

    fn talk(&self, username: &str, npc_query: &str) -> Outcome {
        let room = self.players[username].room.clone();
        let npc_id = match self.find_room_npc(&room, npc_query) {
            Some(npc) => npc,
            None => return Outcome::error(404, "NPC_NOT_FOUND"),
        };
        let npc = &self.world.npcs[&npc_id];
        let dialogue = npc.dialogue.first().cloned().unwrap_or_default();
        Outcome::reply(format!(
            "OK {}",
            json!({ "npc": npc_id, "dialogue": dialogue })
        ))
    }

    fn status(&self, username: &str) -> Outcome {
        let player = &self.players[username];
        let status = if player.target.is_some() {
            "combat"
        } else if player.hp < 50 {
            "wounded"
        } else {
            "healthy"
        };
        Outcome::reply(format!(
            "OK {}",
            json!({"hp": player.hp, "max_hp": 100, "status": status})
        ))
    }

    fn room_deliveries(&self, room: &str, exclude: Option<&str>, message: String) -> Vec<Delivery> {
        self.players
            .iter()
            .filter(|(name, player)| {
                if player.room != room {
                    return false;
                }
                match exclude {
                    Some(excluded) => name.as_str() != excluded,
                    None => true,
                }
            })
            .map(|(name, _)| Delivery {
                recipient: name.clone(),
                message: message.clone(),
            })
            .collect()
    }

    fn all_deliveries(&self, message: String) -> Vec<Delivery> {
        self.players
            .keys()
            .map(|name| Delivery {
                recipient: name.clone(),
                message: message.clone(),
            })
            .collect()
    }

    fn group_deliveries(&self, group_id: &str, message: String) -> Vec<Delivery> {
        self.groups
            .get(group_id)
            .map(|group| {
                group
                    .members
                    .iter()
                    .map(|name| Delivery {
                        recipient: name.clone(),
                        message: message.clone(),
                    })
                    .collect()
            })
            .unwrap_or_default()
    }

    fn find_player_name(&self, query: &str) -> Option<String> {
        self.players
            .keys()
            .find(|name| name.eq_ignore_ascii_case(query))
            .cloned()
    }

    fn find_room_item(&self, room: &str, query: &str) -> Option<String> {
        self.world.rooms[room].items.iter().find_map(|id| {
            if id.eq_ignore_ascii_case(query)
                || self.world.items[id].name.eq_ignore_ascii_case(query)
            {
                Some(id.clone())
            } else {
                None
            }
        })
    }

    fn find_inventory_item(&self, username: &str, query: &str) -> Option<String> {
        self.players[username].inventory.iter().find_map(|id| {
            if id.eq_ignore_ascii_case(query)
                || self.world.items[id].name.eq_ignore_ascii_case(query)
            {
                Some(id.clone())
            } else {
                None
            }
        })
    }

    fn find_room_npc(&self, room: &str, query: &str) -> Option<String> {
        self.world.rooms[room].npcs.iter().find_map(|id| {
            let alive = self.npc_health.get(id).copied().unwrap_or_default() > 0;
            if alive
                && (id.eq_ignore_ascii_case(query)
                    || self.world.npcs[id].name.eq_ignore_ascii_case(query))
            {
                Some(id.clone())
            } else {
                None
            }
        })
    }

    fn item_is_owned_or_placed(&self, item_id: &str) -> bool {
        self.world
            .rooms
            .values()
            .any(|room| room.items.iter().any(|id| id == item_id))
            || self
                .players
                .values()
                .any(|player| player.inventory.iter().any(|id| id == item_id))
    }
}

fn valid_username(username: &str) -> bool {
    let length = username.chars().count();
    (1..=24).contains(&length)
        && !username
            .chars()
            .any(|character| character.is_whitespace() || character.is_control())
}

#[cfg(test)]
mod tests {
    use super::GameState;
    use crate::protocol::Command;
    use std::path::PathBuf;

    fn game() -> GameState {
        let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("data/world.json");
        GameState::load(path).expect("test world should load")
    }

    #[test]
    fn shared_world_is_not_reset_while_another_player_is_online() {
        let mut game = game();
        assert_eq!(game.connect("alice").response, "OK connected");
        assert_eq!(game.connect("bob").response, "OK connected");
        assert_eq!(
            game.handle("alice", Command::Move("north".into())).response,
            "OK room=loc.bakery"
        );
        assert_eq!(
            game.handle("alice", Command::Take("Fresh Bread".into()))
                .response,
            "OK taken=item.bread"
        );

        game.disconnect("alice");

        assert!(
            !game.world.rooms["loc.bakery"]
                .items
                .contains(&"item.bread".to_string())
        );
        assert!(game.players.contains_key("bob"));
    }

    #[test]
    fn last_disconnect_restores_world_and_group_counter() {
        let mut game = game();
        game.connect("alice");
        game.handle("alice", Command::Move("north".into()));
        game.handle("alice", Command::Take("Fresh Bread".into()));
        game.handle(
            "alice",
            Command::Group(crate::protocol::GroupCommand::Create),
        );

        game.disconnect("alice");

        assert!(game.players.is_empty());
        assert!(game.groups.is_empty());
        assert!(
            game.world.rooms["loc.bakery"]
                .items
                .contains(&"item.bread".to_string())
        );
        game.connect("bob");
        assert_eq!(
            game.handle("bob", Command::Group(crate::protocol::GroupCommand::Create))
                .response,
            "OK group=group-1"
        );
    }

    #[test]
    fn multiplayer_chat_and_group_actions_emit_realtime_deliveries() {
        let mut game = game();
        game.connect("alice");
        game.connect("bob");

        let chat = game.handle(
            "alice",
            Command::Chat {
                channel: "GLOBAL".into(),
                message: "hello bob".into(),
            },
        );
        assert_eq!(chat.deliveries.len(), 2);
        assert!(chat.deliveries.iter().any(|delivery| {
            delivery.recipient == "bob" && delivery.message == "EVT GLOBAL CHAT alice hello bob"
        }));

        assert_eq!(
            game.handle(
                "alice",
                Command::Group(crate::protocol::GroupCommand::Create)
            )
            .response,
            "OK group=group-1"
        );
        let invite = game.handle(
            "alice",
            Command::Group(crate::protocol::GroupCommand::Invite("bob".into())),
        );
        assert_eq!(invite.deliveries[0].message, "EVT GROUP INVITE alice");
        assert_eq!(
            game.handle(
                "bob",
                Command::Group(crate::protocol::GroupCommand::Join("alice".into()))
            )
            .response,
            "OK group=group-1"
        );
    }

    #[test]
    fn completed_fetch_quest_keeps_completed_progress() {
        let mut game = game();
        game.connect("alice");
        game.handle("alice", Command::Move("east".into()));
        game.handle("alice", Command::Quest("Village Healer".into()));
        game.handle("alice", Command::Take("Healing Herbs".into()));
        game.handle("alice", Command::Quest("Village Healer".into()));

        let quests = game.handle("alice", Command::Quests).response;
        assert!(quests.contains("\"progress\":\"1/1\""));
        assert!(quests.contains("\"status\":\"completed\""));
    }
}
