import { capitalizeWords, formatModifier, rec, type SpellcastingView } from './characterData'
import { tn, useT, useV } from '../../i18n'
import '../../theme/tavern-inventory-spells.css'

/** Read every recorded slot level, including higher-level slots used for upcasting. */
export function SpellcastingSummary({ data, casting }: { data: Record<string, unknown>; casting: SpellcastingView }) {
  const t = useT()
  const v = useV()
  const rawSlots = rec(rec(data['spellcasting'])?.['spellSlots'])
  const slots = Array.from({ length: 9 }, (_, i) => {
    const level = i + 1
    const raw = rec(rawSlots?.[`level${level}`])
    if (!raw || typeof raw['current'] !== 'number' || typeof raw['max'] !== 'number' || !Number.isFinite(raw['current']) || !Number.isFinite(raw['max'])) return null
    return { level, current: raw['current'], max: raw['max'] }
  }).filter(slot => slot !== null)
  const spellCount = new Set(casting.levels.flatMap(group => group.spells)).size
  return <section className="tis-casting-summary" aria-label={t('Spellcasting resources')}>
    <div className="tis-casting-overview"><div><span className="tis-eyebrow">{t('Spellcasting')}</span><h4>{casting.ability ? t('{ability} caster', { ability: v('ability', capitalizeWords(casting.ability)) }) : t('Spellcaster')}</h4><span className="tis-spell-count">{tn('{count} listed spell', '{count} listed spells', spellCount)}{casting.prepared.length > 0 ? t(' · {count} prepared', { count: new Set(casting.prepared).size }) : ''}</span></div>
      <dl>{casting.saveDC !== null && <div><dt>{t('Save DC')}</dt><dd>{casting.saveDC}</dd></div>}{casting.attackBonus !== null && <div><dt>{t('Spell attack')}</dt><dd>{formatModifier(casting.attackBonus)}</dd></div>}</dl>
    </div>
    {slots.length > 0 ? <><div className="tis-slot-levels">{slots.map(slot => <div key={slot.level} className="tis-slot-level" role="group" aria-label={t('Level {level} spell slots: {current} of {max} available', { level: slot.level, current: slot.current, max: slot.max })}>
      <span className="tis-slot-label">{t('Level {level}', { level: slot.level })}</span><strong>{slot.current}<small>{t(' / {max} available', { max: slot.max })}</small></strong>
      {slot.max > 0 && slot.max <= 12 && Number.isInteger(slot.max) && <span className="tis-slot-pips" aria-hidden="true">{Array.from({length:slot.max}, (_, index) => <i key={index} className={index < slot.current ? 'is-available' : 'is-spent'} />)}</span>}
    </div>)}</div><p className="tis-slot-legend">{t('Filled: available')} <span aria-hidden="true">·</span> {t('Outlined: spent')}</p></> : <p className="tis-slot-legend">{casting.levels.every(level => level.levelIndex === 0) ? t('Cantrips do not use spell slots.') : t('No spell-slot totals recorded.')}</p>}
  </section>
}
