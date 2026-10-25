import { createPortal } from 'react-dom'
import { DialogShell } from '../dialogs/DialogShell'
import { EmberInspection } from './EmberInspection'
import { EquipmentDetails } from './EquipmentDetails'
import { SpellDetails } from './spellDetails'
import { spellKey } from './spellKey'
import { useSpellReference } from './useSpellReference'
import { useEmberDesktop } from '../layout/EmberPresentation'
import { SpellcastingSummary } from './SpellcastingSummary'
import { useT, useV } from '../../i18n'
import {
  arr,
  equipmentList,
  formatModifier,
  rec,
  saveRows,
  skillRows,
  slotTone,
  spellcastingView,
  str,
} from './characterData'

export type NpcModalKind =
  | 'saves'
  | 'skills'
  | 'inventory'
  | 'features'
  | 'traits'
  | 'background'
  | 'spells'

const TITLES = {
  saves: 'Saving Throws',
  skills: 'Skills',
  inventory: 'Inventory',
  features: 'Key Abilities',
  traits: 'Racial Traits',
  background: 'Background',
  spells: 'Spellcasting',
} as const satisfies Record<NpcModalKind, string>

function featureUsage(item: Record<string, unknown>) {
  const usage = rec(item['usage'])
  const count = usage && typeof usage['current'] === 'number' && typeof usage['max'] === 'number' ? `${usage['current']}/${usage['max']}` : str(item['usage'])
  return [count, str(item['refresh']) || str(usage?.['refreshOn']) || str(usage?.['refresh'])].filter(Boolean).join(' · ')
}

function DetailItem({ name, bonus, title }: { name: string; bonus?: string; title?: string }) {
  return <div className="neq-npc-details-item"><div><span className="neq-npc-details-name">{name}</span>{title && <p className="ember-npc-description">{title}</p>}</div>{bonus !== undefined && <span className="neq-npc-details-bonus">{bonus}</span>}</div>
}

function DetailBody({ npc, kind }: { npc: Record<string, unknown>; kind: Exclude<NpcModalKind, 'inventory' | 'spells'> }) {
  const t = useT()
  const v = useV()
  if (kind === 'saves') return <>{saveRows(npc).map((save) => <DetailItem key={save.name} name={`${v('ability', save.name)} ${save.proficient ? '●' : '○'}`} bonus={formatModifier(save.bonus)} />)}</>
  if (kind === 'skills') {
    const skills = skillRows(npc)
    return <>{skills.length ? skills.map((skill) => <DetailItem key={skill.name} name={v('skill', skill.name)} bonus={formatModifier(skill.bonus)} />) : <div className="neq-npc-details-item">{t('No skills available.')}</div>}</>
  }
  const raw = kind === 'features' ? npc['classFeatures'] : kind === 'traits' ? npc['racialTraits'] : rec(npc['backgroundFeature']) ? [npc['backgroundFeature']] : []
  const items = arr(raw).map(rec).filter((item): item is Record<string, unknown> => item !== null)
  const empty = kind === 'features' ? t('No key abilities available.') : kind === 'traits' ? t('No racial traits available.') : t('No background available.')
  return <>{items.length ? items.map((item, index) => <DetailItem key={`${str(item['name'])}-${index}`} name={str(item['name'])} bonus={featureUsage(item) || undefined} title={str(item['description'], str(item['detail'])) || undefined} />) : <div className="neq-npc-details-item">{empty}</div>}</>
}

function InventoryBody({ npc }: { npc: Record<string, unknown> }) {
  const t = useT()
  const v = useV()
  const reference = useSpellReference()
  const items = equipmentList(npc)
  if (!items.length) return <div className="neq-npc-inventory-item">{t('No items in inventory.')}</div>
  return <>{items.map((item, index) => <div key={`${item.name}-${index}`} className="neq-npc-inventory-item"><div className="neq-npc-inventory-item-header"><EmberInspection label={item.name}><EquipmentDetails item={item} />{(item.subtype === 'scroll' || /scroll/i.test(item.type)) && <SpellDetails detail={reference.data[spellKey(item.name.replace(/^scroll\s+(of\s+)?/i, ''))]} fallbackName={item.name} />}</EmberInspection><div className="neq-npc-inventory-item-quantity">x{item.quantity}</div></div><div className="neq-npc-inventory-item-details">{v('itemType', item.type)}{item.equipped ? ` · ${t('Equipped')}` : ''}{item.charges ? ` · ${t('{current}/{max} charges', { current: item.charges.current, max: item.charges.max })}` : ''}</div>{item.description && <div className="neq-npc-inventory-item-description">{item.description}</div>}</div>)}</>
}

function SpellsBody({ npc }: { npc: Record<string, unknown> }) {
  const t = useT()
  const v = useV()
  const ember = useEmberDesktop()
  const reference = useSpellReference()
  const casting = spellcastingView(npc)
  if (!casting) return <div className="neq-npc-no-spellcasting">{t('This character does not have spellcasting abilities.')}</div>
  return <div className={`neq-npc-modal-spellcasting${ember ? ' tis-spells' : ''}`}>
    {ember ? <SpellcastingSummary data={npc} casting={casting} /> : (casting.saveDC !== null || casting.attackBonus !== null) && <div className="neq-npc-modal-spell-stats">{casting.saveDC !== null && <span>{t('Save DC: {dc}', { dc: casting.saveDC })}</span>}{casting.attackBonus !== null && <span>{t('Spell Attack: {value}', { value: formatModifier(casting.attackBonus) })}</span>}</div>}
    {reference.status === 'error' && <p role="status">{t('Spell reference unavailable.')} <button type="button" onClick={reference.retry}>{t('Retry')}</button></p>}
    {casting.levels.map((level) => <div key={level.levelIndex} className="neq-npc-modal-spell-level"><div className="neq-npc-modal-spell-header"><span className="neq-npc-modal-spell-name">{v('spellLevel', level.levelName)}</span>{level.slots && <span className={`neq-npc-modal-spell-slots ${slotTone(level.slots)}`}>{t('{current}/{max} slots', { current: level.slots.current, max: level.slots.max })}</span>}</div><div className="neq-npc-modal-spell-list">{level.spells.map((spell) => <div key={spell} className="neq-npc-modal-spell-item"><EmberInspection label={spell}><SpellDetails fallbackName={spell} detail={reference.data[spellKey(spell)]} /></EmberInspection>{casting.prepared.includes(spell) && <span className="ember-npc-prepared">{t('Prepared')}</span>}</div>)}</div></div>)}
  </div>
}

export function NpcDetailContent({ npc, kind }: { npc: Record<string, unknown>; kind: NpcModalKind }) {
  const expanded = kind === 'inventory' || kind === 'spells'
  return <div className={expanded ? 'neq-npc-inventory-body' : 'neq-npc-details-body'}>{kind === 'inventory' ? <InventoryBody npc={npc} /> : kind === 'spells' ? <SpellsBody npc={npc} /> : <DetailBody npc={npc} kind={kind} />}</div>
}

export function NpcDetailModal({ npc, kind, onClose }: { npc: Record<string, unknown>; kind: NpcModalKind; onClose: () => void }) {
  const t = useT()
  const name = str(npc['name'], t('Unknown NPC'))
  const title = t("{name}'s {title}", { name, title: t(TITLES[kind]) })
  const expanded = kind === 'inventory' || kind === 'spells'
  return createPortal(<DialogShell title={title} onClose={onClose} maxWidth={expanded ? '42rem' : '34rem'} className="ember-npc-detail">
      <NpcDetailContent npc={npc} kind={kind} />
  </DialogShell>, document.body)
}
