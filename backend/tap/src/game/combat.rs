use super::{GameState, Outcome};
use serde_json::json;

impl GameState {
    pub(super) fn attack(&mut self, username: &str, npc_query: &str) -> Outcome {
        let room = self.players[username].room.clone();
        let npc_id = match self.find_room_npc(&room, npc_query) {
            Some(npc) => npc,
            None => return Outcome::error(404, "NPC_NOT_FOUND"),
        };
        let npc = &self.world.npcs[&npc_id];
        if !npc.hostile {
            return Outcome::error(405, "NPC_NOT_HOSTILE");
        }

        let target_hp = self.npc_health.get_mut(&npc_id).unwrap();
        *target_hp = (*target_hp - 10).max(0);
        let target_hp_after = *target_hp;
        let counter_damage = if target_hp_after > 0 { npc.damage } else { 0 };
        let npc_name = npc.name.clone();

        let player = self.players.get_mut(username).unwrap();
        if target_hp_after > 0 {
            player.target = Some(npc_id.clone());
        } else {
            player.target = None;
        }
        player.hp = (player.hp - counter_damage).max(0);
        let mut respawned = false;
        if player.hp == 0 {
            player.hp = 50;
            player.room = self.world.start_room.clone();
            player.target = None;
            respawned = true;
        }
        let player_hp = player.hp;

        if target_hp_after == 0 {
            self.mark_npc_defeated(username, &npc_id);
        }
        let result = json!({
            "attacker_hp": player_hp,
            "target": npc_id,
            "target_hp": target_hp_after,
            "damage": 10,
            "counter_damage": counter_damage,
            "status": if respawned { "respawned" } else if target_hp_after == 0 { "victory" } else { "combat" },
        });
        let mut outcome = Outcome::reply(format!("OK {result}"));
        outcome.deliveries.extend(self.room_deliveries(
            &room,
            Some(username),
            format!("EVT ROOM COMBAT {username} attacked {npc_name}"),
        ));
        if respawned && room != self.world.start_room {
            outcome.deliveries.extend(self.room_deliveries(
                &room,
                Some(username),
                format!("EVT ROOM PRESENCE LEAVE {username}"),
            ));
            outcome.deliveries.extend(self.room_deliveries(
                &self.world.start_room,
                Some(username),
                format!("EVT ROOM PRESENCE ENTER {username}"),
            ));
        }
        outcome
    }

    pub(super) fn defend(&mut self, username: &str) -> Outcome {
        let target_id = match self.players[username].target.clone() {
            Some(target) => target,
            None => return Outcome::error(400, "NOT_IN_COMBAT"),
        };
        if self.npc_health[&target_id] == 0 {
            self.players.get_mut(username).unwrap().target = None;
            return Outcome::error(400, "NOT_IN_COMBAT");
        }
        let damage = (self.world.npcs[&target_id].damage + 1) / 2;
        let old_room = self.players[username].room.clone();
        let player = self.players.get_mut(username).unwrap();
        player.hp = (player.hp - damage).max(0);
        let respawned = player.hp == 0;
        if respawned {
            player.hp = 50;
            player.room = self.world.start_room.clone();
            player.target = None;
        }
        let mut outcome = Outcome::reply(format!(
            "OK {}",
            json!({"damage": damage, "hp": player.hp, "status": if respawned { "respawned" } else { "defending" }, "from_room": old_room})
        ));
        outcome.deliveries.extend(self.room_deliveries(
            &old_room,
            Some(username),
            format!("EVT ROOM COMBAT {username} defended"),
        ));
        if respawned && old_room != self.world.start_room {
            outcome.deliveries.extend(self.room_deliveries(
                &old_room,
                Some(username),
                format!("EVT ROOM PRESENCE LEAVE {username}"),
            ));
            outcome.deliveries.extend(self.room_deliveries(
                &self.world.start_room,
                Some(username),
                format!("EVT ROOM PRESENCE ENTER {username}"),
            ));
        }
        outcome
    }

    pub(super) fn flee(&mut self, username: &str) -> Outcome {
        if self.players[username].target.is_none() {
            return Outcome::error(400, "NOT_IN_COMBAT");
        }
        let old_room = self.players[username].room.clone();
        self.players.get_mut(username).unwrap().target = None;
        self.players.get_mut(username).unwrap().room = self.world.start_room.clone();
        let mut outcome = Outcome::reply(format!("OK room={}", self.world.start_room));
        if old_room != self.world.start_room {
            outcome.deliveries.extend(self.room_deliveries(
                &old_room,
                Some(username),
                format!("EVT ROOM PRESENCE LEAVE {username}"),
            ));
            outcome.deliveries.extend(self.room_deliveries(
                &self.world.start_room,
                Some(username),
                format!("EVT ROOM PRESENCE ENTER {username}"),
            ));
        }
        outcome
    }
}
