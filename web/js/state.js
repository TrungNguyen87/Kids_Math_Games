/**
 * Session and player state - the port of utils/state.py and utils/profiles.py.
 *
 * The level/streak/badge rules are unchanged from the Streamlit app, so a
 * child's difficulty curve feels identical. What changed is where the data
 * lives: st.session_state (server memory) and logs/player_profiles.json
 * (server disk) become localStorage in the child's own browser.
 *
 * That is a real improvement, not just a port:
 *   - progress survives a reload, a redeploy, and being offline;
 *   - nothing about a child ever leaves their device, which is exactly what
 *     docs/PLATFORM_ROADMAP.md section 6 asks for.
 *
 * Every read and write is wrapped: Safari private mode throws on the first
 * localStorage access, and a maths game must not white-screen because of it.
 */
export const MIN_LEVEL = 0; // level 0 is the extra-gentle warm-up tier
export const MAX_LEVEL = 5;
export const LEVEL_UP_STREAK = 3; // correct answers in a row needed to level up
export const LEVEL_DOWN_STREAK = 2; // wrong answers in a row that drop a level
export const SESSION_GOAL_MINUTES = 45;

export const GAME_KEYS = [
  "tafel",
  "breuken",
  "meten",
  "procenten",
  "algebra",
  "meetkunde",
  "verhoudingen",
  "getallen",
  // Speed and logic games share the same level/streak/badge machinery, so
  // they count towards "tried every game" like the rest.
  "bliksem",
  "logica",
  "code",
  "jacht",
];

const PROFILES_KEY = "kmg.profiles";
const CURRENT_KEY = "kmg.currentPlayer";
const PREFS_KEY = "kmg.prefs";

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    // Storage full or blocked: the session keeps working in memory, it just
    // won't be there next time.
    return false;
  }
}

function freshLevels() {
  return Object.fromEntries(GAME_KEYS.map((k) => [k, MIN_LEVEL]));
}

function freshGameStreaks() {
  return Object.fromEntries(GAME_KEYS.map((k) => [k, { correct: 0, wrong: 0 }]));
}

function randomId() {
  return Math.random().toString(16).slice(2, 10);
}

const listeners = new Set();

/** Subscribe to any state change; returns an unsubscribe function. */
export function onStateChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function emitChange() {
  listeners.forEach((fn) => fn(state));
}

const prefs = readJson(PREFS_KEY, {});

export const state = {
  // Session-scoped: these start fresh every time the app is opened, exactly
  // as they did per browser session in Streamlit.
  sessionId: randomId(),
  sessionStart: Date.now(),
  streaks: 0,
  questionsAnswered: 0,
  correctAnswered: 0,
  gameStreaks: freshGameStreaks(),
  // Player-scoped: restored from the saved profile below.
  playerName: "",
  totalScore: 0,
  levels: freshLevels(),
  badges: [],
  gamesTried: new Set(),
  // Device preference, not tied to a player.
  soundEnabled: prefs.soundEnabled !== false,
};

// ---------------------------------------------------------------------------
// Profiles
// ---------------------------------------------------------------------------

/** All saved profiles, keyed by player name ("" is the no-name-yet player). */
export function allProfiles() {
  return readJson(PROFILES_KEY, {});
}

export function profileNames() {
  return Object.keys(allProfiles())
    .filter((n) => n !== "")
    .sort((a, b) => a.localeCompare(b));
}

export function saveCurrentProfile() {
  const profiles = allProfiles();
  profiles[state.playerName] = {
    totalScore: state.totalScore,
    levels: { ...state.levels },
    badges: [...state.badges],
    gamesTried: [...state.gamesTried].sort(),
    updatedAt: new Date().toISOString(),
  };
  writeJson(PROFILES_KEY, profiles);
  try {
    localStorage.setItem(CURRENT_KEY, state.playerName);
  } catch {
    /* see writeJson */
  }
}

/** Restore a saved profile into the live state. Returns true if one existed. */
export function applyProfile(name) {
  const profile = allProfiles()[name];
  state.playerName = name;
  if (!profile) {
    state.totalScore = 0;
    state.levels = freshLevels();
    state.badges = [];
    state.gamesTried = new Set();
    state.gameStreaks = freshGameStreaks();
    emitChange();
    return false;
  }
  state.totalScore = profile.totalScore || 0;
  state.levels = Object.fromEntries(
    GAME_KEYS.map((k) => [k, profile.levels?.[k] ?? MIN_LEVEL]),
  );
  state.badges = profile.badges || [];
  state.gamesTried = new Set(profile.gamesTried || []);
  state.gameStreaks = freshGameStreaks();
  emitChange();
  return true;
}

/** Called once at boot: pick up whoever was playing last on this device. */
export function restoreLastPlayer() {
  let name = "";
  try {
    name = localStorage.getItem(CURRENT_KEY) || "";
  } catch {
    /* see readJson */
  }
  return applyProfile(name);
}

export function setPlayerName(name) {
  const trimmed = (name || "").trim().slice(0, 40);
  if (trimmed === state.playerName) return false;
  // Keep whatever the previous player earned before switching over.
  saveCurrentProfile();
  const existed = applyProfile(trimmed);
  saveCurrentProfile();
  return existed;
}

export function setSoundEnabled(enabled) {
  state.soundEnabled = !!enabled;
  writeJson(PREFS_KEY, { ...readJson(PREFS_KEY, {}), soundEnabled: state.soundEnabled });
  emitChange();
}

// ---------------------------------------------------------------------------
// Scoring and adaptive difficulty (unchanged rules from utils/state.py)
// ---------------------------------------------------------------------------

export function addScore(points = 10) {
  state.totalScore += points;
  state.streaks += 1;
  emitChange();
}

export function resetStreak() {
  state.streaks = 0;
  emitChange();
}

export function getLevel(gameKey) {
  return state.levels[gameKey] ?? MIN_LEVEL;
}

export function setLevel(gameKey, level) {
  const clamped = Math.max(MIN_LEVEL, Math.min(MAX_LEVEL, level));
  state.levels[gameKey] = clamped;
  // Starting fresh at the new level: the old streak counters described a
  // difficulty the child is no longer playing.
  state.gameStreaks[gameKey] = { correct: 0, wrong: 0 };
  emitChange();
  return clamped;
}

/**
 * Update the counters after an answer and adapt the level: up after
 * LEVEL_UP_STREAK correct in a row, down after LEVEL_DOWN_STREAK wrong.
 * @returns {{leveledUp: boolean, leveledDown: boolean}}
 */
export function registerAttempt(gameKey, isCorrect) {
  state.questionsAnswered += 1;
  state.gamesTried.add(gameKey);
  const streak = (state.gameStreaks[gameKey] ??= { correct: 0, wrong: 0 });
  let leveledUp = false;
  let leveledDown = false;
  const currentLevel = getLevel(gameKey);

  if (isCorrect) {
    state.correctAnswered += 1;
    streak.correct += 1;
    streak.wrong = 0;
    if (streak.correct >= LEVEL_UP_STREAK && currentLevel < MAX_LEVEL) {
      setLevel(gameKey, currentLevel + 1);
      leveledUp = true;
    }
  } else {
    streak.wrong += 1;
    streak.correct = 0;
    if (streak.wrong >= LEVEL_DOWN_STREAK && currentLevel > MIN_LEVEL) {
      setLevel(gameKey, currentLevel - 1);
      leveledDown = true;
    }
  }
  emitChange();
  return { leveledUp, leveledDown };
}

/** Count a question without touching the difficulty (used by timed rounds). */
export function countAttemptOnly(gameKey, isCorrect) {
  state.questionsAnswered += 1;
  state.gamesTried.add(gameKey);
  if (isCorrect) state.correctAnswered += 1;
  emitChange();
}

export function sessionElapsedMinutes() {
  return (Date.now() - state.sessionStart) / 60000;
}

export function sessionAccuracy() {
  if (!state.questionsAnswered) return 0;
  return (100 * state.correctAnswered) / state.questionsAnswered;
}

/** Wipe every profile on this device (parent dashboard "danger zone"). */
export function clearAllProfiles() {
  try {
    localStorage.removeItem(PROFILES_KEY);
    localStorage.removeItem(CURRENT_KEY);
  } catch {
    /* see writeJson */
  }
  state.totalScore = 0;
  state.levels = freshLevels();
  state.badges = [];
  state.gamesTried = new Set();
  state.gameStreaks = freshGameStreaks();
  state.streaks = 0;
  state.questionsAnswered = 0;
  state.correctAnswered = 0;
  emitChange();
}
