import { expect, test } from '@playwright/test'

test('dashboard page loads with app title', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-title')).toBeVisible()
  await expect(page.getByTestId('dashboard-page')).toBeVisible()
})

test('sources page shows source cards', async ({ page }) => {
  await page.goto('/sources')
  await expect(page.getByTestId('sources-page')).toBeVisible()
  await expect(page.getByTestId('source-card').first()).toBeVisible({ timeout: 10000 })
})

test('source detail page loads mock_demand with enabled fetch button', async ({ page }) => {
  await page.goto('/sources/mock_demand')
  await expect(page.getByTestId('source-detail-page')).toBeVisible()
  await expect(page.getByTestId('fetch-button')).toBeVisible()
  await expect(page.getByTestId('fetch-button')).toBeEnabled()
})

test('source detail page loads afdc_ev with enabled fetch button', async ({ page }) => {
  await page.goto('/sources/afdc_ev')
  await expect(page.getByTestId('source-detail-page')).toBeVisible()
  await expect(page.getByTestId('fetch-button')).toBeEnabled()
})

test('source detail page for planned source shows disabled fetch button', async ({ page }) => {
  await page.goto('/sources/epa_egrid')
  await expect(page.getByTestId('source-detail-page')).toBeVisible()
  await expect(page.getByTestId('fetch-button')).toBeDisabled()
})

test('datasets page loads', async ({ page }) => {
  await page.goto('/datasets')
  await expect(page.getByTestId('datasets-page')).toBeVisible()
})

test('weather demand page loads', async ({ page }) => {
  await page.goto('/analysis/weather-demand')
  await expect(page.getByTestId('weather-demand-page')).toBeVisible()
})
