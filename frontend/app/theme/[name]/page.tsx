// Temporary palette preview: /theme/<name> renders the dashboard with that palette.
import Dashboard from "../../page";

export const revalidate = 60;

// Local installs export HTML without a server to resolve arbitrary route names.
export const dynamicParams = false;

export function generateStaticParams() {
  return ["pumpkin", "witching", "candycorn", "bog"].map((name) => ({ name }));
}

export default Dashboard;
