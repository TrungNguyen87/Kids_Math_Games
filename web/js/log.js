/**
 * Attempt logging for the parent dashboard - the port of utils/gamelog.py.
 *
 * In the Streamlit app every answered question went to st.session_state.log
 * plus a CSV on the server's disk, with the caveat (documented there) that
 * the on-disk history vanished on redeploy.
 *
 * Here the history lives in the browser's localStorage instead, which means:
 *   - it survives redeploys, because deploying no longer touches it;
 *   - it never leaves the child's device;
 *   - it is per device and per browser, which is the honest tradeoff and the
 *     reason the dashboard keeps a prominent CSV export.
 *
 * The row shape is byte-for-byte the one gamelog.py writes, so a CSV exported
 * from the Streamlit version and one exported from here open the same way.
 */
import { state } from "./state.js";
import { t } from "./i18n.js";

const LOG_KEY = "kmg.attempts";
// Roughly a school year of daily play at 60 questions a day. Old rows are
// dropped from the front rather than letting localStorage hit its quota and
// start throwing mid-lesson.
const MAX_ROWS = 12000;

export const FIELDNAMES = [
  "timestamp",
  "session_id",
  "player",
  "game",
  "level",
  "question",
  "student_answer",
  "correct_answer",
  "result",
  "points",
];

let rows = load();

function load() {
  try {
    const raw = localStorage.getItem(LOG_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persist() {
  try {
    localStorage.setItem(LOG_KEY, JSON.stringify(rows));
  } catch {
    // Quota exceeded: drop the oldest quarter and try once more, so play
    // continues rather than the log silently breaking.
    rows = rows.slice(Math.floor(rows.length / 4));
    try {
      localStorage.setItem(LOG_KEY, JSON.stringify(rows));
    } catch {
      /* give up on persistence; the in-memory log still works this session */
    }
  }
}

/** Record one answered question. */
export function logAttempt({
  gameKey,
  gameName,
  level,
  question,
  studentAnswer,
  correctAnswer,
  isCorrect,
  points,
}) {
  const entry = {
    timestamp: new Date().toISOString().slice(0, 19),
    session_id: state.sessionId,
    player: state.playerName || t("dash.player_unknown"),
    game: gameName,
    level,
    question,
    student_answer: studentAnswer == null ? "" : String(studentAnswer),
    correct_answer: String(correctAnswer),
    // "fout" (not "wrong") on purpose: it is what gamelog.py wrote, and a
    // parent may have CSV exports from both versions side by side.
    result: isCorrect ? "correct" : "fout",
    points: isCorrect ? points : 0,
    game_key: gameKey,
  };
  rows.push(entry);
  if (rows.length > MAX_ROWS) rows = rows.slice(rows.length - MAX_ROWS);
  persist();
  return entry;
}

/** Every attempt ever recorded on this device, oldest first. */
export function allAttempts() {
  return rows;
}

/** Just this browser session's attempts. */
export function sessionAttempts() {
  return rows.filter((r) => r.session_id === state.sessionId);
}

export function clearHistory() {
  rows = [];
  try {
    localStorage.removeItem(LOG_KEY);
  } catch {
    /* nothing to do - the in-memory log is already empty */
  }
}

function csvCell(value) {
  const text = value == null ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function toCsv(entries) {
  const lines = [FIELDNAMES.join(",")];
  for (const entry of entries) {
    lines.push(FIELDNAMES.map((f) => csvCell(entry[f])).join(","));
  }
  return lines.join("\n");
}

/** Hand the browser a CSV file to save. */
export function downloadCsv(filename, csv) {
  // The BOM is what makes Excel open a UTF-8 CSV with the accented Dutch
  // question text intact instead of as mojibake.
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
