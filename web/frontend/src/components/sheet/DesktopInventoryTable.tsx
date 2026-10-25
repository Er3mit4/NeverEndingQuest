import { EmberInspection } from './EmberInspection'
import { EquipmentDetails } from './EquipmentDetails'
import { SpellDetails } from './spellDetails'
import { spellKey } from './spellKey'
import { useSpellReference } from './useSpellReference'
import type { EquipmentItem } from './characterData'
import { useT, useV } from '../../i18n'
import '../../theme/tavern-inventory-spells.css'

export function DesktopInventoryTable({ items, empty }: { items: EquipmentItem[]; empty?: string }) {
  const t = useT()
  const v = useV()
  const reference = useSpellReference()
  if (!items.length) return <p role="status">{empty ?? t('No items in inventory.')}</p>
  return <div className="tis-inventory-table-wrap"><table className="tis-inventory-table" aria-label={t('Inventory items')}>
    <thead><tr><th scope="col">{t('Item')}</th><th scope="col">{t('Type')}</th><th scope="col">{t('Qty')}</th><th scope="col">{t('Status')}</th><th scope="col">{t('Charges')}</th></tr></thead>
    <tbody>{items.map((item, index) => <tr key={`${item.name}-${index}`}>
      <td><EmberInspection label={item.name}><EquipmentDetails item={item} />{(item.subtype.toLowerCase() === 'scroll' || /scroll/i.test(item.type)) && <SpellDetails detail={reference.data[spellKey(item.name.replace(/^scroll\s+(of\s+)?/i, ''))]} fallbackName={item.name} />}</EmberInspection>{item.description && <span className="tis-item-description">{item.description}</span>}</td>
      <td>{v('itemType', item.type)}</td><td className="tis-quantity">×{item.quantity}</td><td><span className={item.equipped ? 'tis-equipped' : 'tis-carried'}>{item.equipped ? t('Equipped') : t('Carried')}</span></td><td className="tis-charges">{item.charges ? `${item.charges.current}/${item.charges.max}` : '—'}</td>
    </tr>)}</tbody>
  </table></div>
}
