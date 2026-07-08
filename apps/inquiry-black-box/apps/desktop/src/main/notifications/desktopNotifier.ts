import electron from "electron";

export type DesktopNotificationInput = {
  title: string;
  body: string;
};

export type DesktopNotifier = {
  show(input: DesktopNotificationInput): Promise<"shown" | "failed">;
};

export function createElectronDesktopNotifier(): DesktopNotifier {
  const { Notification } = electron;
  return {
    async show(input) {
      if (!Notification.isSupported()) {
        return "failed";
      }
      const notification = new Notification({
        title: input.title,
        body: input.body,
      });
      notification.show();
      return "shown";
    },
  };
}
