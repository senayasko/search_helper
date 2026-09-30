/// <reference types="vite/client" />

interface Window {
  desktop?: {
    readCsv: () => Promise<string>;
    minimize: () => Promise<void>;
    toggleMaximize: () => Promise<void>;
    close: () => Promise<void>;
  };
}
