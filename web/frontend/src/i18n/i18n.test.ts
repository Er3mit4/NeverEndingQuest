// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { ptBR } from './pt-BR'
import { formatSaveDate, t, tn, translate, v } from './index'
import { useLocale } from '../stores/locale'
import type { WaitRecord } from '../contract/events'
import { waitStatusText } from '../components/log/turnStatus'

const SOURCE_ROOT = join(__dirname, '..')

function sourceFiles(): string[] {
  const files: string[] = []
  const walk = (dir: string) => {
    for (const name of readdirSync(dir)) {
      const path = join(dir, name)
      if (statSync(path).isDirectory()) walk(path)
      else if (/\.(ts|tsx)$/.test(name) && !/\.test\.tsx?$/.test(name) && !path.includes(`${join('i18n', 'fragments')}`)) files.push(path)
    }
  }
  walk(SOURCE_ROOT)
  return files
}

describe('pt-BR dictionary', () => {
  it('has no empty translations', () => {
    const bad = Object.entries(ptBR).filter(([, value]) => value.trim() === '')
    expect(bad).toEqual([])
  })

  it('covers every literal key passed to t() or tn() in src', () => {
    const keys = new Set<string>()
    for (const file of sourceFiles()) {
      const text = readFileSync(file, 'utf8')
      for (const match of text.matchAll(/\btn\(\s*'((?:[^'\\]|\\.)+)'/g)) keys.add(match[1]!.replace(/\\'/g, "'"))
      for (const match of text.matchAll(/\bt\(\s*'((?:[^'\\]|\\.)+)'/g)) keys.add(match[1]!.replace(/\\'/g, "'"))
      for (const match of text.matchAll(/\bt\(\s*"((?:[^"\\]|\\.)+)"/g)) keys.add(match[1]!.replace(/\\"/g, '"'))
    }
    const missing = [...keys].filter((key) => !(key in ptBR))
    expect(missing).toEqual([])
  })

  it('keeps English as the source language', () => {
    expect(translate('en', 'Save')).toBe('Save')
    expect(translate('en', 'The Dungeon Master is answering')).toBe('The Dungeon Master is answering')
  })

  it('translates known keys', () => {
    expect(translate('pt-BR', 'Save')).toBe('Salvar')
    expect(translate('pt-BR', 'Character sheet')).toBe('Ficha do personagem')
  })
})

describe('interpolation and helpers', () => {
  it('fills named placeholders and leaves unknown ones alone', () => {
    expect(translate('pt-BR', 'Total: {total}', { total: 12 })).toBe('Total: 12')
    expect(translate('pt-BR', 'Total: {total}')).toBe('Total: {total}')
    expect(translate('pt-BR', 'Restoring save... the page will reload when the server is ready.'))
      .toBe('Restaurando o salvamento... a página será recarregada quando o servidor estiver pronto.')
  })

  it('picks the singular and plural form through tn()', () => {
    useLocale.getState().setLocale('pt-BR')
    expect(tn('{count} listed spell', '{count} listed spells', 1)).toBe('1 magia listada')
    expect(tn('{count} listed spell', '{count} listed spells', 4)).toBe('4 magias listadas')
  })

  it('formats save timestamps for pt-BR and keeps English untouched', () => {
    useLocale.getState().setLocale('en')
    expect(formatSaveDate('2026-10-25 14:30:00')).toBe('2026-10-25 14:30:00')
    useLocale.getState().setLocale('pt-BR')
    expect(formatSaveDate('2026-10-25 14:30:00')).toBe('25/10/2026 14:30')
    expect(formatSaveDate('not a date')).toBe('not a date')
  })

  it('maps controlled vocabulary and keeps unknown values', () => {
    useLocale.getState().setLocale('pt-BR')
    expect(v('ability', 'strength')).toBe('Força')
    expect(v('skill', 'Sleight_of_Hand')).toBe('Prestidigitação')
    expect(v('itemType', 'weapon')).toBe('arma')
    expect(v('coin', 'GP')).toBe('PO')
    expect(v('condition', 'poisoned')).toBe('Envenenado')
    expect(v('condition', 'homebrew_curse')).toBe('homebrew_curse')
    expect(v('ability', null)).toBe('')
  })

  it('renders a waiting turn in Portuguese', () => {
    useLocale.getState().setLocale('pt-BR')
    const wait: WaitRecord = {
      kind: 'provider_call', purpose: 'turn', taskId: 'T001', provider: 'openai', providerName: 'OpenAI',
      attempt: 1, maxAttempts: null, elapsedMs: 5_000, phase: 'working', lastActivityMs: 2_000, retryInMs: null,
    }
    expect(waitStatusText(wait, 0)).toBe('O Mestre está respondendo (5 s): OpenAI está trabalhando (última atividade há 2 s).')
  })
})

afterEach(() => {
  useLocale.getState().setLocale('en')
  expect(t('Save')).toBe('Save')
})
