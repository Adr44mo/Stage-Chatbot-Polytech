// Fonction pour la normalisation de l'affichage de date / heure
export function formatDateFrench(dateStr: string | null | undefined): string {
    if (!dateStr) return "-";

    try {
        const date = new Date(dateStr);
        const formatterDate = new Intl.DateTimeFormat("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        timeZone: "Europe/Paris",
        });
        const formatterTime = new Intl.DateTimeFormat("fr-FR", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "Europe/Paris",
        });

        const datePart = formatterDate.format(date);
        const timePart = formatterTime.format(date);

        return `le ${datePart} à ${timePart}`;
    } catch {
        return dateStr;
    }
}
