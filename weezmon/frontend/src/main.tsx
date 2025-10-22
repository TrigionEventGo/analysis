import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";
import { Refine } from "@refinedev/core";
import { RouterBindings } from "@refinedev/react-router-v6";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";
import Dashboard from "./pages/Dashboard";
import Companies from "./pages/Companies";
import Events from "./pages/Events";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

const queryClient = new QueryClient();

function Layout() {
  return (
    <div className="min-h-screen">
      <header className="p-4 border-b bg-white dark:bg-gray-800">
        <div className="container mx-auto flex gap-4">
          <a href="/" className="font-semibold">WeezMon</a>
          <nav className="flex gap-3 text-sm">
            <a href="/">Dashboard</a>
            <a href="/companies">Companies</a>
            <a href="/events">Events</a>
            <a href="/reports">Reports</a>
            <a href="/settings">Settings</a>
          </nav>
        </div>
      </header>
      <main className="container mx-auto p-4">
        <Outlet />
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Refine routerProvider={RouterBindings()}>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="companies" element={<Companies />} />
              <Route path="events" element={<Events />} />
              <Route path="reports" element={<Reports />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </Refine>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
