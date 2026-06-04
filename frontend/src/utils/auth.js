// src/utils/auth.js
export async function checkTokenValidity() {

  const token = sessionStorage.getItem("token");
  const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

  if (!token) return false;

  try {
    const response = await fetch(`${API}/api/check-token`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 200) {
      const json = await response.json();
      if (json.valid) {
        console.info("Token valide");
        return true;

      } else {
        console.error("Token invalide");
        sessionStorage.removeItem("token");
        return false;}
    } else {
        console.error("Erreur de verification du token");
        sessionStorage.removeItem("token");
        return false;
    }
  } catch (error) {
    console.error("Erreur de vérification du token:", error);
    sessionStorage.removeItem("token");

    return false;
  }
}
