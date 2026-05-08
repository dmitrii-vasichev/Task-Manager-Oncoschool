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

test("dashboard third task card shows completed tasks for the last 7 days", () => {
  const source = readSource("app/page.tsx");

  assert.match(source, /completedInScopeThisWeek/);
  assert.match(source, /done_week/);
  assert.match(source, /Выполнено за 7 дней/);
  assert.match(source, /За последнюю неделю задач не завершали/);
  assert.doesNotMatch(source, /Не обновлялись/);
  assert.doesNotMatch(source, /scopedStaleTasks/);
});
