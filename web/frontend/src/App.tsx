import { useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { applyDocumentLocale, useLocale } from './stores/locale'

function App() {
  const locale = useLocale((s) => s.locale)
  // Keep <html lang> in step with the UI language for screen readers,
  // hyphenation and browser spell-check.
  useEffect(() => { applyDocumentLocale(locale) }, [locale])
  return <AppShell />
}

export default App
