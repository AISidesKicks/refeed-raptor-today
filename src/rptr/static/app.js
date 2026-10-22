const state = {
  places: [],
  place: null,
  capabilities: {},
  script: [],
  turn: 1,
  docs: [],
  activeTab: "ask",
  mode: "raptor",
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      if (payload.detail) message = payload.detail;
    } catch (error) {
      // Keep the status text.
    }
    throw new Error(message);
  }
  return response.json();
}

function setText(id, value) {
  const element = $(id);
  if (element) element.textContent = value;
}

function make(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function clear(element) {
  element.replaceChildren();
}

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function formatNumber(value, digits = 3) {
  return Number(value || 0).toFixed(digits);
}

function renderResults(container, results) {
  clear(container);
  if (!results || results.length === 0) {
    container.append(make("p", "replay-note", "No matching passages."));
    return;
  }
  for (const hit of results) {
    const article = make("article", "hit");
    const head = make("div", "hit-head");
    const modelHit = hit.node_id !== undefined;
    if (modelHit) {
      head.append(make("strong", "", `${hit.title} (${hit.node_id})`));
      const meta = make("span", "");
      meta.append(make("span", "kind", hit.kind));
      meta.append(
        document.createTextNode(
          ` level ${hit.level} - score ${formatNumber(hit.score, 4)}` +
            (hit.relevance !== undefined
              ? ` - relevant ${formatPercent(hit.relevance)}`
              : "")
        )
      );
      head.append(meta);
    } else {
      head.append(make("strong", "", `${hit.doc_title} (${hit.doc_id})`));
      head.append(make("span", "", `#${hit.rank} score ${hit.score}`));
    }
    article.append(head);
    if (modelHit && hit.doc_ids && hit.doc_ids.length) {
      article.append(make("p", "replay-note", `Sources: ${hit.doc_ids.join(", ")}`));
    }
    article.append(make("p", "", hit.text));
    container.append(article);
  }
}

function renderTrace(container, trace) {
  clear(container);
  if (!trace || trace.length === 0) return;
  container.append(make("h2", "trace-title", "Decision trace"));
  for (const item of trace) {
    const article = make("article", "trace-step");
    const head = make("div", "trace-head");
    head.append(make("strong", "", item.step.replaceAll("_", " ")));
    if (item.attempt !== undefined) {
      head.append(make("span", "stats", `attempt ${item.attempt}`));
    }
    if (item.band) {
      head.append(make("span", `badge ${item.band === "high" ? "hit" : item.band === "middle" ? "" : "miss"}`, item.band));
    }
    if (item.delegated) {
      head.append(make("span", "kind", "delegated to LFM"));
    } else if (item.source) {
      head.append(make("span", "kind", item.source));
    }
    article.append(head);

    const bits = [];
    if (item.kept !== undefined) bits.push(`kept ${item.kept}`);
    if (item.scored !== undefined) bits.push(`scored ${item.scored}`);
    if (item.probability !== undefined) bits.push(`p ${formatNumber(item.probability, 4)}`);
    if (item.confidence !== undefined) bits.push(`confidence ${formatNumber(item.confidence, 4)}`);
    if (item.accepted !== undefined) bits.push(item.accepted ? "accepted" : "rejected");
    if (item.choice) bits.push(`choice ${item.choice}`);
    if (item.queries) bits.push(`query ${item.queries.join(" | ")}`);
    if (item.mode) bits.push(item.mode);
    if (item.hits !== undefined) bits.push(`${item.hits} candidates`);
    if (item.latency_ms !== undefined) bits.push(`${item.latency_ms} ms`);
    if (bits.length) article.append(make("p", "trace-body", bits.join(" - ")));

    if (item.scores && item.scores.length) {
      const details = document.createElement("details");
      details.append(make("summary", "trace-body", `${item.scores.length} relevance decisions`));
      for (const score of item.scores) {
        details.append(
          make(
            "p",
            "trace-body",
            `${score.node_id}: p ${formatNumber(score.probability, 4)} ` +
              `confidence ${formatNumber(score.confidence, 3)}`
          )
        );
      }
      article.append(details);
    }
    container.append(article);
  }
}

function renderCitationChips(container, citations) {
  if (!citations || !citations.length) return;
  const box = make("div", "citations");
  for (const citation of citations) {
    const label = citation.doc_ids && citation.doc_ids.length
      ? `${citation.node_id} (${citation.doc_ids.join(", ")})`
      : citation.node_id;
    box.append(make("span", "citation", label));
  }
  container.append(box);
}

function metaLine(payload) {
  const parts = [`refeeds ${payload.refeeds || 0}`];
  parts.push(`${payload.timings ? payload.timings.total_ms : 0} ms`);
  if (payload.trace_id) parts.push(`trace ${payload.trace_id.slice(0, 12)}`);
  return parts.join(" - ");
}

function renderAnswer(payload) {
  const answer = $("answer");
  answer.hidden = false;
  answer.replaceChildren();
  answer.append(make("p", "answer-text", payload.answer || "No answer."));
  if (payload.warning) {
    answer.append(make("p", "warning", `Warning: ${payload.warning}`));
  }
  if (payload.note) {
    answer.append(make("p", "replay-note", payload.note));
  }
  renderCitationChips(answer, payload.citations);
  if (payload.mode === "raptor") {
    answer.append(
      make("p", "replay-note", metaLine(payload))
    );
  }
}

function renderStarter(questions) {
  const container = $("starter");
  clear(container);
  for (const question of questions) {
    const button = make("button", "", question);
    button.type = "button";
    button.addEventListener("click", () => {
      $("question").value = question;
      $("ask-form").requestSubmit();
    });
    container.append(button);
  }
}

function socketAsk(payload) {
  return new Promise((resolve, reject) => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/ask`);
    let settled = false;
    const timer = setTimeout(() => {
      finish(() => reject(new Error("websocket timeout")));
    }, 180000);

    function finish(callback) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      try {
        socket.close();
      } catch (error) {
        // The socket may already be closed.
      }
      callback();
    }

    socket.addEventListener("open", () => {
      socket.send(JSON.stringify(payload));
    });
    socket.addEventListener("message", (event) => {
      finish(() => {
        try {
          resolve(JSON.parse(event.data));
        } catch (error) {
          reject(error);
        }
      });
    });
    socket.addEventListener("error", () => {
      finish(() => reject(new Error("websocket failed")));
    });
    socket.addEventListener("close", () => {
      if (!settled) {
        finish(() => reject(new Error("websocket closed")));
      }
    });
  });
}

async function askQuestion(event) {
  event.preventDefault();
  const question = $("question").value.trim();
  if (!question || !state.place) return;
  const answer = $("answer");
  answer.hidden = false;
  answer.replaceChildren(make("p", "answer-text", state.mode === "raptor" ? "Retrieving, deciding, and writing..." : "Searching..."));
  clear($("results"));
  clear($("trace"));

  const payload = { place_id: state.place.id, question, limit: 8, mode: state.mode };
  try {
    let response;
    try {
      response = await socketAsk(payload);
    } catch (socketError) {
      response = await api("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    if (response.error) throw new Error(response.error);
    renderAnswer(response);
    renderResults($("results"), response.results);
    renderTrace($("trace"), response.trace);
  } catch (error) {
    answer.replaceChildren(make("p", "answer-text", `Error: ${error.message}`));
  }
}

function renderReplayEmpty() {
  $("replay-body").replaceChildren(
    make("p", "replay-note", "No script turns for this place.")
  );
  setText("replay-label", "Turn 0");
  $("replay-prev").disabled = true;
  $("replay-next").disabled = true;
}

async function showTurn(turn) {
  if (!state.place || state.script.length === 0) {
    renderReplayEmpty();
    return;
  }
  const index = state.script.findIndex((item) => item.turn === turn);
  const scriptTurn = state.script[index >= 0 ? index : 0];
  state.turn = scriptTurn.turn;
  setText("replay-label", `Turn ${scriptTurn.turn} of ${state.script.length}`);
  $("replay-prev").disabled = index <= 0;
  $("replay-next").disabled = index < 0 || index >= state.script.length - 1;

  const mode = $("replay-mode").value;
  const body = $("replay-body");
  body.replaceChildren(
    make(
      "p",
      "replay-note",
      mode === "recorded" ? "Loading recorded run..." : mode === "raptor" ? "Running the loop..." : "Searching..."
    )
  );
  try {
    const replay = await api(`/api/places/${state.place.id}/replay/${state.turn}?mode=${mode}`);
    body.replaceChildren();
    body.append(make("p", "replay-visitor", replay.visitor));
    if (replay.note) body.append(make("p", "replay-note", replay.note));
    if (replay.expect) {
      const expected = make("p", "replay-expected");
      expected.append(make("strong", "", "Expected: "));
      expected.append(document.createTextNode(replay.expect));
      body.append(expected);
    }
    if (replay.result) {
      const answer = make("div", "answer");
      answer.append(make("p", "answer-text", replay.result.answer));
      if (replay.result.warning) {
        answer.append(make("p", "warning", `Warning: ${replay.result.warning}`));
      }
      renderCitationChips(answer, replay.result.citations);
      if (replay.result.timings) {
        answer.append(
          make("p", "replay-note", metaLine(replay.result))
        );
      }
      body.append(answer);
      const results = make("div", "results");
      renderResults(results, replay.result.results);
      body.append(results);
      const trace = make("div", "trace");
      renderTrace(trace, replay.result.trace);
      body.append(trace);
    } else {
      const results = make("div", "results");
      renderResults(results, replay.hits);
      body.append(results);
    }
  } catch (error) {
    body.replaceChildren(make("p", "replay-note", `Error: ${error.message}`));
  }
}

function moveTurn(delta) {
  const index = state.script.findIndex((item) => item.turn === state.turn);
  const next = state.script[index + delta];
  if (next) showTurn(next.turn);
}

async function loadDocument(docId) {
  if (!state.place) return;
  const body = $("doc-body");
  body.replaceChildren(make("p", "replay-note", "Loading..."));
  try {
    const doc = await api(`/api/places/${state.place.id}/documents/${docId}`);
    body.replaceChildren();
    body.append(make("h2", "", doc.title));
    body.append(
      make(
        "p",
        "doc-metadata",
        `${doc.id} - ${doc.category} - ${doc.date} - ${doc.author}`
      )
    );
    for (const line of String(doc.text || "").split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (trimmed.startsWith("## ")) body.append(make("h3", "", trimmed.slice(3)));
      else if (trimmed.startsWith("# ")) body.append(make("h2", "", trimmed.slice(2)));
      else body.append(make("p", "", trimmed));
    }
  } catch (error) {
    body.replaceChildren(make("p", "replay-note", `Error: ${error.message}`));
  }
}

async function loadDocs(placeId) {
  const docs = await api(`/api/places/${placeId}/documents`);
  state.docs = docs;
  const list = $("doc-list");
  clear(list);
  for (const doc of docs) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.append(document.createTextNode(doc.title));
    button.append(
      make("span", "doc-meta", `${doc.id} - ${doc.category} - ${doc.words} words`)
    );
    button.addEventListener("click", () => loadDocument(doc.id));
    item.append(button);
    list.append(item);
  }
  if (docs.length) loadDocument(docs[0].id);
}

async function checkHealth() {
  const badge = $("health");
  try {
    const health = await api("/api/health");
    if (health.reachable) {
      badge.className = "health up";
      badge.textContent = `router warm - ${health.models.length} models`;
    } else {
      badge.className = "health down";
      badge.textContent = "router offline";
    }
  } catch (error) {
    badge.className = "health down";
    badge.textContent = "router offline";
  }
}

async function loadPlace(placeId) {
  const detail = await api(`/api/places/${placeId}`);
  state.place = detail;
  state.capabilities = detail.capabilities || {};
  state.script = detail.script || [];
  state.turn = 1;
  state.docs = [];
  setText(
    "stats",
    `${detail.documents.toLocaleString()} documents, ` +
      `${detail.words.toLocaleString()} words, ` +
      `${detail.questions} questions, ${detail.license}`
  );

  const canRaptor = Boolean(state.capabilities.raptor);
  const modeSelect = $("ask-mode");
  modeSelect.disabled = !canRaptor;
  state.mode = canRaptor ? "raptor" : "keyword";
  modeSelect.value = state.mode;
  const canRecorded = Boolean(state.capabilities.recorded);
  const replayMode = $("replay-mode");
  replayMode.querySelector('option[value="recorded"]').disabled = !canRecorded;
  replayMode.value = canRecorded ? "recorded" : state.mode;
  $("run-eval-raptor").disabled = !canRaptor;
  setText(
    "ask-mode-note",
    canRaptor
      ? state.capabilities.tree
        ? "embeddings and summary tree ready"
        : "embeddings ready, tree not built"
      : "run pixi run embed to enable the model path"
  );

  renderStarter(detail.starter_questions || []);
  $("replay-body").replaceChildren();
  setText("replay-label", "Turn 1");
  $("replay-prev").disabled = true;
  $("replay-next").disabled = true;
  $("answer").hidden = true;
  clear($("answer"));
  clear($("results"));
  clear($("trace"));
  $("eval-summary").hidden = true;
  clear($("eval-summary"));
  clear($("eval-table"));
  await loadDocs(placeId);
}

async function runEval(mode) {
  if (!state.place) return;
  const summary = $("eval-summary");
  summary.hidden = false;
  summary.replaceChildren(
    make("p", "answer-text", mode === "raptor" ? "Embedding 50 questions and searching the tree..." : "Running keyword baseline...")
  );
  clear($("eval-table"));
  $("run-eval").disabled = true;
  $("run-eval-raptor").disabled = true;
  try {
    const result = await api(`/api/places/${state.place.id}/eval/${mode}`);
    summary.replaceChildren();
    summary.append(
      make(
        "p",
        "answer-text",
        `${result.mode === "raptor" ? "RAPTOR" : "Keyword"} on ${result.questions} questions: ` +
          `Recall@5 ${formatPercent(result.recall_at_5)}, ` +
          `Recall@10 ${formatPercent(result.recall_at_10)}, ` +
          `Recall@20 ${formatPercent(result.recall_at_20)}, ` +
          `MRR ${formatNumber(result.mrr)}.`
      )
    );
    renderEvalTable(result.results);
  } catch (error) {
    summary.replaceChildren(make("p", "answer-text", `Error: ${error.message}`));
  } finally {
    $("run-eval").disabled = false;
    $("run-eval-raptor").disabled = !state.capabilities.raptor;
  }
}

function renderEvalTable(results) {
  const wrap = $("eval-table");
  clear(wrap);
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const label of ["Question", "Type", "Gold", "First rank"]) {
    headRow.append(make("th", "", label));
  }
  thead.append(headRow);
  table.append(thead);
  const tbody = document.createElement("tbody");
  for (const result of results) {
    const row = document.createElement("tr");
    row.append(make("td", "", result.question));
    row.append(make("td", "", result.type));
    row.append(make("td", "", result.gold.join(", ")));
    const rankCell = document.createElement("td");
    if (result.first_rank) {
      rankCell.append(make("span", "badge hit", `#${result.first_rank}`));
      if (result.first_kind) {
        rankCell.append(make("span", "kind", result.first_kind));
      }
    } else {
      rankCell.append(make("span", "badge miss", "miss"));
    }
    row.append(rankCell);
    tbody.append(row);
  }
  table.append(tbody);
  wrap.append(table);
}

function showTab(name) {
  state.activeTab = name;
  for (const button of document.querySelectorAll(".tab")) {
    button.classList.toggle("active", button.dataset.tab === name);
  }
  for (const section of ["ask", "replay", "corpus", "eval"]) {
    $(`tab-${section}`).hidden = section !== name;
  }
  if (name === "replay") showTurn(state.turn);
  if (name === "corpus" && state.place && state.docs.length === 0) {
    loadDocs(state.place.id);
  }
}

async function loadPlaces() {
  const places = await api("/api/places");
  state.places = places;
  const select = $("place");
  clear(select);
  for (const place of places) {
    const option = document.createElement("option");
    option.value = place.id;
    option.textContent = place.title;
    select.append(option);
  }
  if (places.length === 0) {
    setText("stats", "No places found.");
    return;
  }
  select.value = places[0].id;
  await loadPlace(places[0].id);
}

document.addEventListener("DOMContentLoaded", () => {
  for (const button of document.querySelectorAll(".tab")) {
    button.addEventListener("click", () => showTab(button.dataset.tab));
  }
  $("ask-form").addEventListener("submit", askQuestion);
  $("place").addEventListener("change", (event) => loadPlace(event.target.value));
  $("ask-mode").addEventListener("change", (event) => {
    state.mode = event.target.value;
  });
  $("replay-mode").addEventListener("change", () => showTurn(state.turn));
  $("replay-prev").addEventListener("click", () => moveTurn(-1));
  $("replay-next").addEventListener("click", () => moveTurn(1));
  $("run-eval").addEventListener("click", () => runEval("keyword"));
  $("run-eval-raptor").addEventListener("click", () => runEval("raptor"));
  $("run-eval-raptor").disabled = true;
  checkHealth();
  loadPlaces().catch((error) => setText("stats", `Error: ${error.message}`));
});
