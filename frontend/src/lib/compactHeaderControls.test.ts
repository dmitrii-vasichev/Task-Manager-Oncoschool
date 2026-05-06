import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const sourceRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

function readSource(relativePath: string) {
  return readFileSync(path.join(sourceRoot, relativePath), "utf8");
}

test("task board header controls match the compact meeting button height", () => {
  const tasksPage = readSource("app/tasks/page.tsx");
  const taskFilters = readSource("components/tasks/TaskFilters.tsx");

  assert.match(
    tasksPage,
    /className="h-8 w-full rounded-xl gap-1\.5 px-3 text-xs sm:w-auto xl:shrink-0"/,
  );
  assert.match(
    taskFilters,
    /"h-8 w-full rounded-xl border-border\/70 bg-background\/80 shadow-none/,
  );
  assert.match(
    taskFilters,
    /className="h-8 w-full rounded-xl border-border\/70 bg-background\/80 pl-9 pr-9 text-xs shadow-none focus:border-primary\/40"/,
  );
  assert.match(
    taskFilters,
    /className="h-8 rounded-xl gap-1\.5 border-border\/70 bg-background\/80 px-3 text-xs shadow-none"/,
  );
});

test("top-level meeting and team search fields use the compact header height", () => {
  const meetingsPage = readSource("app/meetings/page.tsx");
  const teamPage = readSource("app/team/page.tsx");

  assert.match(
    meetingsPage,
    /className="pl-9 h-8 rounded-xl bg-card border-border\/60 text-xs"/,
  );
  assert.match(
    teamPage,
    /className="pl-9 h-8 rounded-xl bg-card border-border\/60 text-xs"/,
  );
});
