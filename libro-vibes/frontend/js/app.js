(() => {
  const SPINE_COLORS = ["#2f5d50", "#8c3b3b", "#3d4e7a", "#a9802f", "#5e4b6e", "#4f6b3a", "#7a5136"];
  const EXAMPLES = ["The Hobbit", "Pride and Prejudice", "Dune"];

  const form = document.getElementById("search-form");
  const input = document.getElementById("book-input");
  const button = document.getElementById("submit-btn");
  const list = document.getElementById("suggestions");
  const shelf = document.getElementById("shelf");
  const status = document.getElementById("status");
  const detail = document.getElementById("detail");

  // ---------- Utilidades ----------
  const el = (tag, props = {}, children = []) => {
    const node = Object.assign(document.createElement(tag), props);
    children.forEach((c) => node.append(c));
    return node;
  };

  const debounce = (fn, ms) => {
    let t;
    const run = (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
    run.cancel = () => clearTimeout(t);
    return run;
  };

  function setStatus(parts, isError = false) {
    status.replaceChildren(...[].concat(parts));
    status.classList.toggle("error", isError);
  }

  function exampleButtons(titles) {
    const nodes = [];
    titles.forEach((t, i) => {
      if (i > 0) nodes.push(i === titles.length - 1 ? " o " : ", ");
      nodes.push(el("button", { type: "button", textContent: `«${t}»`, onclick: () => search(t) }));
    });
    return nodes;
  }

  // ---------- Repisa ----------
  function placeholderShelf(className) {
    shelf.className = `shelf ${className}`;
    shelf.replaceChildren(
      ...SPINE_COLORS.map((c, i) => {
        const s = el("div", { className: "spine" }, [el("span", { className: "spine-band" })]);
        s.style.setProperty("--c", c);
        s.style.setProperty("--h", `${11 + ((i * 7) % 5)}rem`);
        return s;
      })
    );
  }

  function spineFor(book, index, isSource) {
    const color = isSource ? null : SPINE_COLORS[index % SPINE_COLORS.length];
    // Altura según la nota del libro, grosor según la similitud.
    const height = 11 + ((book.rating ?? 3.5) - 3) * 3;
    const width = isSource ? 3.6 : 2.6 + (book.similarity ?? 0.3) * 4;

    const spine = el("button", {
      type: "button",
      className: `spine${isSource ? " source" : ""}`,
      title: `${book.book} — ${book.author}`,
    }, [
      el("span", { className: "spine-title", textContent: book.book }),
      el("span", { className: "spine-band" }),
    ]);
    spine.setAttribute("role", "listitem");
    spine.setAttribute("aria-pressed", "false");
    if (color) spine.style.setProperty("--c", color);
    spine.style.setProperty("--h", `${Math.min(Math.max(height, 10), 16)}rem`);
    spine.style.setProperty("--w", `${Math.min(width, 4.4)}rem`);
    spine.addEventListener("click", () => showDetail(book, spine, color, isSource));
    return spine;
  }

  function renderShelf(source, results) {
    shelf.className = "shelf";
    const spines = [spineFor(source, 0, true), ...results.map((b, i) => spineFor(b, i, false))];
    shelf.replaceChildren(...spines);
    if (spines[1]) spines[1].click();
  }

  function showDetail(book, spine, color, isSource) {
    shelf.querySelectorAll(".spine").forEach((s) => s.setAttribute("aria-pressed", "false"));
    spine.setAttribute("aria-pressed", "true");
    detail.style.setProperty("--c", color || "var(--ink)");

    const rows = [];
    if (book.rating != null) rows.push(["Nota media", `${book.rating.toFixed(2)} / 5`]);
    if (book.num_ratings) rows.push(["Valoraciones", book.num_ratings.toLocaleString("es")]);
    if (book.genres?.length) rows.push(["Géneros", book.genres.join(", ")]);

    detail.replaceChildren(
      el("h2", { textContent: book.book }),
      el("p", { className: "author", textContent: isSource ? `${book.author} · el libro que buscaste` : book.author }),
      el("dl", {}, rows.flatMap(([k, v]) => [el("dt", { textContent: k }), el("dd", { textContent: v })])),
      ...(book.url ? [el("a", { href: book.url, target: "_blank", rel: "noopener", textContent: "Ver en Goodreads" })] : [])
    );
    detail.hidden = false;
  }

  // ---------- Búsqueda ----------
  async function search(title) {
    title = title.trim();
    closeSuggestions();
    if (!title) {
      setStatus("Escribe el título de un libro para empezar.", true);
      input.focus();
      return;
    }
    input.value = title;
    button.disabled = true;
    detail.hidden = true;
    placeholderShelf("loading");
    setStatus(`Buscando libros parecidos a «${title}»…`);

    try {
      const { source, results } = await Api.recommend(title, window.APP_CONFIG?.RESULTS ?? 6);
      if (!results.length) {
        placeholderShelf("empty");
        setStatus(`Encontramos «${source.book}», pero no hay libros lo bastante parecidos.`);
        return;
      }
      renderShelf(source, results);
      setStatus(`${results.length} libros parecidos a «${source.book}». Toca un lomo para ver los detalles.`);
    } catch (err) {
      placeholderShelf("empty");
      if (err.status === 404) {
        const parts = [`No encontramos «${title}» en el catálogo.`];
        if (err.suggestions?.length) parts.push(" ¿Quisiste decir ", ...exampleButtons(err.suggestions.slice(0, 3)), "?");
        setStatus(parts, true);
      } else {
        setStatus(err.error || "Algo falló al pedir las recomendaciones. Inténtalo de nuevo.", true);
      }
    } finally {
      button.disabled = false;
    }
  }

  // ---------- Autocompletado ----------
  let activeIndex = -1;
  let controller;
  let fetchSuggestions;

  function closeSuggestions() {
    fetchSuggestions?.cancel();
    controller?.abort();
    list.hidden = true;
    list.replaceChildren();
    input.setAttribute("aria-expanded", "false");
    activeIndex = -1;
  }

  function highlight(index) {
    const items = [...list.children];
    items.forEach((li, i) => li.setAttribute("aria-selected", String(i === index)));
    activeIndex = index;
    if (items[index]) items[index].scrollIntoView({ block: "nearest" });
  }

  fetchSuggestions = debounce(async (q) => {
    if (q.length < 2) return closeSuggestions();
    controller?.abort();
    controller = new AbortController();
    try {
      const { results } = await Api.search(q, controller.signal);
      if (!results.length || input.value.trim() !== q || document.activeElement !== input) return closeSuggestions();
      list.replaceChildren(
        ...results.map((r, i) => {
          const li = el("li", { id: `sug-${i}` }, [r.book, el("small", { textContent: r.author })]);
          li.setAttribute("role", "option");
          li.addEventListener("mousedown", (e) => { e.preventDefault(); search(r.book); });
          return li;
        })
      );
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
      activeIndex = -1;
    } catch {
      closeSuggestions(); // el autocompletado es opcional: si falla, no molesta
    }
  }, 250);

  input.addEventListener("input", () => fetchSuggestions(input.value.trim()));
  input.addEventListener("blur", closeSuggestions);
  input.addEventListener("keydown", (e) => {
    const count = list.children.length;
    if (list.hidden || !count) return;
    if (e.key === "ArrowDown") { e.preventDefault(); highlight((activeIndex + 1) % count); }
    else if (e.key === "ArrowUp") { e.preventDefault(); highlight((activeIndex - 1 + count) % count); }
    else if (e.key === "Escape") closeSuggestions();
    else if (e.key === "Enter" && activeIndex >= 0) {
      e.preventDefault();
      search(list.children[activeIndex].firstChild.textContent);
    }
  });

  form.addEventListener("submit", (e) => { e.preventDefault(); search(input.value); });

  // ---------- Estado inicial ----------
  placeholderShelf("empty");
  setStatus(["Tu repisa está vacía. Prueba con ", ...exampleButtons(EXAMPLES), "."]);
})();
