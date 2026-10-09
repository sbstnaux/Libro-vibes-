// Capa de acceso a la API: todo fetch pasa por aquí.
const Api = (() => {
  const base = () => (window.APP_CONFIG?.API_BASE_URL || "").replace(/\/$/, "");

  async function request(path, options = {}) {
    let res;
    try {
      res = await fetch(`${base()}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
    } catch {
      throw { status: 0, error: "No hay conexión con el servidor. Revisa que el backend esté encendido." };
    }
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, ...body };
    return body;
  }

  return {
    recommend: (libro, n) => request("/api/recommend", { method: "POST", body: JSON.stringify({ libro, n }) }),
    search: (q, signal) => request(`/api/books/search?q=${encodeURIComponent(q)}`, { signal }),
  };
})();
