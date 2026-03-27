import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    category: z.string(),
    description: z.string(),
    readTime: z.number(),
    tags: z.array(z.string()).default([]),
    source: z.string().optional(),
    pdfFile: z.string().optional(),
  }),
});

export const collections = { articles };
