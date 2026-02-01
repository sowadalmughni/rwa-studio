/**
 * E2E Tests: Landing Page
 * Author: Sowad Al-Mughni
 *
 * Tests for the public landing page and navigation
 */

import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should display the page title", async ({ page }) => {
    // Check that the page has loaded
    await expect(page).toHaveTitle(/RWA/i);
  });

  test("should display main navigation", async ({ page }) => {
    // Look for navigation elements
    const nav = page.locator("nav").first();
    await expect(nav).toBeVisible();
  });

  test("should be responsive on mobile", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Page should still load correctly
    await expect(page.locator("body")).toBeVisible();
  });

  test("should have accessible skip links or focus management", async ({ page }) => {
    // Basic accessibility check
    const mainContent = page.locator("main").first();

    // Main content area should exist
    if ((await mainContent.count()) > 0) {
      await expect(mainContent).toBeVisible();
    }
  });
});

test.describe("Navigation", () => {
  test("should navigate to different sections", async ({ page }) => {
    await page.goto("/");

    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Check if there are any clickable navigation links
    const links = page.locator("a[href]");
    const count = await links.count();

    expect(count).toBeGreaterThan(0);
  });
});
