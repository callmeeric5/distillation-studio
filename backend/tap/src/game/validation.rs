use crate::model::{QuestObjective, WorldConfig};
use std::collections::{HashSet, VecDeque};

pub fn validate_world(world: &WorldConfig) -> Result<(), String> {
    if !world.rooms.contains_key(&world.start_room) {
        return Err(format!("start room '{}' does not exist", world.start_room));
    }
    if world.rooms.len() < 8 {
        return Err("world must contain at least 8 rooms".to_string());
    }

    let mut placed_items = HashSet::new();
    for (room_id, room) in &world.rooms {
        for target in room.exits.values() {
            if !world.rooms.contains_key(target) {
                return Err(format!(
                    "room '{room_id}' has an invalid exit to '{target}'"
                ));
            }
        }
        for item in &room.items {
            if !world.items.contains_key(item) {
                return Err(format!("room '{room_id}' refers to unknown item '{item}'"));
            }
            if !placed_items.insert(item) {
                return Err(format!("item '{item}' is placed more than once"));
            }
        }
        for npc in &room.npcs {
            if !world.npcs.contains_key(npc) {
                return Err(format!("room '{room_id}' refers to unknown NPC '{npc}'"));
            }
        }
    }
    for (npc_id, npc) in &world.npcs {
        if npc.hp <= 0 {
            return Err(format!("NPC '{npc_id}' must have positive HP"));
        }
        if let Some(quest) = &npc.quest
            && !world.quests.contains_key(quest)
        {
            return Err(format!("NPC '{npc_id}' refers to unknown quest '{quest}'"));
        }
    }
    for (quest_id, quest) in &world.quests {
        if !world.npcs.contains_key(&quest.giver) {
            return Err(format!("quest '{quest_id}' has an unknown giver"));
        }
        if !world.items.contains_key(&quest.reward) {
            return Err(format!("quest '{quest_id}' has an unknown reward"));
        }
        let valid_target = match &quest.objective {
            QuestObjective::HaveItem { target } => world.items.contains_key(target),
            QuestObjective::DefeatNpc { target } => world.npcs.contains_key(target),
        };
        if !valid_target {
            return Err(format!(
                "quest '{quest_id}' has an unknown objective target"
            ));
        }
    }

    let mut reachable = HashSet::new();
    let mut queue = VecDeque::from([world.start_room.clone()]);
    while let Some(room) = queue.pop_front() {
        if reachable.insert(room.clone()) {
            queue.extend(world.rooms[&room].exits.values().cloned());
        }
    }
    if reachable.len() != world.rooms.len() {
        return Err("every room must be reachable from the start room".to_string());
    }
    Ok(())
}
