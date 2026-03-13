
interface ImportMetaEnv {
  readonly VITE_GOOGLE_CLIENT_ID: string
  readonly VITE_GOOGLE_CLIENT_API_KEY: string
  readonly VITE_BACKEND_URL: string
  readonly VITE_AVAILABLE_MODELS: Object
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}