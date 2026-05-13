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

test("projects filters expose text search and forward it to the API query", () => {
  const filters = readSource("components/projects/ProjectFilters.tsx");
  const page = readSource("app/projects/page.tsx");

  assert.match(filters, /search/);
  assert.match(filters, /Поиск/);
  assert.match(page, /params\.search/);
});

test("projects filters use friendly source and calendar controls", () => {
  const filters = readSource("components/projects/ProjectFilters.tsx");
  const page = readSource("app/projects/page.tsx");

  assert.doesNotMatch(filters, /ID идеи/);
  assert.doesNotMatch(filters, /source_idea_id/);
  assert.match(filters, /Источник/);
  assert.match(filters, /Из идеи/);
  assert.match(filters, /Без идеи/);
  assert.match(filters, /DatePicker/);
  assert.doesNotMatch(filters, /YYYY-MM-DD/);
  assert.match(page, /params\.source/);
  assert.doesNotMatch(page, /params\.source_idea_id/);
});

test("project register rows keep a compact metadata layout", () => {
  const source = readSource("components/projects/ProjectRegisterRow.tsx");

  assert.match(source, /py-2\.5/);
  assert.match(source, /flex flex-wrap/);
  assert.doesNotMatch(
    source,
    /xl:grid-cols-\[minmax\(0,1\.1fr\)_minmax\(280px,0\.9fr\)_auto\]/,
  );
  assert.doesNotMatch(source, /xl:flex-col/);
});

test("sidebar exposes projects navigation", () => {
  const source = readSource("components/layout/Sidebar.tsx");

  assert.match(source, /href:\s*"\/projects"/);
  assert.match(source, /label:\s*"Проекты"/);
});

test("project detail route composes operational detail panels", () => {
  const source = readSource("app/projects/[id]/page.tsx");

  assert.match(source, /ProjectStatusPanel/);
  assert.match(source, /ProjectDepartmentPanel/);
  assert.match(source, /ProjectMilestones/);
  assert.match(source, /ProjectLinkedTasks/);
  assert.match(source, /ProjectComments/);
  assert.match(source, /ProjectEventHistory/);
});

test("idea detail route exposes project conversion affordance", () => {
  const source = readSource("app/ideas/[id]/page.tsx");

  assert.match(source, /CreateProjectFromIdeaDialog/);
  assert.match(source, /Создать проект/);
  assert.match(source, /\/projects\/\$\{idea\.project\.id\}/);
});
