/*
  Composant Spinner
  Affiche un indicateur de chargement
*/

export default function Spinner() {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: 16 }}>
      <div className="spinner" />
    </div>
  );
}
