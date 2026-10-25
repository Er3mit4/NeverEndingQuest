import { useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { DialogShell } from '../dialogs/DialogShell'
import { CharacterSheet, Portrait } from '../sheet/CharacterSheet'
import { CharacterSheetIdentity } from '../sheet/CharacterSheetIdentity'
import { CharacterSheetTabs, type CharacterSheetTab } from '../sheet/CharacterSheetTabs'
import { str } from '../sheet/characterData'
import { InventoryTab } from '../sheet/InventoryTab'
import { SpellsTab } from '../sheet/SpellsTab'
import { InventoryViewProvider } from '../sheet/InventoryViewState'
import { useTabDataPolling } from '../sheet/sheetRequests'
import { usePlayer } from '../../stores'
import { matchingNpc } from './partyData'
import { useT } from '../../i18n'
import '../../theme/tavern-npc-review.css'
import '../../theme/tavern-player-review.css'


/** Read the authoritative player stores, never treat a roster summary as a sheet. */
export function PlayerCardDialog({ name, onClose }: { name: string; onClose: () => void }) {
  const t = useT()
  const [active, setActive] = useState<CharacterSheetTab>('character')
  const id = useId()
  const stats = usePlayer(state => state.stats)
  const panel = useRef<HTMLDivElement>(null)
  useLayoutEffect(() => { if (panel.current) panel.current.scrollTop = 0 }, [active])
  const wrongPlayer = stats && !matchingNpc([stats], name)
  useTabDataPolling(active)
  return createPortal(<DialogShell title={t('{name} — Your character', { name: name.replace(/_/g, ' ') })} onClose={onClose} maxWidth="1060px" className="ember-npc-full-card ember-player-full-card ember-sheet-fixed-frame">
    <InventoryViewProvider>
      {stats && !wrongPlayer && <CharacterSheetIdentity stats={stats} portrait={<Portrait key={str(stats['name'])} name={str(stats['name'])} />} />}
      <CharacterSheetTabs id={id} active={active} onChange={setActive} label={t('Player character')} />
      <div ref={panel} className="tps-panel" role="tabpanel" tabIndex={0} id={`${id}-panel`} aria-labelledby={`${id}-${active}`}>
        {wrongPlayer ? <p role="status">{t('This character is no longer the active player.')}</p> : active === 'character' ? <CharacterSheet expanded hideIdentity /> : active === 'inventory' ? <InventoryTab expanded /> : <SpellsTab expanded />}
      </div>
    </InventoryViewProvider>
  </DialogShell>, document.body)
}
