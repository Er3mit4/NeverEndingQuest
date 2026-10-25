import { useState } from 'react'
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
  const valid = Array.from({ length: prompt.faces }, (_, i) => faces[i] ?? '')
    .every((n) => /^\d{1,2}$/.test(n) && Number(n) >= 1 && Number(n) <= 20)
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
        <div>{Array.from({ length: prompt.faces }, (_, i) => <input key={i} aria-label={tr('Die {number}', { number: i + 1 })} type="text" inputMode="numeric" maxLength={2} value={faces[i] ?? ''} disabled={locked} onChange={(e) => setFaces((old) => { const next = [...old]; next[i] = e.target.value; return next })} />)}
          <button type="submit" disabled={locked || !valid}>{tr('Use rolls')}</button></div>
      </form></details>
    </div>
  </section>
}
