// The catalog page: catalog.json (the projects, edited by hand) + versions.json
// (their latest releases, written every 8 hours by .github/workflows/versions.yml).
import { LANGS, initialLang, saveLang, setLang, lang, t, applyTexts, fmtSize } from "./i18n.js";

const $ = (id) => document.getElementById(id);
const state = { items: [], versions: {}, kind: "all", q: "" };

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
  state.versions = ver || {};
  render();
});

// A description in the page's language, else English, else Spanish.
function desc(it) {
  const d = it.desc || {};
  return d[lang()] || d[lang().slice(0, 2)] || d.en || d.es || "";
}
const sysLabel = (s) => (["Port", "App", "Web"].includes(s) ? t(`sys_${s}`) : s);
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

function card(it) {
  const v = state.versions[it.repo];
  const c = el("article", `item item--${it.kind}`);
  const head = el("div", "item__head");
  head.append(el("h2", "item__name", it.name), el("span", `badge badge--${it.kind}`, t(`kind_${it.kind}`)));
  const meta = el("p", "item__meta");
  meta.append(el("span", "item__sys", sysLabel(it.system)), document.createTextNode(" · "));
  const by = el("a", "", t("by", { a: owner(it) }));
  by.href = `https://github.com/${owner(it)}`;
  meta.append(by);
  c.append(head, meta, el("p", "item__desc", desc(it)));

  const rel = el("p", "item__rel");
  if (it.web) {
    rel.textContent = t("web_hint");
  } else if (v) {
    const a = el("a", "", v.version);
    a.href = v.url;
    a.title = t("release_page");
    rel.append(a, document.createTextNode(` · ${fmtDate(v.date)}`));
    if (v.prerelease) rel.append(" ", el("span", "pre", t("prerelease")));
    if (v.file) rel.append(el("span", "item__file", ` · ${v.file}${v.size ? ` (${fmtSize(v.size)})` : ""}`));
  } else if (v === null) {
    rel.textContent = t("no_release");
  }
  c.append(rel);

  const actions = el("div", "item__actions");
  if (it.web) {
    const a = el("a", "btn btn--go", t("open"));
    a.href = it.web; a.target = "_blank"; a.rel = "noopener";
    actions.append(a);
  } else if (v?.download) {
    const a = el("a", "btn btn--go", t("download"));
    a.href = v.download;
    actions.append(a);
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

  if (!it.web && v?.file) {
    // a core's .bin goes in /cores/, a homebrew's in /homebrews/ (the Homebrew tab)
    const binHint = it.kind === "homebrew" ? t("bin_hint_hb") : t("bin_hint");
    c.append(el("p", "item__hint", /\.zip$/i.test(v.file) ? t("zip_hint") : /\.bin$/i.test(v.file) ? binHint : ""));
  }
  return c;
}

const ORDER = { core: 0, homebrew: 1, tool: 2 };
function render() {
  if (!state.items.length) return;
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
