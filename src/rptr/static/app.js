const state = {
  places: [],
  place: null,
  script: [],
  turn: 1,
  docs: [],
  activeTab: "ask",
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

function renderResults(container, results) {
  clear(container);
  if (!results || results.length === 0) {
    container.append(make("p", "replay-note", "No matching passages."));
    return;
  }
  for (const hit of results) {
    const article = make("article", "hit");
    const head = make("div", "hit-head");
    head.append(make("strong", "", `${hit.doc_title} (${hit.doc_id})`));
    head.append(make("span", "", `#${hit.rank} score ${hit.score}`));
    article.append(head);
    article.append(make("p", "", hit.text));
    container.append(article);
  }
}

function renderAnswer(payload) {
  const answer = $("answer");
  answer.hidden = false;
  answer.replaceChildren();
  answer.append(make("p", "", payload.answer));
  if (payload.note) {
    answer.append(make("p", "replay-note", payload.note));
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
    }, 5000);

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
  answer.replaceChildren(make("p", "", "Searching..."));
  clear($("results"));

  const payload = { place_id: state.place.id, question, limit: 8 };
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
  } catch (error) {
    answer.replaceChildren(make("p", "", `Error: ${error.message}`));
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

  const body = $("replay-body");
  body.replaceChildren(make("p", "replay-note", "Loading..."));
  try {
    const replay = await api(`/api/places/${state.place.id}/replay/${state.turn}`);
    body.replaceChildren();
    body.append(make("p", "replay-visitor", replay.visitor));
    if (replay.note) body.append(make("p", "replay-note", replay.note));
    if (replay.expect) {
      const expected = make("p", "replay-expected");
      expected.append(make("strong", "", "Expected: "));
      expected.append(document.createTextNode(replay.expect));
      body.append(expected);
    }
    const results = make("div", "results");
    renderResults(results, replay.hits);
    body.append(results);
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

async function loadPlace(placeId) {
  const detail = await api(`/api/places/${placeId}`);
  state.place = detail;
  state.script = detail.script || [];
  state.turn = 1;
  state.docs = [];
  setText(
    "stats",
    `${detail.documents.toLocaleString()} documents, ` +
      `${detail.words.toLocaleString()} words, ` +
      `${detail.questions} questions, ${detail.license}`
  );
  renderStarter(detail.starter_questions || []);
  $("replay-body").replaceChildren();
  setText("replay-label", "Turn 1");
  $("replay-prev").disabled = true;
  $("replay-next").disabled = true;
  $("answer").hidden = true;
  clear($("answer"));
  clear($("results"));
  $("eval-summary").hidden = true;
  clear($("eval-summary"));
  clear($("eval-table"));
  await loadDocs(placeId);
}

async function runEval() {
  if (!state.place) return;
  const summary = $("eval-summary");
  summary.hidden = false;
  summary.replaceChildren(make("p", "", "Running keyword baseline..."));
  clear($("eval-table"));
  try {
    const result = await api(`/api/places/${state.place.id}/eval/keyword`);
    summary.replaceChildren();
    summary.append(
      make(
        "p",
        "",
        `Keyword baseline on ${result.questions} questions: ` +
          `Recall@5 ${(result.recall_at_5 * 100).toFixed(1)}%, ` +
          `Recall@10 ${(result.recall_at_10 * 100).toFixed(1)}%, ` +
          `Recall@20 ${(result.recall_at_20 * 100).toFixed(1)}%, ` +
          `MRR ${result.mrr.toFixed(3)}.`
      )
    );
    renderEvalTable(result.results);
  } catch (error) {
    summary.replaceChildren(make("p", "", `Error: ${error.message}`));
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
  $("replay-prev").addEventListener("click", () => moveTurn(-1));
  $("replay-next").addEventListener("click", () => moveTurn(1));
  $("run-eval").addEventListener("click", runEval);
  loadPlaces().catch((error) => setText("stats", `Error: ${error.message}`));
});
