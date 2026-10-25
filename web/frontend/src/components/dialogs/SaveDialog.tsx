import { useRef, useState } from 'react'
import { emitC } from '../../services/socket'
import { useDialogs, useSession } from '../../stores'
import { useT, type MessageKey } from '../../i18n'
import { DialogShell, dialogButtonPrimary, dialogButtonSecondary } from './DialogShell'
import { useEmberViewport } from '../layout/useEmberViewport'
import { EmberIcon } from '../layout/EmberIcon'

type SaveMode = 'essential' | 'full'

interface ModeInfo {
  title: MessageKey
  badge: MessageKey
  includes: MessageKey[]
  note: MessageKey
}

const MODE_INFO: Record<SaveMode, ModeInfo> = {
  essential: {
    title: 'Game State Save',
    badge: 'RECOMMENDED',
    includes: [
      'Character progress and inventory',
      'Story progress and quest states',
      'Party location and module data',
      'All conversation history',
      'Active encounters and game state',
    ],
    note: 'Perfect for regular gameplay saves. Faster and smaller file size.',
  },
  full: {
    title: 'Archive Edition Save',
    badge: 'COMPLETE ARCHIVE',
    includes: [
      'Extended conversation archives',
      'Detailed combat logs and analysis',
      'Campaign transition summaries',
      'Multi-AI conversation tracking',
      'Historical data for review',
    ],
    note: 'Ideal for DMs, campaign analysis, or long-term archival. Larger file size.',
  },
}

/** Body unmounts when the dialog closes, so each open starts with a fresh form. */
function SaveDialogBody() {
  const ember = useEmberViewport()
  const t = useT()
  const [description, setDescription] = useState('')
  const [saveMode, setSaveMode] = useState<SaveMode>('essential')
  const descriptionRef = useRef<HTMLTextAreaElement>(null)
  const closeDialog = useDialogs((s) => s.closeDialog)
  const connected = useSession((s) => s.connected)
  const submitted = useRef(false)

  const performSave = () => {
    // Socket.IO buffers disconnected writes. Keep the draft open instead of
    // scheduling a save against whichever campaign reconnects later.
    if (submitted.current || !useSession.getState().connected) return
    submitted.current = true
    emitC('action', {
      action: 'saveGame',
      parameters: { description: description.trim(), saveMode },
    })
    closeDialog()
  }

  const info = MODE_INFO[saveMode]

  return (
    <DialogShell title={t('Save Game')} onClose={closeDialog} maxWidth="600px" legacy className="neq-enhanced-save-dialog-parity" initialFocusRef={descriptionRef}>
      <div>
        <div className="neq-save-form-parity">
          <label htmlFor="save-description">
            {t('Description (optional):')}
          </label>
          <textarea
            ref={descriptionRef}
            id="save-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={t('Enter a brief description of your current progress...')}
            rows={2}
          />

          <label htmlFor="save-mode">
            {t('Save Type:')}
          </label>
          <div className="neq-save-mode-container-parity">
            <select
              id="save-mode"
              value={saveMode}
              onChange={(e) => setSaveMode(e.target.value as SaveMode)}
            >
              <option value="essential">{t('Game State - Complete Save (Recommended)')}</option>
              <option value="full">{t('Archive Edition - Includes Historical Data')}</option>
            </select>

            <div className="neq-save-mode-info-parity">
              <div className="neq-save-mode-title-parity">
                <span className="neq-save-icon-parity" aria-hidden="true">{ember ? <EmberIcon name="book" /> : saveMode === 'essential' ? '💾' : '📚'}</span>
                <strong>{t(info.title)}</strong>
                <span className={`neq-save-badge-parity ${saveMode}`}>
                  {t(info.badge)}
                </span>
              </div>
              <div className="neq-save-description-parity">
                {saveMode === 'essential' ? t('Complete game restoration with all essential data:') : t('Everything from Game State Save plus:')}
                <ul>
                  {info.includes.map((line, index) => (
                    <li key={line}>{`${ember ? '•' : saveMode === 'essential' ? '✅' : ['📜', '⚔️', '🗃️', '🤖', '📊'][index]} ${t(line)}`}</li>
                  ))}
                </ul>
                <div className="neq-save-note-parity">{t(info.note)}</div>
              </div>
            </div>
          </div>
        </div>

        {!connected && <p role="status">{t('Disconnected. Your draft is kept here; reconnect before saving.')}</p>}
        <div className="neq-dialog-buttons-parity">
          <button type="button" className={dialogButtonSecondary} onClick={closeDialog}>
            {t('Cancel')}
          </button>
          <button type="button" aria-label={t('Save Game')} className={dialogButtonPrimary} onClick={performSave} disabled={!connected}>
            {!ember && <span className="neq-button-icon-parity">💾</span>} {t('Save Game')}
          </button>
        </div>
      </div>
    </DialogShell>
  )
}

/** Save Game dialog: emits action saveGame with description + saveMode (plan 4.4e). */
export function SaveDialog() {
  const open = useDialogs((s) => s.open)
  if (open !== 'save') return null
  return <SaveDialogBody />
}
