import { create } from 'zustand'

/** UI locale. `en` is the source language; `pt-BR` is a translation. */
export type Locale = 'en' | 'pt-BR'

export const SUPPORTED_LOCALES: ReadonlyArray<Locale> = ['pt-BR', 'en']

const STORAGE_KEY = 'neq.locale'

function read(): Locale | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === 'en' || value === 'pt-BR' ? value : null
  } catch {
    return null
  }
}

function persist(locale: Locale): void {
  try { localStorage.setItem(STORAGE_KEY, locale) } catch { /* session-only */ }
}

/** Stored choice, then the browser language, then the source language. */
export function detectLocale(): Locale {
  const stored = read()
  if (stored) return stored
  const browserLang = typeof navigator === 'undefined' ? '' : navigator.language
  return browserLang.toLowerCase().startsWith('pt') ? 'pt-BR' : 'en'
}

export function applyDocumentLocale(locale: Locale): void {
  if (typeof document !== 'undefined') document.documentElement.lang = locale
}

export interface LocaleState {
  locale: Locale
  /** A stored choice always wins over the browser language. */
  selected: boolean
  setLocale: (locale: Locale) => void
}

export const useLocale = create<LocaleState>((set) => ({
  locale: detectLocale(),
  selected: read() !== null,
  setLocale: (locale) => {
    persist(locale)
    applyDocumentLocale(locale)
    set({ locale, selected: true })
  },
}))
