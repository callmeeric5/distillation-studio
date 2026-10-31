use super::{Delivery, GameState, Outcome};
use crate::model::Group;
use crate::protocol::GroupCommand;
use std::collections::HashSet;

impl GameState {
    pub(super) fn chat(&self, username: &str, scope: &str, message: &str) -> Outcome {
        let event = format!("EVT {scope} CHAT {username} {message}");
        let deliveries = match scope {
            "GLOBAL" => self.all_deliveries(event),
            "ROOM" => self.room_deliveries(&self.players[username].room, None, event),
            "GROUP" => {
                let group_id = match &self.players[username].group {
                    Some(group) => group,
                    None => return Outcome::error(401, "NOT_IN_GROUP"),
                };
                self.group_deliveries(group_id, event)
            }
            _ => return Outcome::error(400, "INVALID_CHAT_SCOPE"),
        };
        Outcome {
            response: "OK".to_string(),
            deliveries,
            close: false,
        }
    }

    pub(super) fn group(&mut self, username: &str, command: GroupCommand) -> Outcome {
        match command {
            GroupCommand::Create => {
                if self.players[username].group.is_some() {
                    return Outcome::error(402, "ALREADY_IN_GROUP");
                }
                let id = format!("group-{}", self.next_group_id);
                self.next_group_id += 1;
                let mut members = HashSet::new();
                members.insert(username.to_string());
                self.groups.insert(
                    id.clone(),
                    Group {
                        leader: username.to_string(),
                        members,
                    },
                );
                self.players.get_mut(username).unwrap().group = Some(id.clone());
                Outcome::reply(format!("OK group={id}"))
            }
            GroupCommand::Invite(target) => {
                let group_id = match self.players[username].group.clone() {
                    Some(group) => group,
                    None => return Outcome::error(401, "NOT_IN_GROUP"),
                };
                if !self.groups[&group_id].leader.eq(username) {
                    return Outcome::error(403, "NOT_GROUP_LEADER");
                }
                let target_name = match self.find_player_name(&target) {
                    Some(name) => name,
                    None => return Outcome::error(404, "PLAYER_NOT_FOUND"),
                };
                if self.players[&target_name].group.is_some() {
                    return Outcome::error(402, "ALREADY_IN_GROUP");
                }
                self.players
                    .get_mut(&target_name)
                    .unwrap()
                    .invitations
                    .insert(group_id);
                Outcome {
                    response: "OK".to_string(),
                    deliveries: vec![Delivery {
                        recipient: target_name,
                        message: format!("EVT GROUP INVITE {username}"),
                    }],
                    close: false,
                }
            }
            GroupCommand::Join(leader) => {
                if self.players[username].group.is_some() {
                    return Outcome::error(402, "ALREADY_IN_GROUP");
                }
                let leader_name = match self.find_player_name(&leader) {
                    Some(name) => name,
                    None => return Outcome::error(404, "PLAYER_NOT_FOUND"),
                };
                let group_id = match self.players[&leader_name].group.clone() {
                    Some(group) => group,
                    None => return Outcome::error(404, "GROUP_NOT_FOUND"),
                };
                if self.groups[&group_id].leader != leader_name {
                    return Outcome::error(404, "GROUP_NOT_FOUND");
                }
                if !self.players[username].invitations.contains(&group_id) {
                    return Outcome::error(403, "NOT_INVITED");
                }
                self.players.get_mut(username).unwrap().group = Some(group_id.clone());
                self.players
                    .get_mut(username)
                    .unwrap()
                    .invitations
                    .remove(&group_id);
                self.groups
                    .get_mut(&group_id)
                    .unwrap()
                    .members
                    .insert(username.to_string());
                Outcome {
                    response: format!("OK group={group_id}"),
                    deliveries: self
                        .group_deliveries(&group_id, format!("EVT GROUP JOIN {username}")),
                    close: false,
                }
            }
            GroupCommand::Leave => {
                if self.players[username].group.is_none() {
                    return Outcome::error(401, "NOT_IN_GROUP");
                }
                Outcome {
                    response: "OK".to_string(),
                    deliveries: self.leave_group(username),
                    close: false,
                }
            }
        }
    }

    pub(super) fn leave_group(&mut self, username: &str) -> Vec<Delivery> {
        let mut group_id = None;

        if let Some(player) = self.players.get(username) {
            group_id = player.group.clone();
        }

        if group_id.is_none() {
            for (id, group) in &self.groups {
                if group.members.contains(username) {
                    group_id = Some(id.clone());
                    break;
                }
            }
        }

        let group_id = match group_id {
            Some(id) => id,
            None => return Vec::new(),
        };
        if let Some(player) = self.players.get_mut(username) {
            player.group = None;
        }
        let group = self.groups.get_mut(&group_id).unwrap();
        group.members.remove(username);
        if group.members.is_empty() {
            self.groups.remove(&group_id);
            return Vec::new();
        }
        if group.leader == username {
            let mut names: Vec<String> = group.members.iter().cloned().collect();
            names.sort();
            group.leader = names[0].clone();
        }
        self.group_deliveries(&group_id, format!("EVT GROUP LEAVE {username}"))
    }
}
