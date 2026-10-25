import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { DialogShell } from '../dialogs/DialogShell'
import { NpcsTab } from '../sheet/NpcsTab'
import { emitC } from '../../services/socket'
import { useT } from '../../i18n'
import '../../theme/tavern-npc-review.css'
import '../../theme/tavern-player-review.css'

/** Same live character card and nested menus as the NPC tab, not a summary copy. */
export function NpcCardDialog({ name, onClose }: { name: string; onClose: () => void }) {
  const t = useT()
  useEffect(() => { emitC('request_player_data', { dataType: 'npcs' }) }, [name])
  return createPortal(<DialogShell title={t('{name} — Character', { name: name.replace(/_/g, ' ') })} onClose={onClose} maxWidth="1060px" className="ember-npc-full-card ember-sheet-fixed-frame ember-npc-tabbed-card">
    <NpcsTab npcName={name} />
  </DialogShell>, document.body)
}
