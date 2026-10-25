import { useEffect } from 'react'
import { useConnectionNotice, CREATION_CANCELLED } from '../../stores/connectionNotices'
import { useT, type MessageKey } from '../../i18n'

/**
 * The transport notices the client itself writes. Server messages are shown
 * verbatim; only these four known strings are translated.
 */
const NOTICE_KEYS: Record<string, MessageKey> = {
  [CREATION_CANCELLED]: 'Character creation was cancelled. Choose an adventure to start again.',
  'Disconnected from the game server. Reconnecting...': 'Disconnected from the game server. Reconnecting...',
  'Reconnected to your character setup.': 'Reconnected to your character setup.',
  'Reconnected to your game in progress.': 'Reconnected to your game in progress.',
}

/** Transport notices are temporary UI, never campaign history. */
export function ConnectionNotice() {
  const t = useT()
  const { text, revision, clear } = useConnectionNotice()
  useEffect(() => {
    if (!text) return
    const timer = window.setTimeout(clear, 8000)
    return () => window.clearTimeout(timer)
  }, [text, revision, clear])
  if (!text) return null
  const key = NOTICE_KEYS[text]
  return <div role="status" style={{ position: 'fixed', top: 'max(8px, env(safe-area-inset-top))', left: '50%', transform: 'translateX(-50%)', width: 'min(90vw, 480px)', zIndex: 10000, display: 'flex', alignItems: 'center', gap: 12, padding: 12, border: '1px solid #a98c59', borderRadius: 8, background: '#252118', color: '#f4e1be', fontSize: 15, boxShadow: '0 4px 18px #0008' }}>
    <span style={{ flex: 1 }}>{key ? t(key) : text}</span><button type="button" aria-label={t('Dismiss notification')} onClick={clear} style={{ minWidth: 44, minHeight: 44 }}>×</button>
  </div>
}
