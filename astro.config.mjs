// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import { visit } from 'unist-util-visit';

function rehypeInjectAds() {
  return (tree) => {
    const adDiv = (slot) => ({
      type: 'element',
      tagName: 'div',
      properties: { className: ['ad-in-content', 'my-8', 'flex', 'justify-center'] },
      children: [{
        type: 'element',
        tagName: 'ins',
        properties: {
          className: ['adsbygoogle'],
          style: 'display:block;width:100%;max-width:336px',
          'data-ad-client': 'ca-pub-XXXXXXXXXXXXXXXX',
          'data-ad-slot': slot,
          'data-ad-format': 'rectangle',
        },
        children: []
      }]
    });
    let pCount = 0;
    const newChildren = [];
    for (const node of tree.children) {
      newChildren.push(node);
      if (node.type === 'element' && node.tagName === 'p') {
        pCount++;
        if (pCount === 3) newChildren.push(adDiv('1111111111'));
        if (pCount === 7) newChildren.push(adDiv('2222222222'));
      }
    }
    if (pCount < 7) newChildren.push(adDiv('2222222222'));
    tree.children = newChildren;
  };
}

export default defineConfig({
  site: 'https://orgoniteguide.com',
  vite: {
    plugins: [tailwindcss()]
  },
  integrations: [sitemap()],
  markdown: {
    rehypePlugins: [rehypeInjectAds],
  },
});
