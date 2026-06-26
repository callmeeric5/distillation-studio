import { type CSSProperties, useEffect, useMemo, useRef, useState } from 'react';

import {
  listFlyInMaps,
  loadFlyInSimulation,
  type FlyInAssignment,
  type FlyInConnection,
  type FlyInDifficulty,
  type FlyInMapSummary,
  type FlyInMove,
  type FlyInSimulation,
  type FlyInTurn,
  type FlyInZone,
} from './api/flyIn';
import { CollapsibleDescription } from './components/CollapsibleDescription';

const difficulties: FlyInDifficulty[] = ['easy', 'medium', 'hard', 'challenger'];
const displayWidth = 1200;
const displayHeight = 760;
const plotPaddingX = 72;
const plotPaddingY = 72;

const zonePalette = {
  blocked: { fill: '#3d3d3a', stroke: '#171715' },
  end: { fill: '#c96442', stroke: '#8a4429' },
  normal: { fill: '#fffdf8', stroke: '#8b8174' },
  priority: { fill: '#dfe8f0', stroke: '#36546d' },
  restricted: { fill: '#f3dfd2', stroke: '#8a4429' },
  start: { fill: '#e8eee0', stroke: '#49603b' },
};

type DronePosition = {
  droneId: number;
  x: number;
  y: number;
  zoneName: string;
  label: string;
  count?: number;
  state: 'moving' | 'waiting' | 'delivered' | 'idle' | 'in_transit';
  reason?: string;
};

type ReplayFrame = {
  phase: 'initial' | 'arrival' | 'movement';
  turn?: FlyInTurn;
  turnNumber: number;
};

type DroneRuntime = {
  activeMove?: FlyInMove;
  reason?: string;
  state: DronePosition['state'];
  zoneName: string;
};

function fallbackMaps(): Record<FlyInDifficulty, FlyInMapSummary[]> {
  return { challenger: [], easy: [], hard: [], medium: [] };
}

function mapValue(map: FlyInMapSummary) {
  return `${map.difficulty}/${map.filename}`;
}

function findMap(
  maps: Record<FlyInDifficulty, FlyInMapSummary[]>,
  value: string,
) {
  return difficulties.flatMap((difficulty) => maps[difficulty]).find((item) => mapValue(item) === value) ?? null;
}

type DisplayLayout = {
  connectionStroke: {
    normal: number;
    wide: number;
  };
  flagScale: number;
  height: number;
  xValues: number[];
  yValues: number[];
  width: number;
  zoneRadius: number;
};

function getZonePoint(
  zone: FlyInZone,
  layout: DisplayLayout,
) {
  const xIndex = Math.max(layout.xValues.indexOf(zone.position.x), 0);
  const yIndex = Math.max(layout.yValues.indexOf(zone.position.y), 0);
  const plotMaxWidth = displayWidth - plotPaddingX * 2;
  const plotMaxHeight = displayHeight - plotPaddingY * 2;
  const columnGap = layout.xValues.length <= 1 ? 0 : plotMaxWidth / (layout.xValues.length - 1);
  const rowGap = layout.yValues.length <= 1 ? 0 : plotMaxHeight / (layout.yValues.length - 1);
  const graphWidth = columnGap * Math.max(layout.xValues.length - 1, 0);
  const graphHeight = rowGap * Math.max(layout.yValues.length - 1, 0);
  const x = plotPaddingX + (plotMaxWidth - graphWidth) / 2 + xIndex * columnGap;
  const y = plotPaddingY + (plotMaxHeight - graphHeight) / 2 + yIndex * rowGap;
  return { x, y };
}

function waitReasonLabel(reason?: string) {
  return (reason ?? 'idle').replaceAll('_', ' ');
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <span className="min-w-24 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-2 text-center text-sm text-[#5e5d59]">
      <b className="text-[#171715]">{value}</b> {label}
    </span>
  );
}

function midpoint(
  from: { x: number; y: number },
  to: { x: number; y: number },
) {
  return {
    x: (from.x + to.x) / 2,
    y: (from.y + to.y) / 2,
  };
}

function connectionKey(source: string, target: string) {
  return [source, target].sort().join('\u0000');
}

function buildConnectionSet(connections: FlyInConnection[]) {
  return new Set(connections.map((connection) => connectionKey(connection.source, connection.target)));
}

function hasConnection(edges: Set<string>, source: string, target: string) {
  return edges.has(connectionKey(source, target));
}

function buildReplayFrames(simulation: FlyInSimulation | null): ReplayFrame[] {
  if (!simulation) return [{ phase: 'initial', turnNumber: 0 }];
  const frames: ReplayFrame[] = [{ phase: 'initial', turnNumber: 0 }];
  for (const turn of simulation.turns) {
    frames.push({ phase: 'arrival', turn, turnNumber: turn.turn });
    frames.push({ phase: 'movement', turn, turnNumber: turn.turn });
  }
  return frames;
}

function scanTraceIssues(simulation: FlyInSimulation | null, edges: Set<string>) {
  if (!simulation) return [];
  return simulation.turns.flatMap((turn) =>
    turn.moves
      .filter((move) => !hasConnection(edges, move.from_zone, move.to_zone))
      .map((move) => `turn ${turn.turn}: D${move.drone_id} ${move.from_zone}->${move.to_zone}`),
  );
}

function buildDronePositions({
  assignments,
  edges,
  frame,
  points,
  simulation,
}: {
  assignments: FlyInAssignment[];
  edges: Set<string>;
  frame: ReplayFrame;
  points: Map<string, { x: number; y: number }>;
  simulation: FlyInSimulation;
}): DronePosition[] {
  const runtimes = new Map<number, DroneRuntime>();
  for (const assignment of assignments) {
    runtimes.set(assignment.drone_id, {
      state: 'idle',
      zoneName: assignment.path[0] ?? simulation.stats.start,
    });
  }

  if (frame.phase !== 'initial') {
    for (const turn of simulation.turns) {
      if (turn.turn > frame.turnNumber) break;

      for (const runtime of runtimes.values()) {
        runtime.reason = undefined;
        if (runtime.activeMove && runtime.activeMove.arrives_turn <= turn.turn) {
          runtime.zoneName = runtime.activeMove.to_zone;
          runtime.activeMove = undefined;
          runtime.state = runtime.zoneName === simulation.stats.end ? 'delivered' : 'idle';
        }
      }

      if (turn.turn === frame.turnNumber && frame.phase === 'arrival') break;

      for (const move of turn.moves) {
        const runtime = runtimes.get(move.drone_id);
        if (!runtime || !hasConnection(edges, move.from_zone, move.to_zone)) continue;
        runtime.reason = move.reason;
        if (move.duration > 1) {
          runtime.activeMove = move;
          runtime.state = 'in_transit';
        } else {
          runtime.zoneName = move.to_zone;
          runtime.activeMove = undefined;
          runtime.state = move.to_zone === simulation.stats.end ? 'delivered' : 'moving';
        }
      }

      if (turn.turn === frame.turnNumber && frame.phase === 'movement') break;
    }
  }

  const waitingByDrone = new Map(frame.turn?.waiting.map((waiting) => [waiting.drone_id, waiting]));
  return assignments.map((assignment) => {
    const runtime = runtimes.get(assignment.drone_id);
    const waiting = waitingByDrone.get(assignment.drone_id);
    const zoneName = runtime?.zoneName ?? assignment.path[0] ?? simulation.stats.start;
    const basePoint = points.get(zoneName) ?? { x: 0, y: 0 };
    const activeMove = runtime?.activeMove;

    if (activeMove) {
      const from = points.get(activeMove.from_zone) ?? basePoint;
      const to = points.get(activeMove.to_zone) ?? basePoint;
      const point = midpoint(from, to);
      return {
        droneId: assignment.drone_id,
        label: `D${assignment.drone_id}`,
        reason: waiting?.reason ?? runtime?.reason,
        state: 'in_transit',
        x: point.x,
        y: point.y,
        zoneName: `in_transit:${assignment.drone_id}`,
      };
    }

    const state =
      waiting?.reason === 'delivered' || zoneName === simulation.stats.end
        ? 'delivered'
        : waiting
          ? 'waiting'
          : runtime?.state ?? 'idle';
    return {
      droneId: assignment.drone_id,
      label: `D${assignment.drone_id}`,
      reason: waiting?.reason,
      state,
      x: basePoint.x,
      y: basePoint.y,
      zoneName,
    };
  });
}

function centeredDroneOffset(drones: DronePosition[], drone: DronePosition, radius: number) {
  const zoneDrones = drones
    .filter((item) => item.zoneName === drone.zoneName)
    .sort((first, second) => first.droneId - second.droneId);
  const index = zoneDrones.findIndex((item) => item.droneId === drone.droneId);
  if (zoneDrones.length <= 1 || index < 0) return { x: 0, y: 0 };
  const offsetRadius = Math.min(radius * 0.28, 2 + zoneDrones.length * 0.38);
  const angle = (index / zoneDrones.length) * Math.PI * 2 - Math.PI / 2;
  return {
    x: Math.cos(angle) * offsetRadius,
    y: Math.sin(angle) * offsetRadius,
  };
}

function visibleDronePositions(drones: DronePosition[], simulation: FlyInSimulation | null) {
  if (!simulation) return [];
  const endpointZones = new Set([simulation.stats.start, simulation.stats.end]);
  const endpointCounts = new Map<string, number>();
  for (const drone of drones) {
    if (endpointZones.has(drone.zoneName)) {
      endpointCounts.set(drone.zoneName, (endpointCounts.get(drone.zoneName) ?? 0) + 1);
    }
  }
  const seenEndpoints = new Set<string>();
  const visible: DronePosition[] = [];
  for (const drone of drones) {
    if (!endpointZones.has(drone.zoneName)) {
      visible.push(drone);
      continue;
    }
    if (seenEndpoints.has(drone.zoneName)) continue;
    seenEndpoints.add(drone.zoneName);
    visible.push({ ...drone, count: endpointCounts.get(drone.zoneName) });
  }
  return visible;
}

export function FlyInStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [maps, setMaps] = useState<Record<FlyInDifficulty, FlyInMapSummary[]>>(fallbackMaps);
  const [selectedMapValue, setSelectedMapValue] = useState('');
  const [simulation, setSimulation] = useState<FlyInSimulation | null>(null);
  const [cursor, setCursor] = useState(0);
  const [speed, setSpeed] = useState(700);
  const [status, setStatus] = useState('Loading Fly_In maps...');
  const [isBusy, setIsBusy] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTurnsExpanded, setIsTurnsExpanded] = useState(true);
  const didLoadMaps = useRef(false);
  const autoRunMap = useRef('');

  const selectedMap = useMemo(() => findMap(maps, selectedMapValue), [maps, selectedMapValue]);
  const replayFrames = useMemo(() => buildReplayFrames(simulation), [simulation]);
  const currentFrame = replayFrames[Math.min(cursor, replayFrames.length - 1)] ?? replayFrames[0];
  const currentTurn = currentFrame?.turn;
  const currentActivity = currentTurn
    ? `${currentFrame.phase} · ${currentTurn.moves.length} moves, ${currentTurn.waiting.length} waiting`
    : simulation
      ? 'Initial state'
      : 'Idle';

  const displayLayout = useMemo<DisplayLayout>(() => {
    const zones = simulation?.zones ?? [];
    const xValues = Array.from(new Set(zones.map((zone) => zone.position.x))).sort((first, second) => first - second);
    const yValues = Array.from(new Set(zones.map((zone) => zone.position.y))).sort((first, second) => second - first);
    const denseX = xValues.length;
    const zoneRadius = denseX > 18 ? 20 : denseX > 12 ? 19 : denseX > 8 ? 21 : 25;
    return {
      connectionStroke: {
        normal: denseX > 18 ? 1.5 : 2,
        wide: denseX > 18 ? 3 : 4,
      },
      flagScale: denseX > 18 ? 0.82 : denseX > 12 ? 0.92 : 1.05,
      height: displayHeight,
      xValues,
      yValues,
      width: displayWidth,
      zoneRadius: denseX > 18 ? 22 : zoneRadius,
    };
  }, [simulation]);

  const connectionEdges = useMemo(
    () => buildConnectionSet(simulation?.connections ?? []),
    [simulation],
  );
  const traceIssues = useMemo(
    () => scanTraceIssues(simulation, connectionEdges),
    [connectionEdges, simulation],
  );

  const points = useMemo(() => {
    const next = new Map<string, { x: number; y: number }>();
    for (const zone of simulation?.zones ?? []) next.set(zone.name, getZonePoint(zone, displayLayout));
    return next;
  }, [displayLayout, simulation]);

  const dronePositions = useMemo(() => {
    if (!simulation) return [];
    return buildDronePositions({
      assignments: simulation.assignments,
      edges: connectionEdges,
      frame: currentFrame,
      points,
      simulation,
    });
  }, [connectionEdges, currentFrame, points, simulation]);
  const renderedDronePositions = useMemo(
    () => visibleDronePositions(dronePositions, simulation),
    [dronePositions, simulation],
  );
  const droneTransitionStyle = useMemo(
    () => ({ '--fly-in-transition-ms': `${Math.max(80, Math.floor(speed * 0.42))}ms` }) as CSSProperties,
    [speed],
  );

  async function loadMaps() {
    setIsBusy(true);
    try {
      const data = await listFlyInMaps();
      setMaps(data.maps);
      const first = difficulties.flatMap((difficulty) => data.maps[difficulty])[0];
      if (first) {
        setSelectedMapValue(mapValue(first));
        setStatus('Choose a map and run the simulation.');
      } else {
        setStatus('No Fly_In maps found.');
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not load maps.');
    } finally {
      setIsBusy(false);
    }
  }

  async function runSelectedMap(map = selectedMap) {
    if (!map) return;
    setIsBusy(true);
    setIsPlaying(false);
    setStatus(`Running ${map.path}...`);
    try {
      const data = await loadFlyInSimulation(map.difficulty, map.filename);
      setSimulation(data);
      setCursor(0);
      setStatus(`${data.map.name} returned ${data.stats.turns} turns for ${data.stats.drones} drones.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Fly_In simulation failed.');
    } finally {
      setIsBusy(false);
    }
  }

  function play() {
    if (!simulation || isPlaying || cursor >= replayFrames.length - 1) return;
    setIsPlaying(true);
  }

  useEffect(() => {
    if (didLoadMaps.current) return;
    didLoadMaps.current = true;
    void loadMaps();
  }, []);

  useEffect(() => {
    if (!selectedMap || simulation) return;
    const key = mapValue(selectedMap);
    if (autoRunMap.current === key) return;
    autoRunMap.current = key;
    void runSelectedMap(selectedMap);
  }, [selectedMap, simulation]);

  useEffect(() => {
    if (!isPlaying || !simulation) return undefined;
    if (cursor >= replayFrames.length - 1) return undefined;
    const timer = window.setTimeout(() => {
      setCursor((current) => {
        const next = current + 1;
        if (next >= replayFrames.length - 1) setIsPlaying(false);
        return next;
      });
    }, Math.max(120, Math.floor(speed / 2)));
    return () => window.clearTimeout(timer);
  }, [cursor, isPlaying, replayFrames.length, simulation, speed]);

  useEffect(() => {
    if (traceIssues.length > 0) {
      console.warn('Fly_In trace contains moves without a matching connection:', traceIssues);
    }
  }, [traceIssues]);

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="grid min-h-[720px] lg:grid-cols-[minmax(0,1fr)_390px]">
        <section className="flex min-w-0 flex-col">
          <header className="flex flex-col gap-5 border-b border-[#ece8dc] p-5 sm:flex-row sm:items-center sm:justify-between lg:p-7">
            <div className="max-w-3xl">
              <button
                className="mb-5 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#30302e] transition hover:bg-[#faf9f5]"
                onClick={onBack}
                type="button"
              >
                Back to gallery
              </button>
              <p className="text-sm font-semibold text-[#c96442]">42 Fly_In</p>
              <h3 className="mt-2 font-serif text-4xl leading-tight text-[#171715] sm:text-5xl">Fly In</h3>
              <CollapsibleDescription
                className="mt-5"
                fullText={fullDescription ?? description}
                previewText={description}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Metric label="turns" value={simulation?.stats.turns ?? 0} />
              <Metric label="turn" value={currentFrame?.turnNumber ?? 0} />
              <Metric label="drones" value={simulation?.stats.drones ?? 0} />
            </div>
          </header>

          <div className="flex min-h-0 flex-1 bg-[#f4f1e8] p-4 lg:p-5">
            <section className="relative flex min-h-[720px] w-full flex-1 overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
              <div className="pointer-events-none absolute right-5 top-5 z-10 rounded-lg border border-[#ded8ca] bg-[#fffdf8]/95 px-4 py-4 shadow-sm">
                <p className="mb-3 text-sm font-extrabold text-[#30302e]">Zone type</p>
                <div className="grid gap-2 text-xs font-bold text-[#5e5d59]">
                  {[
                    ['Normal', zonePalette.normal],
                    ['Priority', zonePalette.priority],
                    ['Restricted', zonePalette.restricted],
                    ['Blocked', zonePalette.blocked],
                  ].map(([label, palette]) => (
                    <span className="flex items-center gap-2" key={label as string}>
                      <span
                        className="h-3.5 w-6 border"
                        style={{
                          backgroundColor: (palette as { fill: string }).fill,
                          borderColor: (palette as { stroke: string }).stroke,
                        }}
                      />
                      {label as string}
                    </span>
                  ))}
                </div>
              </div>
              <svg
                className="h-full min-h-[720px] w-full flex-1"
                role="img"
                aria-label="Fly_In route simulation"
                viewBox={`0 0 ${displayLayout.width} ${displayLayout.height}`}
              >
                <rect width={displayLayout.width} height={displayLayout.height} fill="#fbfaf6" />
                {simulation?.connections.map((connection) => {
                  const source = points.get(connection.source);
                  const target = points.get(connection.target);
                  if (!source || !target) return null;
                  return (
                    <g key={`${connection.source}-${connection.target}`}>
                      <line
                        stroke="#d2c9b7"
                        strokeLinecap="round"
                        strokeWidth={connection.max_link_capacity > 1 ? displayLayout.connectionStroke.wide : displayLayout.connectionStroke.normal}
                        x1={source.x}
                        x2={target.x}
                        y1={source.y}
                        y2={target.y}
                      />
                      <text
                        fill="#8b8174"
                        fontSize={displayLayout.zoneRadius > 22 ? 12 : 10}
                        fontWeight="700"
                        textAnchor="middle"
                        x={(source.x + target.x) / 2}
                        y={(source.y + target.y) / 2 - 8}
                      >
                        {connection.max_link_capacity}
                      </text>
                    </g>
                  );
                })}

                {simulation?.zones.map((zone) => {
                  const point = points.get(zone.name);
                  if (!point) return null;
                  const palette = zone.role === 'start' || zone.role === 'end' ? zonePalette[zone.role] : zonePalette[zone.zone_type];
                  return (
                    <g key={zone.name}>
                      <circle cx={point.x} cy={point.y} fill={palette.fill} r={displayLayout.zoneRadius} stroke={palette.stroke} strokeWidth="2" />
                      <text fill="#171715" fontSize={displayLayout.zoneRadius > 22 ? 13 : 11} fontWeight="800" textAnchor="middle" x={point.x} y={point.y + 4}>
                        {zone.role === 'start' ? 'S' : zone.role === 'end' ? 'E' : zone.max_drones}
                      </text>
                    </g>
                  );
                })}

                {renderedDronePositions.map((drone) => {
                  const offset = centeredDroneOffset(renderedDronePositions, drone, displayLayout.zoneRadius);
                  const fill =
                    drone.state === 'moving'
                      ? '#c96442'
                      : drone.state === 'in_transit'
                        ? '#6f6a5f'
                        : drone.state === 'delivered'
                          ? '#49603b'
                          : '#36546d';
                  return (
                    <g
                      className={`fly-in-drone-flag ${
                        drone.state === 'waiting' || drone.state === 'in_transit' ? 'fly-in-waiting-drone' : ''
                      } ${isPlaying ? '' : 'fly-in-drone-snap'}`}
                      key={drone.droneId}
                      style={{
                        ...droneTransitionStyle,
                        transform: `translate(${drone.x + offset.x}px, ${drone.y + offset.y}px)`,
                      }}
                    >
                      <g transform={`scale(${displayLayout.flagScale})`}>
                        <line stroke="#30302e" strokeLinecap="round" strokeWidth="2" x1="-5" x2="-5" y1="-10" y2="8" />
                        <path
                          d="M-4 -10 H10 L6 -4 L10 2 H-4 Z"
                          fill={fill}
                          stroke="#fffdf8"
                          strokeLinejoin="round"
                          strokeWidth="2"
                        />
                        <text fill="#fffdf8" fontSize="6" fontWeight="900" textAnchor="middle" x="2" y="-4">
                          {drone.count && drone.count > 1 ? drone.count : drone.droneId}
                        </text>
                      </g>
                      {drone.reason && drone.reason !== 'delivered' ? (
                        <title>{`${drone.label}: ${waitReasonLabel(drone.reason)}`}</title>
                      ) : null}
                    </g>
                  );
                })}
              </svg>
            </section>
          </div>
        </section>

        <aside
          className="scroll-mt-24 flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0"
          id="fly-in-config"
        >
          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Map</span>
            <select
              className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
              disabled={isBusy}
              onChange={(event) => {
                setIsPlaying(false);
                setSelectedMapValue(event.target.value);
                setSimulation(null);
              }}
              value={selectedMapValue}
            >
              {difficulties.map((difficulty) => (
                <optgroup key={difficulty} label={difficulty}>
                  {maps[difficulty].map((map) => (
                    <option key={mapValue(map)} value={mapValue(map)}>
                      {map.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">
              Animation speed <b className="text-[#30302e]">{speed} ms</b>
            </span>
            <input
              className="accent-[#c96442]"
              max={1600}
              min={160}
              onChange={(event) => setSpeed(Number(event.target.value))}
              step={40}
              type="range"
              value={speed}
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Replay step</span>
            <input
              className="accent-[#c96442]"
              disabled={!simulation}
              max={Math.max(replayFrames.length - 1, 0)}
              min={0}
              onChange={(event) => {
                setIsPlaying(false);
                setCursor(Number(event.target.value));
              }}
              type="range"
              value={cursor}
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <button
              className="min-h-11 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8] disabled:opacity-60"
              disabled={!simulation || cursor >= replayFrames.length - 1 || isPlaying}
              onClick={play}
              type="button"
            >
              Play
            </button>
            <button
              className="min-h-11 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8] disabled:opacity-60"
              disabled={!isPlaying}
              onClick={() => setIsPlaying(false)}
              type="button"
            >
              Pause
            </button>
            <button
              className="col-span-2 min-h-11 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8] disabled:opacity-60"
              disabled={!simulation}
              onClick={() => {
                setIsPlaying(false);
                setCursor(0);
              }}
              type="button"
            >
              Reset
            </button>
          </div>

          <p className="min-h-6 text-sm font-medium text-[#5e5d59]">{status}</p>
          {traceIssues.length > 0 ? (
            <p className="rounded-xl border border-[#e5c9bd] bg-[#fff6ed] p-3 text-sm font-semibold text-[#8a4429]">
              {traceIssues.length} trace move{traceIssues.length === 1 ? '' : 's'} skipped because no connection exists.
            </p>
          ) : null}
          <p className="rounded-xl border border-[#e8e3d6] bg-[#fffdf8] p-3 text-sm font-semibold text-[#30302e]">
            {currentActivity}
          </p>

          <section className="overflow-hidden rounded-xl border border-[#e8e3d6] bg-[#fffdf8]">
            <button
              aria-expanded={isTurnsExpanded}
              className="flex min-h-12 w-full items-center justify-between gap-3 px-4 text-left text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8]"
              onClick={() => setIsTurnsExpanded((current) => !current)}
              type="button"
            >
              <span>Turns · {simulation?.turns.length ?? 0}</span>
              <span className="text-[#8a4429]">{isTurnsExpanded ? 'Hide' : 'Show'}</span>
            </button>
            {isTurnsExpanded ? (
              <ol className="grid max-h-72 gap-1 overflow-auto border-t border-[#e8e3d6] p-3 pl-8 font-mono text-sm">
                {(simulation?.turns ?? []).map((turn) => (
                  <li
                    className={`rounded-md px-2 py-1 ${
                      turn.turn === currentFrame?.turnNumber ? 'bg-[#f3dfd2] font-bold text-[#8a4429]' : 'text-[#777267]'
                    }`}
                    key={turn.turn}
                  >
                    <span>turn {turn.turn}: </span>
                    <span>{turn.formatted || 'wait'}</span>
                  </li>
                ))}
              </ol>
            ) : null}
          </section>
        </aside>
      </div>
    </article>
  );
}
