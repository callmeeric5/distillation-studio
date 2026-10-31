import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  fetchTapWorld,
  sendTapCommand,
  tapSessionUrl,
  type TapLook,
  type TapServerMessage,
  type TapWorld,
} from './api/tap';
import { CollapsibleDescription } from './components/CollapsibleDescription';

type SessionState = 'idle' | 'connecting' | 'connected' | 'disconnected';
type ChatLine = { channel: string; player: string; message: string };
type Point = { x: number; y: number };

const buttonClass =
  'min-h-10 rounded-lg bg-[#c96442] px-4 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334] disabled:cursor-not-allowed disabled:opacity-45';
const secondaryButtonClass =
  'min-h-9 rounded-lg border border-[#d8d1c2] bg-[#f4f1e8] px-3 text-sm font-semibold text-[#5e5d59] transition hover:bg-white hover:text-[#171715] disabled:cursor-not-allowed disabled:opacity-45';

const PLAYER_COLORS = ['#c96442', '#6e7c4b', '#264653', '#b98b45', '#8a6254'];
const ADJECTIVES = ['Brave', 'Calm', 'Curious', 'Kind', 'Lucky', 'Swift'];
const NOUNS = ['Badger', 'Finch', 'Fox', 'Heron', 'Moth', 'Otter'];

function randomPlayerName() {
  const adjective = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)];
  return `${adjective}${noun}${Math.floor(10 + Math.random() * 90)}`;
}

function parseJsonResponse(line: string) {
  if (!line.startsWith('OK ')) return null;
  const payload = line.slice(3);
  if (!payload.startsWith('{') && !payload.startsWith('[')) return null;
  try {
    return JSON.parse(payload) as unknown;
  } catch {
    return null;
  }
}

function itemLabel(id: string, world: TapWorld | null) {
  return world?.items[id]?.name ?? id;
}

function buildGraph(world: TapWorld) {
  const ids = Object.keys(world.rooms);
  const outer = ids.filter((id) => id !== world.start_room);
  const positions: Record<string, Point> = {
    [world.start_room]: { x: 360, y: 220 },
  };
  outer.forEach((id, index) => {
    const angle = (Math.PI * 2 * index) / outer.length - Math.PI / 2;
    positions[id] = { x: 360 + Math.cos(angle) * 245, y: 220 + Math.sin(angle) * 155 };
  });
  const seen = new Set<string>();
  const edges: Array<{ from: string; to: string }> = [];
  for (const [from, room] of Object.entries(world.rooms)) {
    for (const to of Object.values(room.exits)) {
      const key = [from, to].sort().join('|');
      if (!seen.has(key) && positions[to]) {
        seen.add(key);
        edges.push({ from, to });
      }
    }
  }
  return { edges, positions };
}

function PlayerToken({ color, name, offset = 0 }: { color: string; name: string; offset?: number }) {
  const x = offset * 18;
  return (
    <g aria-label={name} transform={`translate(${x} 0)`}>
      <circle cx="0" cy="-17" fill={color} r="8" stroke="#fffdf8" strokeWidth="3" />
      <path d="M-10 10 Q-9-7 0-8 Q9-7 10 10Z" fill={color} stroke="#fffdf8" strokeWidth="3" />
    </g>
  );
}

function GameMap({
  currentRoom,
  onMove,
  players,
  visited,
  world,
}: {
  currentRoom: string;
  onMove: (destination: string) => void;
  players: string[];
  visited: Set<string>;
  world: TapWorld;
}) {
  const graph = useMemo(() => buildGraph(world), [world]);
  const reachable = new Set(Object.values(world.rooms[currentRoom]?.exits ?? {}));
  const currentPosition = graph.positions[currentRoom] ?? graph.positions[world.start_room];

  return (
    <svg aria-label="Clickable TAP world" className="h-auto min-h-[360px] w-full" role="img" viewBox="0 0 720 440">
      <defs>
        <filter height="160%" id="tap-shadow" width="160%" x="-30%" y="-30%">
          <feDropShadow dx="0" dy="4" floodColor="#42382f" floodOpacity="0.14" stdDeviation="5" />
        </filter>
      </defs>
      {graph.edges.map(({ from, to }) => (
        <line
          className="tap-map-edge stroke-[#d8d1c2]"
          key={`${from}-${to}`}
          strokeDasharray="5 8"
          strokeLinecap="round"
          strokeWidth="3"
          x1={graph.positions[from].x}
          x2={graph.positions[to].x}
          y1={graph.positions[from].y}
          y2={graph.positions[to].y}
        />
      ))}

      {Object.entries(world.rooms).map(([id, room]) => {
        const active = id === currentRoom;
        const canMove = reachable.has(id);
        const known = visited.has(id) || active;
        const position = graph.positions[id];
        return (
          <g
            aria-label={`${room.name}${canMove ? ', available destination' : ''}`}
            className={canMove ? 'tap-map-node cursor-pointer' : 'tap-map-node'}
            key={id}
            onClick={() => canMove && onMove(id)}
            onKeyDown={(event) => {
              if (canMove && (event.key === 'Enter' || event.key === ' ')) onMove(id);
            }}
            opacity={known || canMove ? 1 : 0.42}
            role={canMove ? 'button' : undefined}
            tabIndex={canMove ? 0 : -1}
            transform={`translate(${position.x} ${position.y})`}
          >
            {canMove ? <circle className="fill-[#f3dfd2]" r="32" /> : null}
            <circle
              className={active ? 'fill-[#c96442] stroke-[#fffdf8]' : 'fill-[#fffdf8] stroke-[#bdb5a5]'}
              filter={active ? 'url(#tap-shadow)' : undefined}
              r={active ? 25 : 18}
              strokeWidth="4"
            />
            {canMove ? <circle className="fill-none stroke-[#c96442]" r="27" strokeDasharray="4 5" strokeWidth="2" /> : null}
            <text
              className="tap-map-label pointer-events-none fill-[#171715] text-[12px] font-bold"
              dominantBaseline="hanging"
              textAnchor="middle"
              y={active ? 34 : 27}
            >
              {room.name}
            </text>
          </g>
        );
      })}

      <g
        className="tap-player-marker"
        style={{ transform: `translate(${currentPosition.x}px, ${currentPosition.y - 35}px)` }}
      >
        {players.slice(0, 5).map((player, index) => (
          <PlayerToken color={PLAYER_COLORS[index % PLAYER_COLORS.length]} key={player} name={player} offset={index} />
        ))}
      </g>
    </svg>
  );
}

export function TapStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const socketRef = useRef<WebSocket | null>(null);
  const authenticatedRef = useRef(false);
  const [world, setWorld] = useState<TapWorld | null>(null);
  const [worldError, setWorldError] = useState('');
  const [session, setSession] = useState<SessionState>('idle');
  const [username, setUsername] = useState(randomPlayerName);
  const [notice, setNotice] = useState('Your traveller is ready.');
  const [look, setLook] = useState<TapLook | null>(null);
  const [visited, setVisited] = useState<Set<string>>(new Set());
  const [inventory, setInventory] = useState<string[]>([]);
  const [online, setOnline] = useState(0);
  const [chatInput, setChatInput] = useState('');
  const [chatLines, setChatLines] = useState<ChatLine[]>([]);
  const [protocolLines, setProtocolLines] = useState<string[]>([]);

  useEffect(() => {
    void fetchTapWorld().then(setWorld).catch((error: unknown) => {
      setWorldError(error instanceof Error ? error.message : 'Could not load the TAP world.');
    });
  }, []);

  const send = useCallback((line: string) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    sendTapCommand(socket, line);
    setProtocolLines((current) => [...current.slice(-199), `→ ${line}`]);
    return true;
  }, []);

  const refresh = useCallback(() => {
    for (const command of ['LOOK', 'INVENTORY', 'WHO']) send(command);
  }, [send]);

  const processLine = useCallback(
    (line: string) => {
      setProtocolLines((current) => [...current.slice(-199), `← ${line}`]);
      if (line === 'OK hello proto=1') {
        setNotice('The shared world answered. Joining…');
        send(`CONNECT ${username.trim()}`);
        return;
      }
      if (line === 'OK connected') {
        authenticatedRef.current = true;
        setSession('connected');
        setNotice(`Welcome, ${username.trim()}. Pick a neighboring place.`);
        refresh();
        return;
      }
      if (line.startsWith('ERR ')) {
        const reason = line.split(' ').slice(2).join(' ').replaceAll('_', ' ');
        setNotice(reason || 'The world could not do that.');
        if (!authenticatedRef.current) {
          setSession('disconnected');
          socketRef.current?.close();
        }
        return;
      }
      const playerCount = line.match(/^OK players=(\d+)$/)?.[1];
      if (playerCount) setOnline(Number(playerCount));
      const statsCount = line.match(/^EVT STATS players=(\d+)$/)?.[1];
      if (statsCount) setOnline(Number(statsCount));

      const chat = line.match(/^EVT (GLOBAL|ROOM|GROUP) CHAT (\S+) (.*)$/);
      if (chat) {
        setChatLines((current) => [
          ...current.slice(-9),
          { channel: chat[1], player: chat[2], message: chat[3] },
        ]);
        return;
      }

      if (line.startsWith('OK room=')) setNotice('Walking to the next place…');
      if (line.startsWith('OK taken=')) setNotice('You picked up a shared object. Other players can no longer take it.');
      if (line.startsWith('OK dropped=')) setNotice('You left the object here for another player.');

      const json = parseJsonResponse(line);
      if (json && typeof json === 'object') {
        if (Array.isArray(json)) {
          if (json.every((entry) => typeof entry === 'string')) setInventory(json as string[]);
          return;
        }
        const value = json as Record<string, unknown>;
        if ('room' in value) {
          const nextLook = value as unknown as TapLook;
          setLook(nextLook);
          setVisited((current) => new Set(current).add(nextLook.room.id));
          setNotice(`You arrived at ${nextLook.room.name}.`);
          return;
        }
      }
      if (line.includes(' PRESENCE ')) send('LOOK');
    },
    [refresh, send, username],
  );

  const processLineRef = useRef(processLine);
  useEffect(() => {
    processLineRef.current = processLine;
  }, [processLine]);

  const disconnect = useCallback((sendQuit = true) => {
    const socket = socketRef.current;
    if (socket && sendQuit && authenticatedRef.current && socket.readyState === WebSocket.OPEN) {
      sendTapCommand(socket, 'QUIT');
    }
    socket?.close();
    socketRef.current = null;
    authenticatedRef.current = false;
    setSession('disconnected');
    setLook(null);
    setInventory([]);
  }, []);

  useEffect(() => () => disconnect(false), [disconnect]);

  function connect() {
    const name = username.trim();
    if (!/^\S{1,24}$/u.test(name)) {
      setNotice('Use 1–24 characters without spaces.');
      return;
    }
    disconnect(false);
    setSession('connecting');
    setNotice('Opening the path to the shared world…');
    setChatLines([]);
    setProtocolLines([]);
    setVisited(new Set());
    const socket = new WebSocket(tapSessionUrl());
    socketRef.current = socket;
    socket.onmessage = (event) => {
      let message: TapServerMessage;
      try {
        message = JSON.parse(String(event.data)) as TapServerMessage;
      } catch {
        setNotice('The gateway returned an unreadable message.');
        return;
      }
      if (message.kind === 'protocol') processLineRef.current(message.line);
      else setNotice(message.detail);
    };
    socket.onerror = () => setNotice('The shared world is not reachable right now.');
    socket.onclose = () => {
      socketRef.current = null;
      authenticatedRef.current = false;
      setSession('disconnected');
    };
  }

  function move(destination: string) {
    if (!look) return;
    const direction = Object.entries(look.room.exits).find(([, roomId]) => roomId === destination)?.[0];
    if (!direction || !send(`MOVE ${direction}`)) return;
    send('LOOK');
    send('WHO');
  }

  function take(item: string) {
    if (!send(`TAKE ${item}`)) return;
    send('LOOK');
    send('INVENTORY');
  }

  function drop(item: string) {
    if (!send(`DROP ${item}`)) return;
    send('LOOK');
    send('INVENTORY');
  }

  function sendChat() {
    const message = chatInput.trim();
    if (!message) return;
    send(`CHAT GLOBAL ${message}`);
    setChatInput('');
  }

  const connected = session === 'connected';
  const currentRoom = look?.room.id ?? world?.start_room ?? '';
  const tourDone = visited.size >= 3;
  const foundObject = inventory.length > 0;
  const latestChats = chatLines.slice(-3);

  return (
    <article className="grid gap-6">
      <div className="flex flex-col gap-5 border-b border-[#ece8dc] pb-7 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <button className={secondaryButtonClass} onClick={onBack} type="button">← Back to gallery</button>
          <p className="mt-5 text-sm font-semibold text-[#c96442]">A tiny shared-world game</p>
          <h3 className="mt-2 font-serif text-4xl text-[#171715] sm:text-5xl">The Answer Protocol</h3>
          <CollapsibleDescription
            className="mt-4 max-w-3xl"
            fullText={fullDescription ?? description}
            previewText="Pick a name, click a neighboring place, and meet whoever is sharing the Rust-owned world with you."
          />
        </div>
        <div className="rounded-2xl border border-[#e8e3d6] bg-[#f4f1e8] px-5 py-4 text-sm">
          <p className="font-semibold text-[#171715]">Live world</p>
          <p className="mt-1 text-[#5e5d59]">{online} traveller{online === 1 ? '' : 's'} online</p>
        </div>
      </div>

      {!connected ? (
        <section className="mx-auto w-full max-w-xl rounded-[28px] border border-[#e8e3d6] bg-[#fffdf8] p-7 shadow-[0_22px_70px_rgba(76,63,48,0.08)] sm:p-9">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#f3dfd2] text-3xl">●</div>
          <p className="mt-5 text-center text-sm font-semibold text-[#c96442]">Your traveller is ready</p>
          <h4 className="mt-2 text-center font-serif text-3xl text-[#171715]">Step into the village</h4>
          <p className="mx-auto mt-3 max-w-md text-center leading-7 text-[#5e5d59]">
            The world is shared with everyone online and starts fresh when the last traveller leaves.
          </p>
          <label className="mt-6 block text-sm font-semibold text-[#171715]" htmlFor="tap-player-name">Traveller name</label>
          <div className="mt-2 grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
            <input
              autoComplete="nickname"
              className="min-h-11 rounded-lg border border-[#d8d1c2] bg-[#faf9f5] px-4 text-[#171715] outline-none focus:border-[#c96442]"
              disabled={session === 'connecting'}
              id="tap-player-name"
              maxLength={24}
              onChange={(event) => setUsername(event.target.value)}
              onKeyDown={(event) => { if (event.key === 'Enter') connect(); }}
              value={username}
            />
            <button className={buttonClass} disabled={session === 'connecting' || !world} onClick={connect} type="button">
              {session === 'connecting' ? 'Joining…' : 'Play now'}
            </button>
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            <button className="text-sm font-semibold text-[#8b8174] underline decoration-dotted underline-offset-4" onClick={() => setUsername(randomPlayerName())} type="button">Roll another name</button>
            <span className="text-xs text-[#8b8174]">No account needed</span>
          </div>
          <p className="mt-5 rounded-lg bg-[#f4f1e8] px-4 py-3 text-sm text-[#5e5d59]" role="status">{worldError || notice}</p>
        </section>
      ) : world && look ? (
        <>
          <section className="overflow-hidden rounded-[28px] border border-[#e8e3d6] bg-[#fffdf8] shadow-[0_22px_70px_rgba(76,63,48,0.08)]">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#ece8dc] bg-[#f4f1e8] px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="relative flex h-3 w-3"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#6e7c4b] opacity-50" /><span className="relative inline-flex h-3 w-3 rounded-full bg-[#6e7c4b]" /></span>
                <p className="text-sm font-semibold text-[#171715]">Shared world is live</p>
                <span className="text-sm text-[#8b8174]">{online} online</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-[#fffdf8] px-3 py-1 text-sm font-semibold text-[#5e5d59]">● {username}</span>
                <button className={secondaryButtonClass} onClick={() => disconnect()} type="button">Leave world</button>
              </div>
            </div>

            <div className="grid lg:grid-cols-[minmax(0,1fr)_330px]">
              <div className="relative min-w-0 border-b border-[#ece8dc] bg-[radial-gradient(circle_at_50%_42%,#fffdf8_0,#f7f2e8_70%)] p-4 lg:border-b-0 lg:border-r sm:p-6">
                <div className="absolute left-5 top-5 z-10 max-w-[230px] rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]/95 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#c96442]">Tiny tour</p>
                  <p className={`mt-2 text-sm font-semibold ${tourDone ? 'text-[#4d5f39]' : 'text-[#5e5d59]'}`}>{tourDone ? '✓' : '○'} Visit three places <span className="font-normal">({Math.min(visited.size, 3)}/3)</span></p>
                  <p className={`mt-1 text-sm font-semibold ${foundObject ? 'text-[#4d5f39]' : 'text-[#5e5d59]'}`}>{foundObject ? '✓' : '○'} Pick up a shared object</p>
                </div>
                <GameMap currentRoom={currentRoom} onMove={move} players={look.players} visited={visited} world={world} />
                <p className="text-center text-sm text-[#8b8174]">Dashed rings show where you can move next.</p>
              </div>

              <aside className="grid content-start gap-5 p-5 sm:p-6">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#c96442]">You are here</p>
                  <h4 className="mt-2 font-serif text-3xl text-[#171715]">{look.room.name}</h4>
                  <p className="mt-3 text-sm leading-6 text-[#5e5d59]">{look.room.description}</p>
                  <p className="mt-4 text-sm font-semibold text-[#171715]">Choose your next stop</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(look.room.exits).map(([direction, destination]) => (
                      <button className={secondaryButtonClass} key={direction} onClick={() => move(destination)} type="button">
                        {direction} → {world.rooms[destination]?.name ?? destination}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl bg-[#f4f1e8] p-4">
                  <p className="text-sm font-semibold text-[#171715]">In this place</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {look.players.map((player, index) => (
                      <span className="inline-flex items-center gap-2 rounded-full bg-[#fffdf8] px-3 py-1.5 text-xs font-semibold text-[#5e5d59]" key={player}>
                        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PLAYER_COLORS[index % PLAYER_COLORS.length] }} />{player}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold text-[#171715]">Shared objects</p>
                  <div className="mt-2 grid gap-2">
                    {look.items.length ? look.items.map((item) => (
                      <button className="flex min-h-11 items-center justify-between rounded-xl border border-[#dec6b5] bg-[#fbede5] px-4 text-left text-sm font-semibold text-[#8a4429] transition hover:-translate-y-0.5" key={item} onClick={() => take(item)} type="button">
                        <span>✦ {itemLabel(item, world)}</span><span>Pick up</span>
                      </button>
                    )) : <p className="text-sm text-[#8b8174]">No loose objects here right now.</p>}
                  </div>
                  {inventory.length ? (
                    <div className="mt-3 rounded-xl border border-[#c9d1bd] bg-[#eef3e8] p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-[#4d5f39]">You are carrying</p>
                      {inventory.map((item) => <button className="mt-2 mr-2 rounded-full bg-[#fffdf8] px-3 py-1 text-xs font-semibold text-[#4d5f39]" key={item} onClick={() => drop(item)} title="Leave this object in the current place" type="button">{itemLabel(item, world)} ×</button>)}
                    </div>
                  ) : null}
                </div>

                <p className="rounded-xl bg-[#f4f1e8] px-4 py-3 text-sm leading-6 text-[#5e5d59]" role="status">{notice}</p>
              </aside>
            </div>

            <div className="border-t border-[#ece8dc] bg-[#fffdf8] p-5 sm:p-6">
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#c96442]">Campfire chat</p><p className="mt-1 text-sm text-[#5e5d59]">Messages appear for everyone in the shared world.</p></div>
              <div className="mt-4 flex min-h-16 flex-wrap items-end gap-3">
                {latestChats.length ? latestChats.map((line, index) => (
                  <div className="max-w-sm rounded-2xl rounded-bl-sm bg-[#f4f1e8] px-4 py-3" key={`${line.player}-${index}`}>
                    <p className="text-xs font-semibold text-[#c96442]">{line.player}</p><p className="mt-1 text-sm text-[#3d3d3a]">{line.message}</p>
                  </div>
                )) : <p className="text-sm text-[#8b8174]">The campfire is quiet. Say hello.</p>}
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
                <input aria-label="Chat message" className="min-h-11 rounded-xl border border-[#d8d1c2] bg-[#faf9f5] px-4 outline-none focus:border-[#c96442]" maxLength={900} onChange={(event) => setChatInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') sendChat(); }} placeholder="Say something to the world…" value={chatInput} />
                <button className={buttonClass} disabled={!chatInput.trim()} onClick={sendChat} type="button">Send bubble</button>
              </div>
            </div>
          </section>

          <details className="min-w-0 rounded-2xl border border-[#e8e3d6] bg-[#fffdf8] p-5">
            <summary className="cursor-pointer font-semibold text-[#171715]">See the protocol underneath the game</summary>
            <p className="mt-2 text-sm text-[#5e5d59]">Every click above becomes a real TAP command handled by the Rust server.</p>
            <div className="mt-4 h-56 overflow-y-auto rounded-xl bg-[#171715] p-4 font-mono text-xs leading-6 text-[#f4efe6]">
              {protocolLines.map((line, index) => <div className="break-all whitespace-pre-wrap" key={`${line}-${index}`}>{line}</div>)}
            </div>
          </details>
        </>
      ) : (
        <p className="rounded-2xl border border-[#e8e3d6] bg-[#fffdf8] p-6 text-[#5e5d59]">Looking around the shared world…</p>
      )}
    </article>
  );
}
