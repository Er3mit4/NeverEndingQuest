import type { Currency } from './characterData'
import { useV } from '../../i18n'

export function EmberCurrency({ currency }: { currency: Currency }) {
  const v = useV()
  return <div className="ember-currency-row">{([['GP', currency.gold], ['SP', currency.silver], ['CP', currency.copper]] as const).map(([label, value]) => <div key={label} className="neq-currency"><span className={`ember-coin ember-coin-${label}`} aria-hidden="true" /><span>{v('coin', label)}</span> {value}</div>)}</div>
}
