import type { NotificationSettings } from "../../main/notifications/notificationManager";

export function renderNotificationSettings(
  container: HTMLElement,
  settings: NotificationSettings,
  onChange: (settings: NotificationSettings) => void | Promise<void>,
): void {
  const section = document.createElement("section");
  section.className = "notification-settings";

  const enabled = document.createElement("input");
  enabled.type = "checkbox";
  enabled.checked = settings.enabled;
  enabled.addEventListener("change", () => {
    void onChange({ ...settings, enabled: enabled.checked });
  });

  const label = document.createElement("label");
  label.append(enabled, document.createTextNode(" Notifications"));

  const cooldown = document.createElement("input");
  cooldown.type = "number";
  cooldown.min = "0";
  cooldown.value = String(Math.round(settings.cooldown_ms / 60_000));
  cooldown.addEventListener("change", () => {
    void onChange({ ...settings, cooldown_ms: Number(cooldown.value) * 60_000 });
  });

  section.append(label, cooldown);
  container.replaceChildren(section);
}
