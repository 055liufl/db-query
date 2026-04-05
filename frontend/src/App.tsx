import { Refine } from "@refinedev/core";
import routerBindings from "@refinedev/react-router-v6";
import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { dataProvider } from "./providers/dataProvider";
import { WorkspacePage } from "./pages/WorkspacePage";

function LegacyQueryRedirect() {
  const { name } = useParams<{ name: string }>();
  return <Navigate to={`/db/${encodeURIComponent(name)}`} replace />;
}

export function App() {
  return (
    <Refine
      routerProvider={routerBindings}
      dataProvider={dataProvider}
      options={{ disableTelemetry: true }}
      resources={[{ name: "dbs", list: "/" }]}
    >
      <div className="h-full min-h-screen">
        <Routes>
          <Route path="/" element={<WorkspacePage />} />
          <Route path="/db/:name" element={<WorkspacePage />} />
          <Route path="/query/:name" element={<LegacyQueryRedirect />} />
        </Routes>
      </div>
    </Refine>
  );
}
