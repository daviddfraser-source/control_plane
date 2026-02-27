const { chromium } = require('playwright');

async function testPages() {
  console.log('Starting Playwright inspection...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Capture console messages and errors
  page.on('console', msg => {
    const type = msg.type();
    if (type === 'error' || type === 'warning') {
      console.log(`[BROWSER ${type.toUpperCase()}]:`, msg.text());
    }
  });

  page.on('pageerror', error => {
    console.log('[PAGE ERROR]:', error.message);
  });

  const routes = [
    '/',
    '/dashboard',
    '/packets',
    '/audit',
    '/risks',
    '/graph',
    '/settings'
  ];

  for (const route of routes) {
    try {
      console.log(`\n========================================`);
      console.log(`Testing: http://localhost:3000${route}`);
      console.log(`========================================`);

      const response = await page.goto(`http://localhost:3000${route}`, {
        waitUntil: 'domcontentloaded',
        timeout: 10000
      });

      console.log(`Status: ${response.status()}`);

      // Wait a bit for client-side rendering
      await page.waitForTimeout(2000);

      // Check for errors in the page
      const errorText = await page.textContent('body').catch(() => '');
      if (errorText.includes('Error') || errorText.includes('error')) {
        console.log('⚠️  Error detected in page content');
        const bodyText = await page.textContent('body');
        console.log('Body preview:', bodyText.substring(0, 500));
      }

      // Get page title
      const title = await page.title();
      console.log(`Title: ${title}`);

      // Check if main content loaded
      const hasContent = await page.evaluate(() => {
        const body = document.body;
        return body && body.children.length > 0;
      });
      console.log(`Has content: ${hasContent}`);

      // Take a screenshot
      await page.screenshot({
        path: `/tmp/playwright-${route.replace('/', 'root')}.png`,
        fullPage: true
      });
      console.log(`Screenshot saved: /tmp/playwright-${route.replace('/', 'root')}.png`);

    } catch (error) {
      console.log(`❌ Error testing ${route}:`, error.message);
    }
  }

  await browser.close();
  console.log('\n✅ Playwright inspection complete');
}

testPages().catch(console.error);
