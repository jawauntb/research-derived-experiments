import { renderApp, type InquiryDesktopBridge } from "./App";

declare global {
  interface Window {
    inquiryDesktop?: InquiryDesktopBridge;
  }
}

const root = document.getElementById("app");

if (!root) {
  throw new Error("missing #app root");
}

if (!window.inquiryDesktop) {
  root.textContent = "Desktop bridge unavailable.";
} else {
  renderApp(root, window.inquiryDesktop);
}
