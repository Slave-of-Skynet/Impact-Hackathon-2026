/* Zero-dependency DOM simulation for achievement notification lifecycle (#83). */
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const script = fs.readFileSync(path.join(__dirname, "../static/js/achievement_notices.js"), "utf8");
const child1 = "00000000-0000-0000-0000-000000000001";
const child2 = "00000000-0000-0000-0000-000000000002";

function run(readerId, codes, storage, blocked = false) {
  const timers = new Map();
  const banners = codes.map((code) => {
    const listeners = {};
    const button = { addEventListener: (event, cb) => { listeners[event] = cb; } };
    return {
      code, removed: false, button, listeners,
      getAttribute: (name) => name === "data-grant-code" ? code : null,
      querySelector: (sel) => sel === ".child-grant-dismiss" ? button : null,
      remove() { this.removed = true; }
    };
  });
  const root = {
    getAttribute: (name) => name === "data-reader-id" ? readerId : null,
    querySelectorAll: () => banners
  };
  let onReady = null, clock = 0;
  const document = {
    readyState: "loading",
    getElementById: (id) => id === "child-grant-notices" ? root : null,
    addEventListener: (name, handler) => { if (name === "DOMContentLoaded") onReady = handler; }
  };
  const window = {
    localStorage: {
      getItem: (key) => {
        if (blocked) throw Error("storage blocked");
        return storage.get(key) || null;
      },
      setItem: (key, value) => {
        if (blocked) throw Error("storage blocked");
        storage.set(key, value);
      }
    },
    setTimeout: (fn, delay) => { assert.strictEqual(delay, 7000); timers.set(++clock, fn); return clock; },
    clearTimeout: (id) => timers.delete(id)
  };
  vm.runInNewContext(script, { window, document, Set, Array, JSON });
  assert.strictEqual(typeof onReady, "function");
  onReady();
  return { banners, timers, window };
}
const storage = new Map();
const a = run(child1, ["first-book", "pages-100"], storage);
assert.strictEqual(a.banners[0].removed, false);
assert.strictEqual(a.timers.size, 2);
a.banners[0].listeners.click();
assert.strictEqual(a.banners[0].removed, true);
assert.strictEqual(a.banners[1].removed, false);
assert.strictEqual(a.timers.size, 1);
const dismissLast = [...a.timers.values()][0];
dismissLast();
assert.strictEqual(a.banners[1].removed, true);
const remembered = JSON.parse(storage.get("gustul:seen-achievements:v1:" + child1));
assert.deepStrictEqual(remembered, ["first-book", "pages-100"]);
const revisited = run(child1, ["first-book", "pages-100"], storage);
assert(revisited.banners.every((b) => b.removed), "Viewed grants must not reappear on reload");
assert.strictEqual(revisited.timers.size, 0);
const anotherChild = run(child2, ["first-book"], storage);
assert.strictEqual(anotherChild.banners[0].removed, false, "Another child may see their own trophy");
const storageDenied = run(child1, ["new-grant"], storage, true);
assert.strictEqual(storageDenied.timers.size, 1);
storageDenied.banners[0].listeners.click();
assert.strictEqual(storageDenied.banners[0].removed, true);
const timerDenied = run(child1, ["new-grant"], storage, true);
[...timerDenied.timers.values()][0]();
assert.strictEqual(timerDenied.banners[0].removed, true);
console.log("Achievement notices: manual close, 7s auto-hide, per-child persistence, storage fallback PASS");