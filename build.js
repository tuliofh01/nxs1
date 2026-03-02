const esbuild = require('esbuild');
const sass = require('sass');
const fs = require('fs');

// Build TypeScript
esbuild.build({
  entryPoints: ['src/public/ts/background.ts', 'src/public/ts/internal.ts', 'src/public/ts/ui.ts'],
  outdir: 'src/public/js',
  bundle: true,
  minify: true,
  sourcemap: true,
  target: ['es2020'],
  format: 'esm',
}).catch(() => process.exit(1));

// Build CSS from SASS
const result = sass.compile("src/public/scss/styles.scss");
fs.writeFileSync("src/public/css/styles.css", result.css);
