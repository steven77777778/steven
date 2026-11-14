import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  // Havok 的 .wasm 不能被 esbuild 預先打包，否則找不到 wasm 檔
  optimizeDeps: { exclude: ["@babylonjs/havok"] },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 4000,
  },
  server: { host: true, port: 5173 },
});
