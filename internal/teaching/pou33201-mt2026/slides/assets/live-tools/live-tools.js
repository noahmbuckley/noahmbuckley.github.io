/*****************************************************************
 * live-tools.js — In-presentation annotation tools for reveal.js
 *
 * Features:
 *   - Drop text boxes on slides (key: t)
 *   - Drop emojis on slides (keys: 1–9, configurable)
 *   - Drop custom reaction images (key: 0, configurable)
 *   - Drag any annotation to reposition
 *   - Click an annotation + Backspace to delete
 *   - Auto-save to localStorage (per-deck-path)
 *   - Manual export/import via JSON file
 *   - Back-stack navigation: clicking in-slide links pushes onto a
 *     stack; Cmd/Ctrl+B pops back to the prior slide
 *
 * Default keybindings (can be remapped in window.LIVE_TOOLS_CONFIG):
 *   t                    — text box at click point
 *   Shift + letter       — emoji at click point (S=star, F=fire, G=goal,
 *                          I=idea, Q=question, E=exclaim, L=lol, P=party,
 *                          Y=eYes — see CONFIG.emojis)
 *   Shift + R            — first item of imageReactions at click point
 *   Esc                  — cancel pending placement / commit text edit
 *   Backspace / Delete   — delete focused annotation
 *   Cmd/Ctrl + B         — pop navigation back-stack (previous slide)
 *   Cmd/Ctrl + Shift + E — export annotations to JSON file
 *   Cmd/Ctrl + Shift + I — import annotations from JSON file
 *   Cmd/Ctrl + Shift + X — clear annotations on current slide
 *   Cmd/Ctrl + Shift + A — toggle live-tools on/off (panic button)
 *
 * Note: number keys (0-9) are intentionally NOT bound — they belong to
 * reveal.js for "type N + Enter to jump to slide N".
 *
 * Storage key:   "live-tools::" + location.pathname
 ******************************************************************/

(function () {
  "use strict";

  // -------------------------------------------------------------
  // Configuration (override by setting window.LIVE_TOOLS_CONFIG before this script loads)
  // Emoji keys are uppercase letters (matching e.key when Shift is held).
  // -------------------------------------------------------------
  const DEFAULT_CONFIG = {
    emojis: {
      "S": "⭐",  // Star
      "F": "🔥",  // Fire
      "G": "🎯",  // Goal
      "I": "💡",  // Idea
      "Q": "❓",  // Question
      "E": "❗",  // Exclaim
      "L": "😂",  // Lol
      "P": "🎉",  // Party
      "Y": "👀",  // eYes
    },
    imageReactionKey: "R",  // Shift + this key drops imageReactions[0]
    imageReactions: [
      // Absolute or relative URLs; Shift+R drops the first one.
      // Example: "assets/reactions/mind-blown.png"
    ],
    emojiSize: 56,         // px
    textBoxFontSize: 28,    // px
    textBoxColor: "#1A5276",
    textBoxBg: "rgba(244, 208, 63, 0.85)", // gold-ish sticky-note color
    textBoxPadding: "6px 10px",
  };

  const CONFIG = Object.assign({}, DEFAULT_CONFIG, window.LIVE_TOOLS_CONFIG || {});

  // -------------------------------------------------------------
  // State
  // -------------------------------------------------------------
  const STORAGE_KEY = "live-tools::" + location.pathname;
  const NAV_STACK = []; // for Cmd+B back-navigation
  let pendingPlacement = null; // {kind, payload} — armed by key, dropped on next click
  let focusedNode = null;
  let enabled = true;
  let annotations = loadAnnotations();

  // -------------------------------------------------------------
  // Storage
  // -------------------------------------------------------------
  function loadAnnotations() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return parsed.annotations || {};
    } catch (e) {
      console.warn("[live-tools] could not load annotations:", e);
      return {};
    }
  }

  function saveAnnotations() {
    try {
      const payload = {
        version: 1,
        deck: location.pathname,
        savedAt: new Date().toISOString(),
        annotations: annotations,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
      console.warn("[live-tools] could not save annotations:", e);
    }
  }

  function exportAnnotations() {
    const payload = {
      version: 1,
      deck: location.pathname,
      savedAt: new Date().toISOString(),
      annotations: annotations,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const stamp = new Date().toISOString().replace(/[:T]/g, "-").slice(0, 19);
    const name = (location.pathname.split("/").pop() || "slides").replace(/\.html?$/, "");
    a.href = url;
    a.download = `${name}-annotations-${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    flash(`Exported ${Object.keys(annotations).length} slide(s)`);
  }

  function importAnnotations() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "application/json,.json";
    input.onchange = () => {
      const file = input.files && input.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = JSON.parse(reader.result);
          if (!parsed.annotations || typeof parsed.annotations !== "object") {
            throw new Error("missing 'annotations' object");
          }
          annotations = parsed.annotations;
          saveAnnotations();
          renderAllSlides();
          flash(`Imported ${Object.keys(annotations).length} slide(s)`);
        } catch (e) {
          alert("Could not import: " + e.message);
        }
      };
      reader.readAsText(file);
    };
    input.click();
  }

  // -------------------------------------------------------------
  // Slide identity
  // -------------------------------------------------------------
  function slideId(section) {
    if (!section) return null;
    if (section.id) return section.id;
    const idx = window.Reveal && Reveal.getIndices(section);
    if (idx) return `h${idx.h}-v${idx.v || 0}`;
    return null;
  }

  function currentSection() {
    return window.Reveal && Reveal.getCurrentSlide();
  }

  // -------------------------------------------------------------
  // Coordinate mapping (page px → slide px)
  // -------------------------------------------------------------
  function pageToSlide(section, clientX, clientY) {
    const rect = section.getBoundingClientRect();
    const w = section.offsetWidth || 1050;
    const h = section.offsetHeight || 700;
    const sx = (clientX - rect.left) * (w / rect.width);
    const sy = (clientY - rect.top) * (h / rect.height);
    return { x: Math.round(sx), y: Math.round(sy) };
  }

  // -------------------------------------------------------------
  // Render
  // -------------------------------------------------------------
  function renderSlide(section) {
    if (!section) return;
    section.querySelectorAll(":scope > .live-annotation").forEach(n => n.remove());
    const id = slideId(section);
    const list = annotations[id] || [];
    list.forEach((ann, i) => {
      const node = buildNode(ann, id, i);
      section.appendChild(node);
    });
  }

  function renderAllSlides() {
    document.querySelectorAll(".reveal .slides section").forEach(renderSlide);
  }

  function buildNode(ann, slideKey, index) {
    const node = document.createElement("div");
    node.className = "live-annotation live-annotation--" + ann.type;
    node.dataset.slideKey = slideKey;
    node.dataset.index = String(index);
    node.style.position = "absolute";
    node.style.left = ann.x + "px";
    node.style.top = ann.y + "px";
    node.style.cursor = "move";
    node.style.userSelect = "none";
    node.style.zIndex = "100";

    if (ann.type === "text") {
      node.contentEditable = "true";
      node.style.fontSize = (ann.fontSize || CONFIG.textBoxFontSize) + "px";
      node.style.color = ann.color || CONFIG.textBoxColor;
      node.style.background = ann.bg || CONFIG.textBoxBg;
      node.style.padding = CONFIG.textBoxPadding;
      node.style.borderRadius = "4px";
      node.style.fontWeight = "600";
      node.style.minWidth = "20px";
      node.style.lineHeight = "1.2";
      node.style.boxShadow = "1px 2px 4px rgba(0,0,0,0.15)";
      node.textContent = ann.content || "";
      node.addEventListener("input", () => {
        ann.content = node.textContent;
        saveAnnotations();
      });
    } else if (ann.type === "emoji") {
      node.style.fontSize = (ann.size || CONFIG.emojiSize) + "px";
      node.style.lineHeight = "1";
      node.textContent = ann.content;
    } else if (ann.type === "image") {
      const img = document.createElement("img");
      img.src = ann.src;
      img.style.width = (ann.width || 200) + "px";
      img.style.pointerEvents = "none";
      node.appendChild(img);
    }

    attachDrag(node, ann);
    attachFocus(node);
    return node;
  }

  // -------------------------------------------------------------
  // Drag
  // -------------------------------------------------------------
  function attachDrag(node, ann) {
    let dragging = false;
    let startSlide = null;
    let startSlideX = 0, startSlideY = 0;
    let startAnnX = 0, startAnnY = 0;

    node.addEventListener("mousedown", (e) => {
      // Don't start drag if user is editing a text box (already focused)
      if (ann.type === "text" && document.activeElement === node) return;
      e.stopPropagation();
      dragging = true;
      startSlide = node.parentElement;
      const p = pageToSlide(startSlide, e.clientX, e.clientY);
      startSlideX = p.x; startSlideY = p.y;
      startAnnX = ann.x; startAnnY = ann.y;
      e.preventDefault();
    });

    document.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      const p = pageToSlide(startSlide, e.clientX, e.clientY);
      ann.x = startAnnX + (p.x - startSlideX);
      ann.y = startAnnY + (p.y - startSlideY);
      node.style.left = ann.x + "px";
      node.style.top = ann.y + "px";
    });

    document.addEventListener("mouseup", () => {
      if (!dragging) return;
      dragging = false;
      saveAnnotations();
    });
  }

  function attachFocus(node) {
    node.addEventListener("mousedown", () => {
      if (focusedNode && focusedNode !== node) {
        focusedNode.style.outline = "";
      }
      focusedNode = node;
      node.style.outline = "2px dashed rgba(231, 76, 60, 0.7)";
    });
  }

  function deleteAnnotation(node) {
    const slideKey = node.dataset.slideKey;
    const index = parseInt(node.dataset.index, 10);
    if (!annotations[slideKey]) return;
    annotations[slideKey].splice(index, 1);
    if (annotations[slideKey].length === 0) delete annotations[slideKey];
    saveAnnotations();
    const section = node.parentElement;
    renderSlide(section);
    focusedNode = null;
  }

  // -------------------------------------------------------------
  // Adding annotations
  // -------------------------------------------------------------
  function addAnnotation(section, ann) {
    const id = slideId(section);
    if (!id) return;
    if (!annotations[id]) annotations[id] = [];
    annotations[id].push(ann);
    saveAnnotations();
    renderSlide(section);
    if (ann.type === "text") {
      // Focus the new text box for immediate typing
      const nodes = section.querySelectorAll(".live-annotation--text");
      const last = nodes[nodes.length - 1];
      if (last) {
        setTimeout(() => {
          last.focus();
          // Move caret to end
          const range = document.createRange();
          range.selectNodeContents(last);
          range.collapse(false);
          const sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
        }, 50);
      }
    }
  }

  function clearCurrentSlide() {
    const section = currentSection();
    if (!section) return;
    const id = slideId(section);
    if (!id) return;
    if (!annotations[id]) return flash("Nothing to clear");
    delete annotations[id];
    saveAnnotations();
    renderSlide(section);
    flash("Slide cleared");
  }

  // -------------------------------------------------------------
  // Pending placement (key armed → next click drops)
  // -------------------------------------------------------------
  function armPlacement(kind, payload) {
    pendingPlacement = { kind, payload };
    document.body.style.cursor = "crosshair";
    flash(`Click slide to place ${payload.preview || kind}`);
  }

  function disarmPlacement() {
    pendingPlacement = null;
    document.body.style.cursor = "";
  }

  function handleSlideClick(e) {
    if (!pendingPlacement) return;
    const section = e.target.closest(".reveal .slides section");
    if (!section) return;
    // Don't trigger when clicking an existing annotation
    if (e.target.closest(".live-annotation")) return;
    const p = pageToSlide(section, e.clientX, e.clientY);
    const { kind, payload } = pendingPlacement;
    let ann;
    if (kind === "text") {
      ann = { type: "text", x: p.x, y: p.y, content: "" };
    } else if (kind === "emoji") {
      ann = { type: "emoji", x: p.x, y: p.y, content: payload.char };
    } else if (kind === "image") {
      ann = { type: "image", x: p.x, y: p.y, src: payload.src };
    }
    if (ann) addAnnotation(section, ann);
    disarmPlacement();
    e.preventDefault();
    e.stopPropagation();
  }

  // -------------------------------------------------------------
  // Back-stack navigation: track every slide change. Cmd+B = previous slide.
  // The `popping` flag prevents the back-nav itself from polluting the stack.
  // -------------------------------------------------------------
  let lastSlideKey = null;
  let popping = false;

  function trackSlideChange(currentSlide) {
    const key = slideId(currentSlide);
    if (lastSlideKey && lastSlideKey !== key && !popping) {
      NAV_STACK.push(lastSlideKey);
      if (NAV_STACK.length > 50) NAV_STACK.shift();
    }
    popping = false;
    lastSlideKey = key;
  }

  function popBackNav() {
    const target = NAV_STACK.pop();
    if (!target) return flash("Nothing to go back to");
    popping = true;
    const el = document.getElementById(target);
    if (el) {
      const idx = Reveal.getIndices(el);
      Reveal.slide(idx.h, idx.v || 0);
      return;
    }
    // Fallback: parse h-v
    const m = target.match(/^h(\d+)-v(\d+)$/);
    if (m) {
      Reveal.slide(parseInt(m[1], 10), parseInt(m[2], 10));
      return;
    }
    popping = false; // didn't navigate
  }

  // -------------------------------------------------------------
  // Flash message
  // -------------------------------------------------------------
  let flashTimer = null;
  function flash(msg) {
    let el = document.getElementById("live-tools-flash");
    if (!el) {
      el = document.createElement("div");
      el.id = "live-tools-flash";
      el.style.cssText = "position:fixed;bottom:20px;left:50%;transform:translateX(-50%);" +
        "background:rgba(0,0,0,0.8);color:white;padding:8px 16px;border-radius:4px;" +
        "font-family:sans-serif;font-size:14px;z-index:10000;pointer-events:none;" +
        "transition:opacity 0.3s;opacity:0;";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.opacity = "1";
    clearTimeout(flashTimer);
    flashTimer = setTimeout(() => { el.style.opacity = "0"; }, 1500);
  }

  // -------------------------------------------------------------
  // Keyboard
  // -------------------------------------------------------------
  function setupKeyboard() {
    document.addEventListener("keydown", (e) => {
      // Always-on: panic toggle
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === "a") {
        enabled = !enabled;
        document.body.classList.toggle("live-tools-disabled", !enabled);
        flash("Live tools " + (enabled ? "ON" : "OFF"));
        e.preventDefault();
        return;
      }
      if (!enabled) return;

      // If currently editing a text-box annotation, don't intercept regular keys.
      // Detect via activeElement (focusedNode may not be set after programmatic focus).
      const ae = document.activeElement;
      const editingText = ae && ae.classList &&
                          ae.classList.contains("live-annotation--text");
      if (editingText) {
        if (e.key === "Escape") {
          ae.blur();
          if (focusedNode) focusedNode.style.outline = "";
          focusedNode = null;
          e.preventDefault();
        }
        return;
      }

      // Cmd/Ctrl + Shift combos
      if ((e.metaKey || e.ctrlKey) && e.shiftKey) {
        const k = e.key.toLowerCase();
        if (k === "e") { exportAnnotations(); e.preventDefault(); return; }
        if (k === "i") { importAnnotations(); e.preventDefault(); return; }
        if (k === "x") { clearCurrentSlide(); e.preventDefault(); return; }
      }

      // Cmd/Ctrl + B = back nav
      if ((e.metaKey || e.ctrlKey) && !e.shiftKey && e.key.toLowerCase() === "b") {
        popBackNav();
        e.preventDefault();
        return;
      }

      // Esc cancels pending placement, otherwise lets reveal handle
      if (e.key === "Escape") {
        if (pendingPlacement) {
          disarmPlacement();
          e.preventDefault();
          return;
        }
        if (focusedNode) {
          focusedNode.style.outline = "";
          focusedNode = null;
          return;
        }
      }

      // Backspace/Delete on focused annotation
      if ((e.key === "Backspace" || e.key === "Delete") && focusedNode) {
        deleteAnnotation(focusedNode);
        e.preventDefault();
        return;
      }

      // Plain `t` (no modifiers, no shift) → arm text box
      if (e.key === "t" && !e.shiftKey && !e.metaKey && !e.ctrlKey && !e.altKey) {
        armPlacement("text", { preview: "text box" });
        e.preventDefault();
        return;
      }

      // Shift + letter → arm emoji or image reaction.
      // Shift-only (no Cmd/Ctrl/Alt) so we don't swallow Cmd+Shift combos.
      if (e.shiftKey && !e.metaKey && !e.ctrlKey && !e.altKey && e.key.length === 1) {
        const k = e.key.toUpperCase();
        // Image reaction first (so it can override an emoji entry if both share a key)
        if (k === CONFIG.imageReactionKey) {
          const src = CONFIG.imageReactions[0];
          if (src) {
            armPlacement("image", { src, preview: "image" });
            e.preventDefault();
            return;
          }
        }
        const ch = CONFIG.emojis[k];
        if (ch) {
          armPlacement("emoji", { char: ch, preview: ch });
          e.preventDefault();
          return;
        }
      }
    }, true);
  }

  // -------------------------------------------------------------
  // Init
  // -------------------------------------------------------------
  function init(deck) {
    // Enable reveal.js's built-in "type N then Enter to jump to slide N".
    // Requires reveal.js v4.6+ (Quarto bundles a recent version).
    try { deck.configure({ jumpToSlide: true }); } catch (e) { /* older reveal */ }

    setupKeyboard();
    document.addEventListener("click", handleSlideClick, true);
    deck.on("slidechanged", (e) => {
      trackSlideChange(e.currentSlide);
      renderSlide(e.currentSlide);
    });
    deck.on("ready", () => {
      lastSlideKey = slideId(currentSection());
      renderAllSlides();
    });
    // In case ready already fired
    if (deck.isReady && deck.isReady()) {
      lastSlideKey = slideId(currentSection());
      renderAllSlides();
    }
    console.log("[live-tools] ready. Try: t, Shift+S/F/G/I/Q/E/L/P/Y, Cmd+Shift+E, Cmd+B");
  }

  // Expose as a reveal.js plugin so it can be registered
  window.RevealLiveTools = {
    id: "RevealLiveTools",
    init: init,
    // Public API for buttons or external triggers
    export: exportAnnotations,
    import: importAnnotations,
    clearSlide: clearCurrentSlide,
    arm: armPlacement,
  };
})();
