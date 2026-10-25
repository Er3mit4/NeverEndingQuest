import type { EquipmentItem } from './characterData'
import { useT, useV } from '../../i18n'

export function EquipmentDetails({ item }: { item: EquipmentItem }) {
  const t = useT()
  const v = useV()
  return <><dl>
    <dt>{t('Type')}</dt><dd>{v('itemType', item.type)}</dd>
    {item.subtype && <><dt>{t('Subtype')}</dt><dd>{v('itemSubtype', item.subtype)}</dd></>}
    {item.spellLevel !== null && <><dt>{t('Spell level')}</dt><dd>{item.spellLevel === 0 ? v('spellLevel', 'Cantrip') : item.spellLevel}</dd></>}
    <dt>{t('Quantity')}</dt><dd>{item.quantity}</dd>
    {item.equipped && <><dt>{t('Equipment')}</dt><dd>{t('Equipped')}</dd></>}
    {item.magical && <><dt>{t('Magic')}</dt><dd>{t('Magical item')}</dd></>}
    {item.consumable && <><dt>{t('Use')}</dt><dd>{t('Consumable')}</dd></>}
    {item.charges && <><dt>{t('Charges')}</dt><dd>{item.charges.current} / {item.charges.max}</dd></>}
  </dl><p>{item.description || t('No description available.')}</p></>
}
