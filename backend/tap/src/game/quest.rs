use super::{GameState, Outcome};
use crate::model::{QuestObjective, QuestStatus};
use serde_json::json;

impl GameState {
    pub(super) fn quest(&mut self, username: &str, npc_query: &str) -> Outcome {
        let room = self.players[username].room.clone();
        let npc_id = match self.find_room_npc(&room, npc_query) {
            Some(npc) => npc,
            None => return Outcome::error(404, "NPC_NOT_FOUND"),
        };
        let quest_id = match self.world.npcs[&npc_id].quest.clone() {
            Some(quest) => quest,
            None => return Outcome::error(406, "NO_QUEST_AVAILABLE"),
        };
        let current = self.players[username].quests.get(&quest_id).cloned();
        match current {
            None => {
                self.players
                    .get_mut(username)
                    .unwrap()
                    .quests
                    .insert(quest_id.clone(), QuestStatus::Active);
                self.refresh_quest(username, &quest_id);
                Outcome::reply(format!(
                    "OK {}",
                    self.quest_json(username, &quest_id, "active")
                ))
            }
            Some(QuestStatus::Active) => Outcome::reply(format!(
                "OK {}",
                self.quest_json(username, &quest_id, "active")
            )),
            Some(QuestStatus::ObjectiveMet) => {
                let quest = self.world.quests[&quest_id].clone();
                if let QuestObjective::HaveItem { target } = &quest.objective {
                    self.players
                        .get_mut(username)
                        .unwrap()
                        .inventory
                        .retain(|id| id != target);
                }
                if self.item_is_owned_or_placed(&quest.reward) {
                    return Outcome::error(400, "REWARD_UNAVAILABLE");
                }
                self.players
                    .get_mut(username)
                    .unwrap()
                    .inventory
                    .push(quest.reward.clone());
                self.players
                    .get_mut(username)
                    .unwrap()
                    .quests
                    .insert(quest_id.clone(), QuestStatus::Completed);
                Outcome::reply(format!(
                    "OK {}",
                    self.quest_json(username, &quest_id, "completed")
                ))
            }
            Some(QuestStatus::Completed) => Outcome::error(406, "NO_QUEST_AVAILABLE"),
        }
    }

    pub(super) fn quests(&self, username: &str) -> Outcome {
        let list: Vec<_> = self.players[username]
            .quests
            .iter()
            .map(|(id, status)| {
                let label = match status {
                    QuestStatus::Active => "active",
                    QuestStatus::ObjectiveMet => "ready_to_complete",
                    QuestStatus::Completed => "completed",
                };
                self.quest_json(username, id, label)
            })
            .collect();
        Outcome::reply(format!("OK {}", json!(list)))
    }

    fn quest_json(&self, username: &str, quest_id: &str, status: &str) -> serde_json::Value {
        let quest = &self.world.quests[quest_id];
        let progress = match &quest.objective {
            QuestObjective::HaveItem { target } => {
                if matches!(
                    self.players[username].quests.get(quest_id),
                    Some(QuestStatus::Completed)
                ) || self.players[username].inventory.contains(target)
                {
                    "1/1"
                } else {
                    "0/1"
                }
            }
            QuestObjective::DefeatNpc { .. } => {
                if matches!(
                    self.players[username].quests.get(quest_id),
                    Some(QuestStatus::ObjectiveMet | QuestStatus::Completed)
                ) {
                    "1/1"
                } else {
                    "0/1"
                }
            }
        };
        json!({
            "quest_id": quest_id,
            "description": quest.description,
            "reward": quest.reward,
            "status": status,
            "progress": progress,
        })
    }

    fn refresh_quest(&mut self, username: &str, quest_id: &str) {
        let met = match &self.world.quests[quest_id].objective {
            QuestObjective::HaveItem { target } => {
                self.players[username].inventory.contains(target)
            }
            QuestObjective::DefeatNpc { .. } => false,
        };
        if met {
            self.players
                .get_mut(username)
                .unwrap()
                .quests
                .insert(quest_id.to_string(), QuestStatus::ObjectiveMet);
        }
    }

    pub(super) fn refresh_item_quest(&mut self, username: &str, item_id: &str) {
        let quest_ids: Vec<String> = self.players[username]
            .quests
            .iter()
            .filter_map(|(id, status)| {
                let matching = matches!(
                    &self.world.quests[id].objective,
                    QuestObjective::HaveItem { target } if target == item_id
                );
                if matching && *status == QuestStatus::Active {
                    Some(id.clone())
                } else {
                    None
                }
            })
            .collect();
        for id in quest_ids {
            self.players
                .get_mut(username)
                .unwrap()
                .quests
                .insert(id, QuestStatus::ObjectiveMet);
        }
    }

    pub(super) fn unset_item_quest(&mut self, username: &str, item_id: &str) {
        let quest_ids: Vec<String> = self.players[username]
            .quests
            .iter()
            .filter_map(|(id, status)| {
                let matching = matches!(
                    &self.world.quests[id].objective,
                    QuestObjective::HaveItem { target } if target == item_id
                );
                if matching && *status == QuestStatus::ObjectiveMet {
                    Some(id.clone())
                } else {
                    None
                }
            })
            .collect();
        for id in quest_ids {
            self.players
                .get_mut(username)
                .unwrap()
                .quests
                .insert(id, QuestStatus::Active);
        }
    }

    pub(super) fn mark_npc_defeated(&mut self, username: &str, npc_id: &str) {
        let quest_ids: Vec<String> = self.players[username]
            .quests
            .iter()
            .filter_map(|(id, status)| {
                let matching = matches!(
                    &self.world.quests[id].objective,
                    QuestObjective::DefeatNpc { target } if target == npc_id
                );
                if matching && *status == QuestStatus::Active {
                    Some(id.clone())
                } else {
                    None
                }
            })
            .collect();
        for id in quest_ids {
            self.players
                .get_mut(username)
                .unwrap()
                .quests
                .insert(id, QuestStatus::ObjectiveMet);
        }
    }
}
