/** Remove any PHI that older builds cached in localStorage (defense in depth). */
export function purgeLegacyPhi(): void {
  if (typeof window === "undefined") return;
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith("patient_reports_"))
      .forEach((k) => localStorage.removeItem(k));
  } catch {
    /* ignore */
  }
}
