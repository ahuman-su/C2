// src/utils/auth.js
export async function checkTokenValidity() {

  const token = sessionStorage.getItem("token");

  if (!token) return false;

  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/check-token`, {
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
        return false;}
    } else {
        console.error("Erreur de verification du token");
        return false;
    }
  } catch (error) {
    console.error("Erreur de vérification du token:", error);

    return false;
  }
}