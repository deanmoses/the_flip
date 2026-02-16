import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['flipfix/static/**/*.test.js'],
  },
});
