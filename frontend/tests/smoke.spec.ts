import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { BACKEND_URL, DISCLOSURE, FIXTURES_DIR, FRONTEND_URL, ROOT_DIR, login } from './helpers';

/**
 * Release acceptance journey (offline mock mode, running demo stack, real backend):
 * login -> new application -> invalid uploads rejected -> deck uploaded -> evaluation started ->
 * real progress observed -> six domains / 87 criteria / supervisory / validation ->
 * evidence inspected -> report opened -> PDF downloaded and saved for inspection.
 */
test.describe('TIDES-AI release acceptance journey', () => {
  test.setTimeout(240000);

  test('submit a synthetic application and obtain the validated 87-criterion PDF report', async ({ page }) => {
    const backendCalls: string[] = [];
    page.on('request', (req) => {
      if (req.url().startsWith(BACKEND_URL)) backendCalls.push(`${req.method()} ${new URL(req.url()).pathname}`);
    });
    const pageErrors: string[] = [];
    page.on('pageerror', (err) => pageErrors.push(err.message));

    // 1-2. Authenticate
    await login(page);
    await expect(page.getByRole('heading', { name: 'Incubation Diligence Dashboard' })).toBeVisible();
    await expect(page.getByTestId('mock-disclosure').first()).toHaveText(new RegExp(DISCLOSURE));

    // 3-4. New application with startup information
    await page.goto(`${FRONTEND_URL}/applications/new`);
    await page.getByTestId('submit-application').click();
    await expect(page.locator('text=Please correct the highlighted fields.')).toBeVisible();
    await page.getByTestId('fill-sample').click();
    for (const name of ['information_accurate', 'consent_to_evaluation', 'documents_owned_or_authorised']) {
      await page.locator(`input[name="${name}"]`).check();
    }
    await expect(page.locator('input[name="synthetic_demo_data"]')).toBeChecked();
    const created = page.waitForResponse((r) => r.url() === `${BACKEND_URL}/api/v1/applications` && r.request().method() === 'POST');
    await page.getByTestId('submit-application').click();
    const createdRes = await created;
    expect(createdRes.status()).toBe(201);
    const application = await createdRes.json();
    await expect(page.getByTestId('application-ref')).toHaveText(application.application_ref);

    // 5. Uploads: client-side type rejection, server-side corrupt-content rejection, valid deck
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(path.join(FIXTURES_DIR, 'malicious_binary.exe'));
    await expect(page.getByTestId('upload-error').first()).toContainText('Unsupported file type');
    const corrupt = path.join(os.tmpdir(), `tides_corrupt_${Date.now()}.pdf`);
    fs.writeFileSync(corrupt, 'MZ this is an executable pretending to be a PDF');
    await fileInput.setInputFiles(corrupt);
    await expect(page.getByTestId('upload-error').first()).toContainText('not a document');
    await fileInput.setInputFiles(path.join(FIXTURES_DIR, 'cleanpower_systems_pitch_deck.pdf'));
    await expect(page.getByTestId('uploaded-documents')).toContainText('cleanpower_systems_pitch_deck.pdf');
    await page.getByTestId('finish-uploads').click();

    // 6-7. Application persisted; open it
    await page.getByTestId('open-application').click();
    await page.waitForURL(`**/applications/${application.id}`);
    await expect(page.getByRole('heading', { name: 'CleanPower Systems Pvt Ltd' })).toBeVisible();
    await expect(page.getByTestId('application-documents')).toContainText('cleanpower_systems_pitch_deck.pdf');
    const persisted = await page.request.get(`${BACKEND_URL}/api/v1/applications/${application.id}`, {
      headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('access_token'))}` },
    });
    expect(persisted.status()).toBe(200);

    // 8-9. Start evaluation and observe real backend progress
    await page.getByTestId('start-evaluation').click();
    await expect(page.getByTestId('run-progress')).toBeVisible();
    const evaluationId = (await page.getByTestId('evaluation-id').textContent())?.trim() || '';
    expect(evaluationId).toMatch(/^[0-9a-f-]{36}$/);
    await expect(page.getByTestId('open-results')).toBeVisible({ timeout: 180000 });
    await expect(page.getByTestId('progress-pct')).toHaveText('100%');

    // 10-12. Extraction, claims/evidence and all six domain stages succeeded
    for (const key of ['extraction:cover_intake', 'extraction:financials_support', 'claims', 'domain:problem_solution', 'domain:market_opportunity', 'domain:founder_team', 'domain:commercialisation', 'domain:innovation_impact', 'domain:financials_support', 'supervisory', 'validation']) {
      await expect(page.getByTestId(`stage-${key}`)).toHaveAttribute('data-status', 'SUCCESS');
    }

    // 13-16. Results: 81 domain + 6 cover criteria, supervisory review, report validation
    await page.getByTestId('open-results').click();
    await page.waitForURL(`**/evaluations/run/${evaluationId}`);
    await expect(page.getByTestId('mock-disclosure')).toHaveText(new RegExp(DISCLOSURE));
    await expect(page.getByTestId('coverage-total')).toHaveText('87/87');
    await expect(page.getByTestId('domains-completed')).toHaveText('6/6');
    await expect(page.getByTestId('validation-status')).toContainText('COMPLETED');
    await expect(page.getByTestId('committee-recommendation')).not.toBeEmpty();

    await page.getByTestId('tab-domains').click();
    const expectedCounts: Record<string, number> = {
      problem_solution: 13, market_opportunity: 10, founder_team: 13,
      commercialisation: 13, innovation_impact: 11, financials_support: 21,
    };
    let total = 0;
    for (const [key, count] of Object.entries(expectedCounts)) {
      await page.getByTestId(`domain-tab-${key}`).click();
      await expect(page.locator('[data-testid^="criterion-"]')).toHaveCount(count);
      total += count;
    }
    expect(total).toBe(81);

    // Evidence behind an assessment: inspect a documented criterion
    await page.getByTestId('domain-tab-problem_solution').click();
    await page.getByTestId('inspect-PS-01').click();
    await expect(page.getByTestId('evidence-drawer')).toBeVisible();
    await expect(page.getByTestId('evidence-record').first()).toContainText('Grid outages');
    await page.getByRole('button', { name: 'Close evidence' }).click();

    await page.getByTestId('tab-cover').click();
    for (const cm of ['CM-01', 'CM-02', 'CM-03', 'CM-04', 'CM-05', 'CM-06']) {
      await expect(page.getByTestId(`criterion-${cm}`)).toBeVisible();
    }

    await page.getByTestId('tab-supervisory').click();
    await expect(page.getByTestId('supervisory-panel')).toContainText('Supervisory synthesis');
    await expect(page.getByTestId('supervisory-panel')).toContainText('COMPLETED');

    // 17-19. Report: open in viewer, download, and save for inspection
    await page.getByTestId('tab-report').click();
    await page.getByTestId('load-report').click();
    await expect(page.getByTestId('report-viewer')).toBeVisible({ timeout: 30000 });
    const downloadPromise = page.waitForEvent('download');
    await page.getByTestId('download-report').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/^MOCK_DEMO_TIDES_Due_Diligence_.*\.pdf$/);
    const outDir = path.join(ROOT_DIR, 'reports', 'demo_acceptance');
    fs.mkdirSync(outDir, { recursive: true });
    const saved = path.join(outDir, 'acceptance_report.pdf');
    await download.saveAs(saved);
    const bytes = fs.readFileSync(saved);
    expect(bytes.subarray(0, 5).toString()).toBe('%PDF-');
    expect(bytes.length).toBeGreaterThan(20000);
    fs.writeFileSync(path.join(outDir, 'acceptance_run.json'), JSON.stringify({
      evaluation_id: evaluationId,
      application_id: application.id,
      application_ref: application.application_ref,
      startup_id: application.startup_id,
      pdf: saved,
      backend_calls: backendCalls,
    }, null, 2));

    // Browser talked to the real backend endpoints throughout
    for (const call of [
      'POST /api/v1/auth/login',
      'POST /api/v1/applications',
      `POST /api/v1/applications/${application.id}/documents`,
      `POST /api/v1/applications/${application.id}/evaluations`,
      `GET /api/v1/evaluation-runs/${evaluationId}`,
      `GET /api/v1/evaluation-runs/${evaluationId}/results`,
      `GET /api/v1/evaluation-runs/${evaluationId}/report.pdf`,
    ]) {
      expect(backendCalls).toContain(call);
    }
    expect(pageErrors).toEqual([]);
  });
});
