import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PreferencesPage from "../pages/PreferencesPage";

vi.mock("../hooks/usePreferences", () => ({
  usePreferences: () => ({
    profile: {},
    settings: {
      theme: "system",
      accent_color: "blue",
      density: "comfortable",
      language: "en",
      timezone: "browser",
      date_format: "DD/MM/YYYY",
      landing_page: "/",
    },
    notificationSettings: {
      email: true,
      sms: false,
      push: true,
      in_app: true,
      frequency: "immediate",
    },
    notifications: [],
    sessions: [],
    devices: [],
    activity: [],
    favorites: [],
    savedFilters: [],
    unread: 0,
    loading: false,
    saving: false,
    error: null,
    load: vi.fn().mockResolvedValue(undefined),
    saveSettings: vi.fn(),
    saveNotifications: vi.fn(),
    revokeSession: vi.fn(),
    searchActivity: vi.fn().mockReturnValue([]),
  }),
}));

describe("PreferencesPage", () => {
  it("renders preference sections", () => {
    render(<PreferencesPage />);
    expect(
      screen.getByRole("heading", {
        name: /User preferences and notification center/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^Notification center$/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Notification settings/i })
    ).toBeInTheDocument();
  });
});
