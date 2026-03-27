export async function GET() {
  const body = [
    'User-agent: *',
    'Allow: /',
    '',
    'Sitemap: https://orgoniteguide.com/sitemap-index.xml',
  ].join('\n');
  return new Response(body, { headers: { 'Content-Type': 'text/plain' } });
}
