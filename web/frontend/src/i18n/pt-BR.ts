import { common } from './fragments/common'
import { dialogs } from './fragments/dialogs'
import { layout } from './fragments/layout'
import { log } from './fragments/log'
import { party } from './fragments/party'
import { settings } from './fragments/settings'
import { sheet } from './fragments/sheet'
import { sheetNpcs } from './fragments/sheetNpcs'

/**
 * Brazilian Portuguese dictionary.
 *
 * The key is the exact English string rendered by the source UI; the value is
 * its pt-BR translation. New UI text must be added here, which keeps
 * `MessageKey` honest: a `t()` call only type-checks for a known key.
 */
export const ptBR = {
  ...common,
  ...layout,
  ...log,
  ...dialogs,
  ...settings,
  ...sheet,
  ...sheetNpcs,
  ...party,
}
