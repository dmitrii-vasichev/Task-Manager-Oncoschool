import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const srcDir = join(process.cwd(), "src");

function readSource(path: string): string {
  return readFileSync(join(srcDir, path), "utf8");
}

test("projects route exposes register and create affordances", () => {
  const source = readSource("app/projects/page.tsx");

  assert.match(source, /CreateProjectDialog/);
  assert.match(source, /ProjectFilters/);
  assert.match(source, /ProjectRegisterRow/);
});

test("sidebar exposes projects navigation", () => {
  const source = readSource("components/layout/Sidebar.tsx");

  assert.match(source, /href:\s*"\/projects"/);
  assert.match(source, /label:\s*"Проекты"/);
});
