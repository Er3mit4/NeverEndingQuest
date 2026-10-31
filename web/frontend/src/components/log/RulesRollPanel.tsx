import { useId, useState } from 'react'
import type { RulesRollPrompt } from '../../contract/events'
import { emitC } from '../../services/socket'
import { useComposerGating } from '../../modes/useComposerGating'
import { useRulesRoll } from '../../stores/rulesRoll'
import './rules-roll.css'
import { useEmberDesktop } from '../layout/EmberPresentation'
import { t, useT, useV } from '../../i18n'

export function RulesRollActions({ prompt }: { prompt: RulesRollPrompt }) {
  const tr = useT()
  const quickFaces = useRulesRoll((state) => state.quickFaces)
  const gating = useComposerGating()
  const locked = !gating.canSend || prompt.submitted
  return <span className="neq-requested-roll-actions">
    {quickFaces.length > 0 && <button type="button" disabled={locked || quickFaces.length !== prompt.faces} onClick={() => emitC('submit_check_roll', { id: prompt.id, faces: quickFaces })}>{tr('Submit rolled dice: {faces}', { faces: quickFaces.join(', ') })}</button>}
    <button type="button" disabled={locked} onClick={() => emitC('submit_check_roll', { id: prompt.id, faces: null })}>{prompt.submitted ? tr('Resolving…') : tr('Roll for me')}</button>
  </span>
}

// #984: the dice the game adds to the check (Guidance, Bless), from typed fields only.
function addedDice(prompt: RulesRollPrompt) {
  return (Array.isArray(prompt.dice) ? prompt.dice : [])
    .filter((d) => Number.isInteger(d?.count) && d.count > 0 && Number.isInteger(d?.sides) && d.sides > 0 && typeof d?.name === 'string')
    .map((d) => ` \u00b7 + ${d.count}d${d.sides} ${d.name} ${t('(the game rolls)')}`)
    .join('')
}

export function RulesRollPanel({ prompt }: { prompt: RulesRollPrompt }) {
  const tr = useT()
  const v = useV()
  const [faces, setFaces] = useState<string[]>([])
  const ember = useEmberDesktop()
  const gating = useComposerGating()
  const locked = !gating.canSend || prompt.submitted
  const isDie = (n: string) => /^\d{1,2}$/.test(n) && Number(n) >= 1 && Number(n) <= 20
  const entries = Array.from({ length: prompt.faces }, (_, i) => faces[i] ?? '')
  const valid = entries.every(isDie)
  // #1117: say why "Use rolls" is off. Only a filled-in field can be wrong; the
  // live region is always rendered so a screen reader announces its new text.
  const bad = entries.map((n) => n !== '' && !isDie(n))
  const errorId = useId()
  const send = (values: number[] | null) => {
    if (locked) return
    emitC('submit_check_roll', { id: prompt.id, faces: values })
  }
  return <section className="neq-rules-roll" aria-label={tr('Requested check')}>
    <div className="neq-rules-roll-title"><strong>{prompt.label}</strong><span>{prompt.characterName}</span></div>
    <p>{prompt.faces === 2 ? tr('Two d20s · {mode}', { mode: v('rollMode', prompt.netMode) }) : tr('One d20')}{addedDice(prompt)}{prompt.dc != null ? tr(' · Difficulty {dc}', { dc: prompt.dc }) : ''}</p>
    {prompt.reason && <p className="neq-rules-roll-reason">{prompt.reason}</p>}
    <div className="neq-rules-roll-actions">
      {!ember && <RulesRollActions prompt={prompt} />}
      <details><summary>{tr('Use my own dice')}</summary><form onSubmit={(e) => { e.preventDefault(); if (valid) send(faces.map(Number)) }}>
        <p>{tr('Enter each die as rolled. Your character’s bonuses are added automatically.')}</p>
        <div>{Array.from({ length: prompt.faces }, (_, i) => <input key={i} aria-label={tr('Die {number}', { number: i + 1 })} type="text" inputMode="numeric" maxLength={2} value={faces[i] ?? ''} disabled={locked} aria-invalid={bad[i] || undefined} aria-describedby={bad[i] ? errorId : undefined} onChange={(e) => setFaces((old) => { const next = [...old]; next[i] = e.target.value; return next })} />)}
          <button type="submit" disabled={locked || !valid}>{tr('Use rolls')}</button></div>
        <p className="neq-rules-roll-error" id={errorId} aria-live="polite">{bad.some(Boolean) ? tr('Each die is a whole number from 1 to 20.') : ''}</p>
      </form></details>
    </div>
  </section>
}
