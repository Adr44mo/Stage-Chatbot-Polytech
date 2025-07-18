// ==================================================================
// Gestionnaire des appels API pour l'authentification administrateur
// ==================================================================

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
export async function loginAdmin(
  username: string,
  password: string,
  recaptchaToken?: string,
  isCaptchaValidated?: boolean
): Promise<{ ok: boolean; error?: string }> {
  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/x-www-form-urlencoded",
    };
    headers["X-Recaptcha-Token"] = recaptchaToken || "";
    if (isCaptchaValidated && !recaptchaToken) {
      headers["X-Recaptcha-Validated"] = "true";
    }

    const res = await fetch("/auth/login", {
      method: "POST",
      headers,
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
