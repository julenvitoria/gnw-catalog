// The catalog page: catalog.json (the projects, edited by hand) + versions.json
// (their latest releases, written every 8 hours by .github/workflows/versions.yml).
import { LANGS, initialLang, saveLang, setLang, lang, t, applyTexts, fmtSize } from "./i18n.js";

const $ = (id) => document.getElementById(id);
const state = { items: [], firmware: null, versions: {}, kind: "all", q: "" };

// ------------------------------------------------------------ language
const langSel = $("lang");
for (const [code, label] of Object.entries(LANGS)) langSel.add(new Option(label, code));
function useLang(code) {
  setLang(code);
  langSel.value = code;
  applyTexts();
  render();
}
langSel.addEventListener("change", () => { saveLang(langSel.value); useLang(langSel.value); });

// ------------------------------------------------------------ filters
const KIND_KEY = "gnw-catalog.kind";
try { const k = localStorage.getItem(KIND_KEY); if (["all", "core", "homebrew", "tool"].includes(k)) state.kind = k; } catch { /* default */ }
for (const chip of document.querySelectorAll("[data-kind]")) {
  chip.addEventListener("click", () => {
    state.kind = chip.dataset.kind;
    try { localStorage.setItem(KIND_KEY, state.kind); } catch { /* not remembered */ }
    render();
  });
}
$("q").addEventListener("input", () => { state.q = $("q").value; render(); });

// ------------------------------------------------------------ data
Promise.all([
  fetch("catalog.json", { cache: "no-cache" }).then((r) => r.json()),
  fetch("versions.json", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
]).then(([cat, ver]) => {
  state.items = cat.items;
  state.firmware = cat.firmware || null;
  state.versions = ver || {};
  render();
});

// versions.json entry for a repo: { release, pre } (pre = a newer pre-release).
// The first versions of the file had the release fields flat; read both.
function vers(repo) {
  const v = state.versions[repo];
  if (v === undefined) return undefined;            // not checked yet
  if (v === null) return { release: null, pre: null };
  if ("release" in v || "pre" in v) return { release: v.release || null, pre: v.pre || null };
  return { release: v, pre: null };
}

// A description in the page's language, else English, else Spanish.
function desc(it) {
  const d = it.desc || {};
  return d[lang()] || d[lang().slice(0, 2)] || d.en || d.es || "";
}
const sysLabel = (s) => (["Port", "App", "Web", "Demo"].includes(s) ? t(`sys_${s}`) : s);
const owner = (it) => it.repo.split("/")[0];
const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(`${iso}T12:00:00`);
  return isNaN(d) ? iso : d.toLocaleDateString(lang(), { day: "numeric", month: "short", year: "numeric" });
}

// ------------------------------------------------------------ cards
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function relLine(r, cls) {
  const p = el("p", `item__rel ${cls || ""}`);
  const a = el("a", "", r.version);
  a.href = r.url; a.title = t("release_page"); a.target = "_blank"; a.rel = "noopener";
  p.append(a, document.createTextNode(` · ${fmtDate(r.date)}`));
  if (r.file) p.append(el("span", "item__file", ` · ${r.file}${r.size ? ` (${fmtSize(r.size)})` : ""}`));
  return p;
}

function card(it) {
  const v = vers(it.repo);
  const c = el("article", `item item--${it.kind}`);
  const head = el("div", "item__head");
  head.append(el("h2", "item__name", it.name), el("span", `badge badge--${it.kind}`, t(`kind_${it.kind}`)));
  const meta = el("p", "item__meta");
  meta.append(el("span", "item__sys", sysLabel(it.system)), document.createTextNode(" · "));
  const by = el("a", "", t("by", { a: owner(it) }));
  by.href = `https://github.com/${owner(it)}`;
  meta.append(by);
  c.append(head, meta, el("p", "item__desc", desc(it)));
  if (it.data) c.append(el("p", "item__data", t(it.data === "free" ? "data_free" : "data_own")));

  // releases: the full one, and a newer pre-release when there is one
  if (it.web) {
    c.append(el("p", "item__rel", t("web_hint")));
  } else if (v) {
    if (v.release) c.append(relLine(v.release));
    if (v.pre) {
      const p = relLine(v.pre, "item__rel--pre");
      p.prepend(el("span", "pre", t("prerelease")), " ");
      c.append(p);
      if (it.pre_for_rc) c.append(el("p", "item__prenote", t(v.release ? "pre_for_rc" : "pre_for_rc_only")));
    }
    if (!v.release && !v.pre) c.append(el("p", "item__rel", t("no_release")));
  }

  // a fork: how its original is doing
  if (it.upstream) {
    const u = vers(it.upstream);
    const up = el("p", "item__up");
    const a = el("a", "", t("fork_of", { r: it.upstream }));
    a.href = `https://github.com/${it.upstream}`; a.target = "_blank"; a.rel = "noopener";
    up.append(a);
    const ur = u && (u.pre || u.release);
    if (ur) {
      up.append(document.createTextNode(` · ${t("original")}: ${ur.version} · ${fmtDate(ur.date)}`));
      const mine = v && (v.pre || v.release);
      if (mine && mine.date > ur.date) up.append(" ", el("span", "ahead", t("ahead")));
    }
    c.append(up);
  }

  const actions = el("div", "item__actions");
  if (it.web) {
    const a = el("a", "btn btn--go", t("open"));
    a.href = it.web; a.target = "_blank"; a.rel = "noopener";
    actions.append(a);
  } else if (v) {
    if (v.release?.download) {
      const a = el("a", "btn btn--go", v.pre ? t("dl_stable", { v: v.release.version }) : t("download"));
      a.href = v.release.download;
      actions.append(a);
    }
    if (v.pre?.download) {
      const a = el("a", "btn btn--pre", t("dl_pre", { v: v.pre.version }));
      a.href = v.pre.download;
      actions.append(a);
    }
  }
  const code = el("a", "btn", t("repo"));
  code.href = `https://github.com/${it.repo}`; code.target = "_blank"; code.rel = "noopener";
  actions.append(code);
  if (it.extra) {
    const x = el("a", "btn", t(it.extra.label) || it.extra.label);
    x.href = it.extra.url; x.target = "_blank"; x.rel = "noopener";
    actions.append(x);
  }
  c.append(actions);

  const file = v && (v.release || v.pre)?.file;
  if (!it.web && file) {
    // a core's .bin goes in /cores/, a homebrew's in /homebrews/ (the Homebrew tab)
    const binHint = it.kind === "homebrew" ? t("bin_hint_hb") : t("bin_hint");
    c.append(el("p", "item__hint", /\.zip$/i.test(file) ? t("zip_hint") : /\.bin$/i.test(file) ? binHint : ""));
  }
  return c;
}

// ------------------------------------------------------------ firmware
function fwButton(id, r) {
  const a = $(id);
  a.hidden = !r;
  if (!r) return;
  a.href = r.download || r.url;
  a.querySelector("strong").textContent = r.version;
  a.querySelector("em").textContent = fmtDate(r.date);
}
function renderFirmware() {
  const fw = state.firmware;
  $("fw").hidden = !fw;
  if (!fw) return;
  const v = vers(fw.repo) || { release: null, pre: null };
  $("fw-name").textContent = fw.name;
  $("fw-desc").textContent = desc(fw);
  fwButton("fw-rel", v.release);
  fwButton("fw-pre", v.pre);
  $("fw-note").hidden = !v.pre;
}

const ORDER = { core: 0, homebrew: 1, tool: 2 };
function render() {
  if (!state.items.length) return;
  renderFirmware();
  const q = norm(state.q.trim());
  const match = (it) => !q || norm([it.name, it.system, owner(it), desc(it), it.repo].join(" ")).includes(q);
  const searched = state.items.filter(match);
  for (const chip of document.querySelectorAll("[data-kind]")) {
    const k = chip.dataset.kind;
    chip.setAttribute("aria-checked", String(k === state.kind));
    chip.querySelector("b").textContent = searched.filter((it) => k === "all" || it.kind === k).length;
  }
  const shown = searched.filter((it) => state.kind === "all" || it.kind === state.kind)
    .sort((a, b) => ORDER[a.kind] - ORDER[b.kind] || a.name.localeCompare(b.name));
  const grid = $("grid");
  grid.textContent = "";
  for (const it of shown) grid.append(card(it));
  $("empty").hidden = shown.length > 0;
  $("count").textContent = t("count", { n: shown.length });
}

useLang(initialLang());
