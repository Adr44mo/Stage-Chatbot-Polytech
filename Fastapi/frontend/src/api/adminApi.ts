// ===========================================================
// Gestionnaire des appels API pour l'interface administrateur
// ===========================================================

// Vérifie si l'utilisateur admin est authentifié (cookie JWT)
export async function checkAdminAuth(): Promise<boolean> {
  try {
    const res = await fetch("/auth/me", { credentials: "include" });
    return res.ok;
  } catch {
    return false;
  }
}

// Déconnecte l'utilisateur admin (supprime le cookie JWT)
export async function logoutAdmin() {
  await fetch("/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}

// Effectue le login admin (pose le cookie JWT)
export async function loginAdmin(username: string, password: string): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      credentials: "include",
      body: new URLSearchParams({ username, password }),
    });
    if (res.ok) return { ok: true };
    const data = await res.json();
    return { ok: false, error: data.detail || "Erreur d'authentification" };
  } catch {
    return { ok: false, error: "Erreur réseau" };
  }
}