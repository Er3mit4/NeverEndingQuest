import { useState } from 'react'
import { DesktopInventoryTable } from './DesktopInventoryTable'
import { equipmentList, filterEquipment, sortEquipment, type InventorySort } from './characterData'
import { useT } from '../../i18n'

export function NpcInventoryPanel({ npc }: { npc: Record<string, unknown> }) {
  const t = useT()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState<InventorySort>('name-asc')
  const items = equipmentList(npc)
  const categories = [...new Set(items.map(item => item.type))].sort()
  const visible = sortEquipment(filterEquipment(items, query).filter(item => category === 'equipped' ? item.equipped : !category || item.type === category), sort)
  return <section className="tis-inventory" aria-label={t('NPC inventory')}>
    <div className="tis-inventory-toolbar">
      <input aria-label={t('Search NPC inventory')} placeholder={t('Find an item…')} value={query} onChange={event => setQuery(event.target.value)} />
      <select aria-label={t('Filter NPC inventory')} value={category} onChange={event => setCategory(event.target.value)}><option value="">{t('All items')}</option><option value="equipped">{t('Equipped')}</option>{categories.map(type => <option key={type} value={type}>{type}</option>)}</select>
      <select aria-label={t('Sort NPC inventory')} value={sort} onChange={event => setSort(event.target.value as InventorySort)}><option value="name-asc">{t('Name A–Z')}</option><option value="type">{t('Type')}</option><option value="quantity">{t('Quantity')}</option></select>
      <span className="tis-item-count">{t('{shown} / {total} entries', { shown: visible.length, total: items.length })}</span>
    </div>
    <DesktopInventoryTable items={visible} empty={items.length ? t('No items match the filter.') : t('No items in inventory.')} />
  </section>
}
