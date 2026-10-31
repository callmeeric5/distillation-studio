pub const MAX_LINE_BYTES: usize = 1024;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Command {
    Connect(String),
    Look,
    Move(String),
    Chat { channel: String, message: String },
    Who,
    Group(GroupCommand),
    Take(String),
    Drop(String),
    Inventory,
    Talk(String),
    Attack(String),
    Defend,
    Flee,
    Status,
    Quest(String),
    Quests,
    Quit,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GroupCommand {
    Create,
    Invite(String),
    Join(String),
    Leave,
}

pub fn parse_command(line: &str) -> Result<Command, &'static str> {
    if line.len() > MAX_LINE_BYTES {
        return Err("LINE_TOO_LONG");
    }
    if line.chars().any(|character| character.is_control()) {
        return Err("CONTROL_CHARACTER");
    }

    let line = line.trim();
    if line.is_empty() {
        return Err("EMPTY_COMMAND");
    }

    let (name, arguments) = split_once_space(line);
    let name = name.to_ascii_uppercase();
    match name.as_str() {
        "CONNECT" => Ok(Command::Connect(required(arguments)?)),
        "LOOK" => no_arguments(arguments, Command::Look),
        "MOVE" => Ok(Command::Move(required(arguments)?)),
        "CHAT" => parse_chat(arguments),
        "WHO" => no_arguments(arguments, Command::Who),
        "GROUP" => parse_group(arguments),
        "TAKE" => Ok(Command::Take(required(arguments)?)),
        "DROP" => Ok(Command::Drop(required(arguments)?)),
        "INVENTORY" => no_arguments(arguments, Command::Inventory),
        "TALK" => Ok(Command::Talk(required(arguments)?)),
        "ATTACK" => Ok(Command::Attack(required(arguments)?)),
        "DEFEND" => no_arguments(arguments, Command::Defend),
        "FLEE" => no_arguments(arguments, Command::Flee),
        "STATUS" => no_arguments(arguments, Command::Status),
        "QUEST" => Ok(Command::Quest(required(arguments)?)),
        "QUESTS" => no_arguments(arguments, Command::Quests),
        "QUIT" => no_arguments(arguments, Command::Quit),
        _ => Err("UNKNOWN_COMMAND"),
    }
}

fn split_once_space(text: &str) -> (&str, Option<String>) {
    match text.find(char::is_whitespace) {
        Some(index) => {
            let rest = text[index..].trim();
            let arguments = if rest.is_empty() {
                None
            } else {
                Some(rest.to_string())
            };
            (text[..index].trim(), arguments)
        }
        None => (text, None),
    }
}

fn required(arguments: Option<String>) -> Result<String, &'static str> {
    arguments.ok_or("MISSING_ARGUMENT")
}

fn no_arguments(arguments: Option<String>, command: Command) -> Result<Command, &'static str> {
    if arguments.is_some() {
        Err("UNEXPECTED_ARGUMENT")
    } else {
        Ok(command)
    }
}

fn parse_chat(arguments: Option<String>) -> Result<Command, &'static str> {
    let arguments = required(arguments)?;
    let (scope, message) = split_once_space(&arguments);
    let message = required(message)?;
    let scope = scope.to_ascii_uppercase();
    if !matches!(scope.as_str(), "GLOBAL" | "ROOM" | "GROUP") {
        return Err("INVALID_CHAT_SCOPE");
    }
    Ok(Command::Chat {
        channel: scope,
        message,
    })
}

fn parse_group(arguments: Option<String>) -> Result<Command, &'static str> {
    let arguments = required(arguments)?;
    let (action, value) = split_once_space(&arguments);
    let command = match action.to_ascii_uppercase().as_str() {
        "CREATE" if value.is_none() => GroupCommand::Create,
        "INVITE" => GroupCommand::Invite(required(value)?),
        "JOIN" => GroupCommand::Join(required(value)?),
        "LEAVE" if value.is_none() => GroupCommand::Leave,
        _ => return Err("INVALID_GROUP_COMMAND"),
    };
    Ok(Command::Group(command))
}

#[cfg(test)]
mod tests {
    use super::{Command, MAX_LINE_BYTES, parse_command};

    #[test]
    fn command_names_are_case_insensitive() {
        assert_eq!(parse_command("look"), Ok(Command::Look));
        assert_eq!(
            parse_command("chat room hello there"),
            Ok(Command::Chat {
                channel: "ROOM".into(),
                message: "hello there".into(),
            })
        );
    }

    #[test]
    fn rejects_control_characters_and_oversized_lines() {
        assert_eq!(parse_command("LOOK\0"), Err("CONTROL_CHARACTER"));
        assert_eq!(
            parse_command(&"x".repeat(MAX_LINE_BYTES + 1)),
            Err("LINE_TOO_LONG")
        );
    }
}
