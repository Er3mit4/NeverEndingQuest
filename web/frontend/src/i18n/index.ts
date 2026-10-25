/**
 * Tiny i18n layer: no dependency, no runtime catalogue loading.
 *
 * `t()` takes the exact English UI string as its key. `pt-BR.ts` maps it to
 * Portuguese, so a translated UI never changes component structure and the
 * English build keeps working unchanged.
 */

import { useLocale, type Locale } from '../stores/locale'
import { ptBR } from './pt-BR'
import { vocabulary, type VocabGroup } from './vocabulary'

export type { Locale, VocabGroup }
export type Params = Record<string, string | number>
export type MessageKey = keyof typeof ptBR

function interpolate(text: string, params?: Params): string {
  if (!params) return text
  return text.replace(/\{(\w+)\}/g, (match, name: string) => {
    const value = params[name]
    return value === undefined ? match : String(value)
  })
}

export function translate(locale: Locale, key: MessageKey, params?: Params): string {
  const text = locale === 'pt-BR' ? ptBR[key] : key
  return interpolate(text, params)
}

/** Translate with the current locale (non-reactive; use `useT` in components). */
export function t(key: MessageKey, params?: Params): string {
  return translate(useLocale.getState().locale, key, params)
}

/** Reactive `t`: subscribes the component to locale changes. */
export function useT(): typeof t {
  useLocale((s) => s.locale)
  return t
}

/** Pick `one` for a single unit and `other` for zero/many, with `{count}` filled. */
export function tn(one: MessageKey, other: MessageKey, count: number, params?: Params): string {
  return t(count === 1 ? one : other, { count, ...params })
}

/** Translate a controlled data value (attributes, skills, item types...). */
export function v(group: VocabGroup, value: string | null | undefined): string {
  if (!value) return ''
  return vocabulary(useLocale.getState().locale, group, value)
}

/** Reactive `v` for components that only render data values. */
export function useV(): typeof v {
  useLocale((s) => s.locale)
  return v
}

export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  const locale = useLocale.getState().locale
  return new Intl.NumberFormat(locale === 'en' ? 'en-US' : locale, options).format(value)
}

/** `2026-10-25 14:30:00` -> `25/10/2026 14:30` in pt-BR; untouched in English. */
export function formatSaveDate(value: string): string {
  if (useLocale.getState().locale !== 'pt-BR') return value
  const match = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/.exec(value)
  if (!match) return value
  const [, year, month, day, hour, minute] = match
  return hour ? `${day}/${month}/${year} ${hour}:${minute}` : `${day}/${month}/${year}`
}
