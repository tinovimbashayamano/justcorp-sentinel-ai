import { describe, expect, it } from "vitest";
import {
  activeSessions,
  filterActivity,
  normalizeNotificationSettings,
  normalizeSettings,
  notificationSeverity,
  sortNotifications,
  toggleFavorite,
  unreadCount,
} from "../domain/preferences";

describe("preferences domain", () => {
  it("normalizes settings", () => {
    expect(normalizeSettings({ theme: "dark" }).theme).toBe("dark");
  });

  it("uses default settings", () => {
    expect(normalizeSettings({}).language).toBe("en");
  });

  it("normalizes notification settings", () => {
    expect(normalizeNotificationSettings({ sms: true }).sms).toBe(true);
  });

  it("sorts notifications newest first", () => {
    const result = sortNotifications([
      { id: 1, timestamp: "2026-07-27" },
      { id: 2, timestamp: "2026-07-28" },
    ]);
    expect(result[0].id).toBe(2);
  });

  it("counts unread notifications", () => {
    expect(
      unreadCount([
        { read: false, archived: false },
        { read: true, archived: false },
      ])
    ).toBe(1);
  });

  it("filters revoked sessions", () => {
    expect(
      activeSessions([
        { id: 1, revoked: false },
        { id: 2, revoked: true },
      ])
    ).toHaveLength(1);
  });

  it("adds a favorite", () => {
    expect(toggleFavorite([], "report-1")).toContain("report-1");
  });

  it("removes a favorite", () => {
    expect(toggleFavorite(["report-1"], "report-1")).toHaveLength(0);
  });

  it("filters activity", () => {
    expect(
      filterActivity(
        [{ id: 1, description: "Password changed" }],
        "password"
      )
    ).toHaveLength(1);
  });

  it("normalizes unsupported notification severity", () => {
    expect(notificationSeverity("urgent")).toBe("normal");
  });
});
