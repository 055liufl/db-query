import { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import React from "react";
import ReactDOM from "react-dom/client";

loader.config({ monaco });
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider, App as AntdApp } from "antd";
import zhCN from "antd/locale/zh_CN";
import { App } from "./App";
import { mdTheme } from "./theme";
import "./index.css";

const rootEl = document.getElementById("root");
if (!rootEl) {
  throw new Error("root element missing");
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={mdTheme}>
      <AntdApp>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <App />
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>,
);
