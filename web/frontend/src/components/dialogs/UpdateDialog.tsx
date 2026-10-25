import { useEffect, useRef, useState } from 'react'
import { emitC } from '../../services/socket'
import { prepareForServerRestart, reloadWhenServerReady } from '../../services/restart'
import { useDialogs, useSession } from '../../stores'
import { DialogShell, dialogButtonPrimary, dialogButtonSecondary } from './DialogShell'
import { useEmberViewport } from '../layout/useEmberViewport'
import { useT } from '../../i18n'

function UpdateDialogBody() {
  const ember = useEmberViewport()
  const t = useT()
  const version = useSession((s) => s.version)
  const update = useDialogs((s) => s.update)
  const closeDialog = useDialogs((s) => s.closeDialog)
  const connected = useSession((s) => s.connected)
  const [preparing, setPreparing] = useState(false)
  const generation = useRef(0)
  const busy = useRef(false)
  useEffect(() => {
    if (!connected || update.running) {
      generation.current++
      busy.current = false
      setPreparing(false)
    }
    return () => { generation.current++; busy.current = false }
  }, [connected, update.running])
  const requestClose = () => {
    generation.current++
    closeDialog()
  }
  useEffect(() => { if (update.complete) void reloadWhenServerReady() }, [update.complete])
  const proceed = async () => {
    if (busy.current || useDialogs.getState().update.running || !useSession.getState().connected) return
    const attempt = ++generation.current
    const isCurrent = () => attempt === generation.current && useSession.getState().connected
      && useDialogs.getState().open === 'update' && !useDialogs.getState().update.running
    busy.current = true
    setPreparing(true)
    try {
      await prepareForServerRestart(isCurrent)
      if (!isCurrent()) return
      useDialogs.getState().updateStarted()
      emitC('trigger_update', undefined)
    } catch (error) {
      if (!isCurrent()) return
      const reason = error instanceof Error ? error.message : String(error)
      useDialogs.getState().updateError({
        error: t('Update could not start: {error}', { error: reason }),
      })
      busy.current = false
      setPreparing(false)
    }
  }
  const currentStatus = preparing ? t('Preparing server restart...') : update.complete
    ? t('{message} Please refresh the page.', { message: update.complete })
    : update.error
      ? t('Update failed: {error}', { error: update.error })
      : update.log.at(-1) ?? null
  return <DialogShell title={ember ? t('Update Available') : `🔄 ${t('Update Available')}`} onClose={requestClose} maxWidth="700px" legacy>
    <div className="neq-update-content-parity">
      <p>{version ? t('A new version is available: v{local} -> v{remote}', { local: version.local_version, remote: version.remote_version }) : t('A new version is available!')}</p>
      <div className="neq-reset-warning-box-parity"><strong>{!ember && '⚠️ '}{t('Backup Recommended')}</strong><p>{t('Before updating, we recommend backing up your saved games and any custom modules.')}</p></div>
      {!connected && <p role="status">{t('Disconnected. Reconnect before starting an update.')}</p>}
      <div className="neq-dialog-buttons-parity"><button type="button" className={dialogButtonPrimary} disabled={!connected || preparing || (ember && update.running)} onClick={() => void proceed()}>{t('Proceed with Update')}</button><button type="button" className={dialogButtonSecondary} onClick={requestClose}>{t('Cancel')}</button></div>
      {currentStatus && <div className="neq-update-progress-parity"><p role="status">{currentStatus}</p></div>}
    </div>
  </DialogShell>
}

export function UpdateDialog() { const open = useDialogs((s) => s.open); return open === 'update' ? <UpdateDialogBody /> : null }
