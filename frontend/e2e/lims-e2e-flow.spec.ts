import { test, expect } from "@playwright/test";

test.describe("LIMS — Fluxo Ponta a Ponta de Fiscalização Pós-Mercado", () => {
  test("deve exibir a tela de login com conformidade regulatória", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveTitle(/LIMS/i);
    await expect(page.locator("text=Assinatura eletrônica")).toBeVisible();
    await expect(page.locator("text=Trilha de auditoria")).toBeVisible();
    await expect(page.locator("text=Rastreabilidade ponta a ponta")).toBeVisible();
  });

  test("deve permitir navegação para a rota de verificação pública de laudo", async ({ page }) => {
    await page.goto("/public/verify");
    await expect(page.locator("text=Verificação Pública")).toBeVisible();
  });
});
