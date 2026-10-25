import type { ServerEvents } from '../../contract/events'
import { formatNumber, t, tn } from '../../i18n'

/** #1388: the session cost line's text, shared by the header and Settings. */
export type Spend = NonNullable<ServerEvents['token_update']['spend']>

/** The approved disclaimer (#1388), verbatim; <priced_at> is the catalog's list-price date. */
export function spendDisclaimer(pricedAt: string): string {
  return t('Estimate only: worked out from the token usage OpenAI reports with each response, at OpenAI\'s list prices dated {pricedAt}. Your OpenAI bill is the authority.', { pricedAt })
}

function dollars(usd: number): string {
  return usd < 0.01
    ? t('under $0.01')
    : t('about ${amount}', { amount: usd.toFixed(2) })
}

/** The header text for one spend snapshot. */
export function spendLineText(spend: Spend): string {
  if (!spend.available) return t('This session: estimate unavailable')
  const calls = spend.calls === 1
    ? t('This session: {calls} AI call', { calls: formatNumber(spend.calls) })
    : t('This session: {calls} AI calls', { calls: formatNumber(spend.calls) })
  if (spend.provider_kind === 'local') return t('{calls}, local model', { calls })
  if (spend.provider_kind !== 'openai') return calls
  const other = spend.portraits + spend.voice > 0 ? t('; images and voice not included') : ''
  return t('{calls}, {amount} for AI text{other}', { calls, amount: dollars(spend.usd), other })
}

/** The hover breakdown: this turn, tokens, the unpriced counts, billed retries, the disclaimer. */
export function spendHoverText(spend: Spend): string {
  const turn = spend.turn_calls === 1
    ? t('This turn: {calls} AI call', { calls: formatNumber(spend.turn_calls) })
    : t('This turn: {calls} AI calls', { calls: formatNumber(spend.turn_calls) })
  const lines = [
    spend.provider_kind === 'openai'
      ? t('{turn}, {amount}', { turn, amount: dollars(spend.turn_usd) })
      : turn,
    t('Tokens: {prompt} in ({cached} cached), {completion} out', {
      prompt: formatNumber(spend.prompt),
      cached: formatNumber(spend.cached),
      completion: formatNumber(spend.completion),
    }),
  ]
  if (spend.portraits + spend.voice > 0) lines.push(t('Images: {portraits}, voice clips: {voice} (not priced)', { portraits: formatNumber(spend.portraits), voice: formatNumber(spend.voice) }))
  if (spend.possibly_billed > 0) lines.push(tn('{count} retry that failed part-way may also have been billed.', '{count} retries that failed part-way may also have been billed.', spend.possibly_billed, { count: formatNumber(spend.possibly_billed) }))
  if (spend.provider_kind === 'openai') lines.push(spendDisclaimer(spend.priced_at))
  return lines.join('\n')
}
