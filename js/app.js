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
try { const k = localStorage.getItem(KIND_KEY); if (["all", "official", "core", "homebrew", "tool"].includes(k)) state.kind = k; } catch { /* default */ }
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
  const h = r.info?.header;
  if (h) p.append(" ", el("span", `fwtag ${h >= 3 ? "fwtag--rc" : "fwtag--old"}`, t(h >= 3 ? "fw_tag_rc" : "fw_tag_1x")));
  if (r.file) p.append(el("span", "item__file", ` · ${r.file}${r.size ? ` (${fmtSize(r.size)})` : ""}`));
  return p;
}

function card(it) {
  const v = vers(it.repo);
  const c = el("article", `item item--${it.kind}`);
  const head = el("div", "item__head");
  const badges = el("span", "badges");
  if (it.official) badges.append(el("span", "badge badge--official", t("official")));
  badges.append(el("span", `badge badge--${it.kind}`, t(`kind_${it.kind}`)));
  head.append(el("h2", "item__name", it.name), badges);
  const meta = el("p", "item__meta");
  meta.append(el("span", "item__sys", sysLabel(it.system)), document.createTextNode(" · "));
  const by = el("a", "", t("by", { a: owner(it) }));
  by.href = `https://github.com/${owner(it)}`;
  meta.append(by);
  c.append(head, meta, el("p", "item__desc", desc(it)));
  if ((state.versions._installer || []).includes(it.repo)) c.append(el("p", "item__inst", t("in_installer")));
  if (it.data) c.append(el("p", "item__data", t(it.data === "free" ? "data_free" : "data_own")));
  const systems = v && ((v.pre?.info?.systems) || (v.release?.info?.systems));
  if (systems || it.bios) {
    const box = el("div", "item__card");
    for (const sy of systems || []) {
      const p = el("p");
      p.append(el("b", "", sy.name), ` · /roms/${sy.dir}/`);
      if (sy.ext?.length) p.append(el("span", "ext", ` · ${sy.ext.map((e) => "." + e).join(" ")}`));
      if (sy.cheat) p.append(el("span", "ext", ` · ${t("cheats")}: /cheats/${sy.dir}/*.${sy.cheat}`));
      box.append(p);
    }
    if (it.bios) {
      const p = el("p");
      const dir = `/bios/${it.bios.dir}/`;
      const b = it.bios;
      let label = t(b.included ? "bios_inc" : b.optional ? "bios_opt" : "bios");
      if (b.when) label += ` (${desc({ desc: b.when })})`;
      p.append(el("b", "", label), " · ", b.files.length === 1 ? dir + b.files[0] : `${dir} → ${b.files.join(", ")}`);
      box.append(p);
    }
    c.append(box);
  }

  // releases: the full one, and a newer pre-release when there is one
  if (it.web) {
    c.append(el("p", "item__rel", t("web_hint")));
  } else if (v) {
    if (v.release) c.append(relLine(v.release));
    // its pre-release is the one for the firmware's RC: say so on the release
    const hr = v.release?.info?.header, hp = v.pre?.info?.header;
    if (hr && hr < 3) c.append(el("p", "item__prenote", t(hp >= 3 ? "pre_for_rc" : "only_1x")));
    if (v.pre) {
      const p = relLine(v.pre, "item__rel--pre");
      p.prepend(el("span", "pre", t("prerelease")), " ");
      c.append(p);
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
  const inKind = (it, k) => k === "all" || (k === "official" ? !!it.official : it.kind === k);
  for (const chip of document.querySelectorAll("[data-kind]")) {
    const k = chip.dataset.kind;
    chip.setAttribute("aria-checked", String(k === state.kind));
    chip.querySelector("b").textContent = searched.filter((it) => inKind(it, k)).length;
  }
  const shown = searched.filter((it) => inKind(it, state.kind))
    .sort((a, b) => ORDER[a.kind] - ORDER[b.kind] || a.name.localeCompare(b.name) || !!b.official - !!a.official);
  const grid = $("grid");
  grid.textContent = "";
  for (const it of shown) grid.append(card(it));
  $("empty").hidden = shown.length > 0;
  $("count").textContent = t("count", { n: shown.length });
}

useLang(initialLang());
