const feed = document.querySelector("#chat-feed");
const statusEl = document.querySelector("#status");
const stackList = document.querySelector("#stack-list");
const composer = document.querySelector("#composer");
const promptEl = document.querySelector("#prompt");
const datasetSelectEl = document.querySelector("#dataset-select");
const loadDatasetButton = document.querySelector("#load-dataset");
const datasetSummaryEl = document.querySelector("#dataset-summary");
const documentFileEl = document.querySelector("#document-file");
const documentSummaryEl = document.querySelector("#document-summary");
const runButton = document.querySelector("#run-workflow");
const decisionGate = document.querySelector("#decision-gate");
const recommendationEl = document.querySelector("#recommendation");
const metricConsent = document.querySelector("#metric-consent");
const metricEvidence = document.querySelector("#metric-evidence");
const metricRisk = document.querySelector("#metric-risk");
const metricBand = document.querySelector("#metric-band");
const handoffList = document.querySelector("#handoff-list");

let loadedDataset = null;
let loadedDatasetDocuments = [];

const AGENTS = {
  HumanOwner: { label: "Customer Owner", initials: "CO", side: "user" },
  QuadroIntake: { label: "Quadro Intake", initials: "QCI", side: "agent" },
  QuadroEvidence: { label: "Evidence Spine", initials: "QES", side: "agent" },
  QuadroPolicy: { label: "Policy Risk", initials: "QPR", side: "agent" },
  QuadroDecision: { label: "Decision Packet", initials: "QDP", side: "agent" },
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setBusy(isBusy) {
  statusEl.textContent = isBusy ? "running" : "idle";
  statusEl.classList.toggle("running", isBusy);
  runButton.disabled = isBusy;
}

function seedFeed() {
  feed.innerHTML = `
    <article class="message system-message">
      <div class="avatar">Q</div>
      <div class="bubble">
        <div class="bubble-head">
          <strong>Quadro</strong>
          <span>workspace open</span>
        </div>
        <p>
          Ask a question, paste source material, or attach files. Quadro answers
          normal questions directly; customer review packets run through the agent
          handoff chain and write an audit trail.
        </p>
      </div>
    </article>
  `;
}

async function runWorkflow(path) {
  const message = promptEl.value.trim();
  setBusy(true);
  renderPending(message);

  try {
    const documents = await collectDocuments();
    const body = { message, documents };
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    renderWorkflow(payload);
    promptEl.value = "";
    statusEl.textContent = "complete";
  } catch (error) {
    feed.insertAdjacentHTML(
      "beforeend",
      `<article class="message system-message error-message">
        <div class="avatar">!</div>
        <div class="bubble">
          <div class="bubble-head"><strong>Run blocked</strong></div>
          <p>${escapeHtml(error.message)}</p>
        </div>
      </article>`,
    );
    statusEl.textContent = "blocked";
  } finally {
    statusEl.classList.remove("running");
    runButton.disabled = false;
    feed.scrollTop = feed.scrollHeight;
  }
}

async function collectDocuments() {
  const documents = loadedDatasetDocuments.map((document) => ({ ...document }));
  const packet = promptEl.value.trim();
  const files = Array.from(documentFileEl.files || []);
  if (!documents.length && packet && shouldTreatPromptAsDocument(packet, files.length)) {
    documents.push({ title: "Review Packet", body: packet });
  }
  for (const file of files) {
    documents.push({ title: file.name, body: await file.text() });
  }
  return documents;
}

function renderPending(message) {
  seedFeed();
  const content = message || "Run the customer review.";
  const documentCount = stagedDocumentCount();
  const datasetCard = loadedDataset
    ? `<div class="mini-card">
        <strong>Acceptance set</strong>
        <span>${escapeHtml(loadedDataset.id)} -> expected ${escapeHtml(expectedLabel(loadedDataset))}</span>
      </div>`
    : "";
  feed.insertAdjacentHTML(
    "beforeend",
    `<article class="message user-message">
      <div class="avatar">CO</div>
      <div class="bubble">
        <div class="bubble-head">
          <strong>Customer Owner</strong>
          <span>${documentCount ? "review packet" : "question"}</span>
        </div>
        <p>${escapeHtml(content)}</p>
        <div class="mini-card">
          <strong>Source package</strong>
          <span>${documentCount ? `${documentCount} source item${documentCount === 1 ? "" : "s"} attached` : "no source documents attached"}</span>
        </div>
        ${datasetCard}
      </div>
    </article>`,
  );
}

function renderWorkflow(payload) {
  const transcript = payload.transcript || [];
  const html = transcript.map(renderEvent).join("");
  feed.insertAdjacentHTML("beforeend", html);
  feed.insertAdjacentHTML("beforeend", renderPartnerReadouts(payload));
  feed.insertAdjacentHTML("beforeend", renderBandPublish(payload.band_publish));
  renderDecision(payload);
  setActiveAgent("QuadroDecision");
  feed.scrollTop = feed.scrollHeight;
}

function renderEvent(event) {
  const meta = AGENTS[event.sender] || {
    label: event.sender,
    initials: event.sender.slice(0, 2).toUpperCase(),
    side: "agent",
  };
  const mentions = (event.mentions || [])
    .map((mention) => `<span>@${escapeHtml(displayName(mention))}</span>`)
    .join("");
  const summary = eventSummary(event);
  const step = agentStep(event.sender);
  return `
    <article class="message ${meta.side === "user" ? "user-message" : ""}">
      <div class="avatar">${escapeHtml(meta.initials)}</div>
      <div class="bubble">
        <div class="bubble-head">
          <strong>${escapeHtml(meta.label)}</strong>
          <span>${escapeHtml(step || event.kind)}</span>
        </div>
        <p>${escapeHtml(event.content)}</p>
        ${mentions ? `<div class="mentions">${mentions}</div>` : ""}
        ${summary}
      </div>
    </article>
  `;
}

function eventSummary(event) {
  const payload = event.payload || {};
  if (payload.task_frame) {
    const frame = payload.task_frame;
    const cohesion = payload.input_cohesion;
    return `<div class="audit-card">
      <div class="audit-title">Step 1: Customer Intake</div>
      <div class="trace-grid">
        <div><strong>Requested action</strong><span>${escapeHtml(frame.requested_action)}</span></div>
        <div><strong>Consent</strong><span>${escapeHtml(humanize(frame.consent.status))} by ${escapeHtml(frame.consent.actor)}</span></div>
        <div><strong>Scope</strong><span>${chips(frame.consent.scope)}</span></div>
        <div><strong>Constraints</strong><span>${list(frame.consent.constraints)}</span></div>
      </div>
      ${cohesion ? renderCohesion(cohesion) : ""}
      ${frame.open_questions.length ? `<div class="audit-note"><strong>Open questions</strong>${list(frame.open_questions)}</div>` : ""}
    </div>`;
  }
  if (payload.chat_assist) {
    const assist = payload.chat_assist;
    return `<div class="audit-card">
      <div class="audit-title">Quadro answer</div>
      <p>${escapeHtml(assist.answer)}</p>
      <div class="audit-note"><strong>Review path</strong>${list(assist.review_path || [])}</div>
    </div>`;
  }
  if (payload.intake_checklist) {
    return `<div class="audit-card">
      <div class="audit-title">Step 1: Intake fields needed</div>
      ${list(payload.intake_checklist.required_fields)}
    </div>`;
  }
  if (payload.evidence_manifest) {
    const manifest = payload.evidence_manifest;
    const visible = visibleEvidence(manifest.items);
    const customerDocs = visible.filter((item) =>
      (item.scope_tags || []).includes("customer_document"),
    ).length;
    const items = uniqueEvidence(visible).slice(0, 8);
    const hiddenSystem = (manifest.items || []).length - visible.length;
    return `<div class="audit-card">
      <div class="audit-title">Step 2: Evidence Spine</div>
      <div class="audit-kpis">
        <span>${visible.length} review documents</span>
        <span>${customerDocs} customer/data hits</span>
        <span>${manifest.missing_items.length} missing</span>
      </div>
      <ol class="evidence-list">
        ${items
          .map(
            (item) => `<li>
              <strong>${escapeHtml(item.title)}</strong>
              <span>${escapeHtml(humanizePath(item.source))}</span>
              <small>${chips(item.scope_tags || [])}</small>
              <p>${escapeHtml(cleanSummary(item.summary))}</p>
            </li>`,
          )
          .join("")}
      </ol>
      ${hiddenSystem > 0 ? `<p class="audit-muted">${hiddenSystem} system background source packets were used for context and hidden from this review list.</p>` : ""}
      ${manifest.missing_items.length ? `<div class="audit-warning"><strong>Missing evidence</strong>${list(manifest.missing_items)}</div>` : ""}
      ${modelReadout(payload)}
    </div>`;
  }
  if (payload.policy_read) {
    const policy = payload.policy_read;
    return `<div class="audit-card">
      <div class="audit-title">Step 3: Policy / Risk</div>
      <div class="trace-grid">
        <div><strong>Risk</strong><span>${escapeHtml(humanize(policy.risk_level))}</span></div>
        <div><strong>Recommendation</strong><span>${escapeHtml(humanize(policy.recommendation))}</span></div>
        <div><strong>Escalation</strong><span>${policy.escalation_required ? "required" : "not required"}</span></div>
      </div>
      <div class="${policy.blockers.length ? "audit-warning" : "audit-pass"}">
        <strong>${policy.blockers.length ? "Blockers" : "No blockers"}</strong>
        ${policy.blockers.length ? list(policy.blockers) : "<span>Consent and required evidence passed policy review.</span>"}
      </div>
      ${modelReadout(payload)}
    </div>`;
  }
  if (payload.decision_packet) {
    const packet = payload.decision_packet;
    return `<div class="audit-card decision-audit">
      <div class="audit-title">Step 4: Decision Packet</div>
      <div class="outcome-row">
        <span class="outcome-pill ${outcomeClass(packet.outcome)}">${escapeHtml(humanizeOutcome(packet.outcome))}</span>
        <span>${escapeHtml(humanize(packet.current_gate))}</span>
      </div>
      <div class="trace-grid">
        <div><strong>Recommendation</strong><span>${escapeHtml(humanize(packet.recommendation))}</span></div>
        <div><strong>Approvals</strong><span>${chips(packet.required_approvals || [])}</span></div>
      </div>
      <div class="audit-note"><strong>Why</strong>${list(packet.rationale || [])}</div>
      ${packet.revision_history.length ? `<div class="audit-note"><strong>Revision history</strong>${list(packet.revision_history)}</div>` : ""}
      ${modelReadout(payload)}
    </div>`;
  }
  if (payload.consent) {
    return `<div class="mini-card">
      <strong>Consent revision</strong>
      <span>Revision ${payload.consent.revision}: ${escapeHtml(payload.consent.status)}</span>
    </div>`;
  }
  return "";
}

function modelReadout(payload) {
  const readout = payload.model_readout;
  if (!readout) {
    return "";
  }
  if (readout.status === "ACTIVE") {
    return `<div class="model-card">
      <div class="model-head">
        <strong>Local Hermes model readout</strong>
        <span>${escapeHtml(humanize(readout.role || "agent"))}</span>
      </div>
      <p>${escapeHtml(cleanSummary(readout.content || ""))}</p>
      <small>${escapeHtml(readout.backend || "local")} ${escapeHtml(readout.runtime || "")}</small>
    </div>`;
  }
  return `<div class="model-card blocked">
    <div class="model-head">
      <strong>Model lane blocked</strong>
      <span>${escapeHtml(humanize(readout.role || "agent"))}</span>
    </div>
    <p>${escapeHtml(cleanSummary(readout.reason || "Hermes did not return a live readout."))}</p>
  </div>`;
}

function renderCohesion(cohesion) {
  const activeSignals = Object.entries(cohesion.signals || {})
    .filter(([, active]) => active)
    .map(([name]) => name);
  const rows = [
    `source documents: ${cohesion.source_count || 0}`,
    `next gate: ${humanize(cohesion.next_gate || "waiting")}`,
    `confidence: ${humanize(cohesion.confidence || "unknown")}`,
  ];
  return `<div class="audit-note cohesion-note">
    <strong>Input stabilization</strong>
    ${list(rows)}
    ${activeSignals.length ? `<span>${chips(activeSignals)}</span>` : ""}
  </div>`;
}

function renderBandPublish(publish) {
  if (!publish) {
    return "";
  }
  const eventCount = (publish.events || []).length;
  const label = publish.ok
    ? "Band publish complete"
    : publish.mode === "local_assist"
      ? "Band review not run"
    : publish.enabled
      ? "Band publish blocked"
      : "Band publish off";
  const detail = publish.ok
    ? `${eventCount} agent handoff event${eventCount === 1 ? "" : "s"} posted to Band chat ${publish.chat_id || "unknown"}`
    : publish.blocked || "Set QUADRO_PUBLISH_TO_BAND=1 and QUADRO_BAND_CHAT_ID to publish this run.";
  const eventRows = (publish.events || [])
    .map(
      (event) => `<li>
        <strong>${escapeHtml(humanize(event.agent))}</strong>
        <span>${event.ok ? "posted" : "blocked"}${event.status_code ? ` · HTTP ${event.status_code}` : ""}</span>
      </li>`,
    )
    .join("");
  return `<article class="message system-message">
    <div class="avatar">B</div>
    <div class="bubble">
      <div class="bubble-head">
        <strong>${escapeHtml(label)}</strong>
        <span>${escapeHtml(publish.mode || "band")}</span>
      </div>
      <div class="audit-card band-audit ${publish.ok ? "band-ok" : "band-blocked"}">
        <div class="audit-title">Band coordination proof</div>
        <p>${escapeHtml(detail)}</p>
        ${eventRows ? `<ul class="audit-list">${eventRows}</ul>` : ""}
      </div>
    </div>
  </article>`;
}

function renderPartnerReadouts(payload) {
  const cards = [];
  const errors = payload.partner_errors || {};
  if (payload.partner_readout) {
    cards.push(
      partnerCard(
        "AI/ML API verifier",
        payload.partner_readout,
        payload.aimlapi_usage,
      ),
    );
  }
  if (payload.featherless_readout) {
    cards.push(
      partnerCard(
        "Featherless AI verifier",
        payload.featherless_readout,
        payload.featherless_usage,
      ),
    );
  }
  Object.entries(errors).forEach(([provider, message]) => {
    cards.push(
      partnerErrorCard(`${humanize(provider)} verifier`, message),
    );
  });
  if (!cards.length) {
    return "";
  }
  return `<article class="message system-message">
    <div class="avatar">M</div>
    <div class="bubble">
      <div class="bubble-head">
        <strong>Partner model verification</strong>
        <span>post-decision</span>
      </div>
      ${cards.join("")}
    </div>
  </article>`;
}

function partnerErrorCard(title, message) {
  return `<div class="model-card blocked partner-card">
    <div class="model-head">
      <strong>${escapeHtml(title)}</strong>
      <span>provider gated</span>
    </div>
    <p>${escapeHtml(cleanSummary(message || "Partner verifier did not return a live readout."))}</p>
    <small>Core Quadro decision remains complete; rerun after provider access is enabled.</small>
  </div>`;
}

function partnerCard(title, content, usage) {
  const model = usage && usage.model ? usage.model : "configured model";
  const tokenText =
    usage && usage.usage && usage.usage.total_tokens
      ? `${usage.usage.total_tokens} tokens`
      : "usage not returned";
  return `<div class="model-card partner-card">
    <div class="model-head">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(model)}</span>
    </div>
    <p>${escapeHtml(cleanSummary(content || ""))}</p>
    <small>${escapeHtml(tokenText)}</small>
  </div>`;
}

function chips(values) {
  if (!values || !values.length) {
    return "<em>none</em>";
  }
  return `<span class="chip-row">${values.map((value) => `<i>${escapeHtml(humanize(value))}</i>`).join("")}</span>`;
}

function list(values) {
  if (!values || !values.length) {
    return "<span>none</span>";
  }
  return `<ul class="audit-list">${values.map((value) => `<li>${escapeHtml(humanize(value))}</li>`).join("")}</ul>`;
}

function shortSource(source) {
  return String(source || "")
    .replace(/^.*data\/evaluation_sets\//, "data/")
    .replace(/^.*docs\/source_packets\//, "source_packets/");
}

function humanizePath(source) {
  const short = shortSource(source);
  return humanize(short)
    .replaceAll("data/evaluation sets/", "")
    .replaceAll("documents/", "")
    .replaceAll("source packets/", "system context / ");
}

function humanize(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replaceAll("/", " / ")
    .replace(/\\s+/g, " ")
    .trim()
    .replace(/^./, (char) => char.toUpperCase());
}

function humanizeOutcome(outcome) {
  if (outcome === "ANSWERED") {
    return "Answered";
  }
  if (outcome === "APPROVE") {
    return "Approve";
  }
  if (outcome === "SAY_NO") {
    return "Say no";
  }
  if (outcome === "NEED_MORE_INFO") {
    return "Need more info";
  }
  return humanize(outcome || "Need review");
}

function cleanSummary(summary) {
  return String(summary || "")
    .replaceAll("```text", "")
    .replaceAll("```", "")
    .replace(/\\s+/g, " ")
    .trim();
}

function visibleEvidence(items) {
  const reviewItems = (items || []).filter((item) => !String(item.source || "").includes("/docs/source_packets/"));
  return reviewItems.length ? reviewItems : items || [];
}

function uniqueEvidence(items) {
  const seen = new Set();
  const output = [];
  for (const item of items || []) {
    const key = `${item.title}|${item.source}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    output.push(item);
  }
  return output;
}

function outcomeClass(outcome) {
  if (outcome === "APPROVE") {
    return "approve";
  }
  if (outcome === "SAY_NO") {
    return "deny";
  }
  return "info";
}

function agentStep(sender) {
  return {
    HumanOwner: "documents + task",
    QuadroIntake: "step 1",
    QuadroEvidence: "step 2",
    QuadroPolicy: "step 3",
    QuadroDecision: "step 4",
  }[sender];
}

function shouldTreatPromptAsDocument(text, fileCount = 0) {
  const trimmed = String(text || "").trim();
  const lower = trimmed.toLowerCase();
  if (!trimmed) {
    return false;
  }
  const helpSignals = [
    "what can you do",
    "how does this work",
    "how do you work",
    "explain",
    "what should i upload",
    "what documents",
    "where do documents go",
    "how do i test",
  ];
  const sourceSignals = [
    "task:",
    "review request:",
    "customer:",
    "policy:",
    "approval:",
    "authorization",
    "consent",
    "invoice",
    "refund",
    "csv",
    "json",
    "log",
    "wire",
    "claim",
    "export",
    "payout",
    "disclosure",
    "vendor",
    "contract",
    "withdrew authorization",
    "approval not attached",
    "must not proceed",
  ];
  if (helpSignals.some((signal) => lower.includes(signal)) && trimmed.length < 280) {
    return false;
  }
  if (fileCount && trimmed.length < 260 && /^(can|should|please|run|review|approve|send|release|is|are|do|does|what)\b/i.test(trimmed)) {
    return false;
  }
  if (trimmed.length > 320) {
    return true;
  }
  return sourceSignals.some((signal) => lower.includes(signal)) && trimmed.includes("\n");
}

function renderDecision(payload) {
  const packet = payload.final_packet || {};
  const state = payload.state_path || {};
  const evidence = state.evidence_state || {};
  const policy = state.policy_state || {};

  decisionGate.textContent = humanize(packet.current_gate || "waiting");
  recommendationEl.textContent = packet.outcome
    ? `${humanizeOutcome(packet.outcome)}: ${humanize(packet.recommendation)}`
    : humanize(packet.recommendation || "No packet generated.");
  metricConsent.textContent = `rev ${packet.consent_revision ?? 0}`;
  metricEvidence.textContent = String((evidence.items || []).length);
  metricRisk.textContent = humanize(policy.risk_level || "waiting");
  if (payload.band_publish) {
    metricBand.textContent = payload.band_publish.ok
      ? "published"
      : payload.band_publish.mode === "local_assist"
        ? "not run"
      : payload.band_publish.enabled
        ? "blocked"
        : "off";
  }

  handoffList.querySelectorAll("li").forEach((item) => {
    item.classList.add("complete");
    item.classList.remove("current");
  });
  handoffList.lastElementChild.classList.add("current");
}

function displayName(name) {
  return (AGENTS[name] && AGENTS[name].label) || name.replace("Quadro", "");
}

function setActiveAgent(sender) {
  document.querySelectorAll(".agent-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.agent === sender);
  });
}

async function refreshStack() {
  const response = await fetch("/api/tool-stack");
  const payload = await response.json();
  stackList.innerHTML = payload.stack
    .map((item) => {
      return `
        <article class="stack-card">
          <div class="stack-card-head">
            <strong>${escapeHtml(item.name)}</strong>
            <span class="pill ${item.status.toLowerCase()}">${escapeHtml(item.status)}</span>
          </div>
          <p>${escapeHtml(item.description)}</p>
          <small>${escapeHtml(item.detail)}</small>
        </article>
      `;
    })
    .join("");
}

async function loadDatasetList() {
  if (!datasetSelectEl) {
    return;
  }
  try {
    const response = await fetch("/api/document-sets");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    const options = (payload.document_sets || [])
      .map((item) => {
        const label = `${item.id} - ${humanize(item.title)} -> ${expectedLabel(item)}`;
        return `<option value="${escapeHtml(item.id)}">${escapeHtml(label)}</option>`;
      })
      .join("");
    datasetSelectEl.insertAdjacentHTML("beforeend", options);
  } catch (error) {
    datasetSummaryEl.textContent = `Acceptance sets unavailable: ${error.message}`;
  }
}

async function loadSelectedDataset() {
  const id = datasetSelectEl.value;
  if (!id) {
    clearLoadedDataset();
    return;
  }
  loadDatasetButton.disabled = true;
  datasetSummaryEl.textContent = "Loading acceptance set...";
  try {
    const response = await fetch(`/api/document-sets/${encodeURIComponent(id)}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const pack = await response.json();
    loadedDataset = pack;
    loadedDatasetDocuments = Array.isArray(pack.documents) ? pack.documents : [];
    promptEl.value = pack.operator_message || pack.case_overrides?.requested_action || pack.title || "";
    datasetSummaryEl.innerHTML = `<strong>${escapeHtml(pack.title)}</strong> loaded: ${loadedDatasetDocuments.length} document${loadedDatasetDocuments.length === 1 ? "" : "s"}, expected ${escapeHtml(expectedLabel(pack))}.`;
    documentFileEl.value = "";
    updateDocumentSummary();
  } catch (error) {
    clearLoadedDataset();
    datasetSummaryEl.textContent = `Could not load set: ${error.message}`;
  } finally {
    loadDatasetButton.disabled = false;
  }
}

function clearLoadedDataset() {
  loadedDataset = null;
  loadedDatasetDocuments = [];
  datasetSummaryEl.textContent = "Optional: load one of Quadro's public-safe acceptance sets into this room.";
  updateDocumentSummary();
}

function expectedLabel(pack) {
  const expected = pack.expected || {};
  const outcome = humanizeOutcome(expected.outcome || "needs review");
  const gate = expected.gate ? ` / ${humanize(expected.gate)}` : "";
  return `${outcome}${gate}`;
}

function updateDocumentSummary() {
  const packetLength = promptEl.value.trim().length;
  const files = Array.from(documentFileEl.files || []);
  const datasetCount = loadedDatasetDocuments.length;
  if (!packetLength && !files.length && !datasetCount) {
    documentSummaryEl.textContent = "Ask a question, or paste source material and a decision request.";
    return;
  }
  const fileNames = files.map((file) => file.name).join(", ");
  const textAsSource = shouldTreatPromptAsDocument(promptEl.value, files.length);
  const textSummary = packetLength
    ? `${textAsSource ? "source text" : "question"} ${packetLength.toLocaleString()} chars`
    : "";
  const datasetSummary = datasetCount
    ? `${datasetCount} documents loaded from ${loadedDataset.id}`
    : "";
  documentSummaryEl.textContent = [datasetSummary, textSummary, fileNames].filter(Boolean).join("; ");
}

function stagedDocumentCount() {
  const files = Array.from(documentFileEl.files || []);
  const promptDocument = loadedDatasetDocuments.length
    ? 0
    : shouldTreatPromptAsDocument(promptEl.value, files.length)
      ? 1
      : 0;
  return loadedDatasetDocuments.length + promptDocument + files.length;
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  const path = loadedDataset && loadedDataset.revisit
    ? "/api/run-workflow"
    : "/api/run-workflow/no-revisit";
  runWorkflow(path);
});

promptEl.addEventListener("input", updateDocumentSummary);
documentFileEl.addEventListener("change", updateDocumentSummary);
datasetSelectEl.addEventListener("change", () => {
  if (!datasetSelectEl.value) {
    clearLoadedDataset();
  }
});
loadDatasetButton.addEventListener("click", loadSelectedDataset);

document.querySelector("#refresh-stack").addEventListener("click", refreshStack);

seedFeed();
updateDocumentSummary();
loadDatasetList();
refreshStack();
