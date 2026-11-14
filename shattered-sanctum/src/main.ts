import { Game } from "./core/Game";

declare global {
  interface Window {
    /** 除錯用：在 console 輸入 __game 可取得所有系統與參數 */
    __game?: Game;
  }
}

const canvas = document.getElementById("game") as HTMLCanvasElement;
const overlay = document.getElementById("overlay")!;
const overlayText = document.getElementById("overlay-text")!;

async function boot(): Promise<void> {
  const game = await Game.create(canvas, (text) => (overlayText.textContent = text));
  window.__game = game;
  game.start();
  overlay.classList.add("hidden");

  window.addEventListener("keydown", (e) => {
    if (e.code === "F2") {
      e.preventDefault();
      void game.toggleInspector();
    }
  });
}

boot().catch((err) => {
  console.error(err);
  overlayText.textContent = "啟動失敗：" + (err instanceof Error ? err.message : String(err));
});
