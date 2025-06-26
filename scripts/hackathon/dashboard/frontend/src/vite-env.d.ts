/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_USE_STATIC?: string
  readonly VITE_API_TARGET?: string
  readonly PROD?: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 