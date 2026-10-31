use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone, Deserialize)]
pub struct WorldConfig {
    pub start_room: String,
    pub rooms: HashMap<String, Room>,
    pub items: HashMap<String, Item>,
    pub npcs: HashMap<String, Npc>,
    pub quests: HashMap<String, Quest>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Room {
    pub name: String,
    pub description: String,
    pub exits: HashMap<String, String>,
    #[serde(default)]
    pub items: Vec<String>,
    #[serde(default)]
    pub npcs: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Item {
    pub name: String,
    pub description: String,
    pub obtainable: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Npc {
    pub name: String,
    pub description: String,
    pub dialogue: Vec<String>,
    #[serde(default)]
    pub hostile: bool,
    #[serde(default)]
    pub hp: i32,
    #[serde(default)]
    pub damage: i32,
    pub quest: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Quest {
    pub description: String,
    pub giver: String,
    pub objective: QuestObjective,
    pub reward: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum QuestObjective {
    HaveItem { target: String },
    DefeatNpc { target: String },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QuestStatus {
    Active,
    ObjectiveMet,
    Completed,
}

#[derive(Debug, Clone)]
pub struct Player {
    pub room: String,
    pub hp: i32,
    pub inventory: Vec<String>,
    pub target: Option<String>,
    pub group: Option<String>,
    pub invitations: HashSet<String>,
    pub quests: HashMap<String, QuestStatus>,
}

impl Player {
    pub fn new(start_room: &str) -> Self {
        Self {
            room: start_room.to_string(),
            hp: 100,
            inventory: Vec::new(),
            target: None,
            group: None,
            invitations: HashSet::new(),
            quests: HashMap::new(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct Group {
    pub leader: String,
    pub members: HashSet<String>,
}
