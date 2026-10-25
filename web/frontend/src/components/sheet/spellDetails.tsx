/** Presentation-only reference details; never resolves or executes spell mechanics. */
import { useT, useV } from '../../i18n'

function text(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

export function SpellDetails({ detail, fallbackName }: {
  detail?: Record<string, unknown>
  fallbackName: string
}) {
  const t = useT()
  const v = useV()
  const name = text(detail?.name) || fallbackName
  if (!detail || !Object.keys(detail).length) return <>
    <h4 className="ember-inspection-title">{name}</h4>
    <p className="ember-inspection-description">{t('Spell reference details are unavailable. Your character’s spell list is unchanged.')}</p>
  </>

  const components = detail.components && typeof detail.components === 'object' && !Array.isArray(detail.components)
    ? detail.components as Record<string, unknown> : undefined
  const componentNames = components
    ? [['verbal', 'V'], ['somatic', 'S'], ['material', 'M']].filter(([key]) => components[key] === true).map(([, label]) => label).join(', ')
    : text(detail.components)
  const level = typeof detail.level === 'number' && Number.isFinite(detail.level)
    ? detail.level === 0 ? v('spellLevel', 'Cantrip') : t('Level {level}', { level: detail.level }) : ''
  const classes = Array.isArray(detail.classes) ? detail.classes.map(text).filter(Boolean).join(', ') : text(detail.classes)
  const rows: [string, string][] = [
    [t('Level'), level], [t('School'), v('school', text(detail.school))], [t('Casting time'), text(detail.casting_time)],
    [t('Range'), text(detail.range)], [t('Components'), componentNames],
    [t('Materials'), text(components?.materials) || text(detail.materials)], [t('Duration'), text(detail.duration)],
    [t('Ritual'), typeof detail.ritual === 'boolean' ? detail.ritual ? t('Yes') : t('No') : ''],
    [t('Concentration'), typeof detail.concentration === 'boolean' ? detail.concentration ? t('Yes') : t('No') : ''],
    [t('Classes'), classes],
  ]
  return <>
    <h4 className="ember-inspection-title">{name}</h4>
    <dl className="ember-inspection-meta">{rows.filter(([, value]) => value).map(([label, value]) =>
      <div key={label}><dt>{label}</dt><dd>{value}</dd></div>,
    )}</dl>
    <p className="ember-inspection-description">{text(detail.description) || t('Spell description is unavailable.')}</p>
    {text(detail.higher_levels) && <section className="ember-inspection-section">
      <h5>{t('At higher levels')}</h5><p className="ember-inspection-description">{text(detail.higher_levels)}</p>
    </section>}
    {text(detail.source) && <p className="ember-inspection-source">{t('Source: {source}', { source: text(detail.source) })}{text(detail.version) && !text(detail.source).includes(text(detail.version)) ? ` · ${text(detail.version)}` : ''}</p>}
    {text(detail._srd_attribution) && <p className="ember-inspection-source">{text(detail._srd_attribution)}</p>}
  </>
}
