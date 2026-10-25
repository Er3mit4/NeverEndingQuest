// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { InputBar } from '../components/log/InputBar'
import { ConnectionNotice } from '../components/layout/ConnectionNotice'
import { useConnectionNotice, CREATION_CANCELLED } from '../stores/connectionNotices'
import { useSession } from '../stores'
import { useLocale } from '../stores/locale'

afterEach(() => {
  cleanup()
  useLocale.getState().setLocale('en')
  useConnectionNotice.getState().clear()
  useSession.setState({ connected: false, mode: 'disconnected', isProcessing: false })
})

describe('pt-BR player chrome', () => {
  it('renders the command bar in Portuguese', () => {
    useLocale.getState().setLocale('pt-BR')
    render(<InputBar />)
    expect(screen.getByPlaceholderText('Digite seu comando...')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Enviar' })).toBeTruthy()
  })

  it('translates the client connection notices and keeps server text verbatim', () => {
    useLocale.getState().setLocale('pt-BR')
    useConnectionNotice.getState().show(CREATION_CANCELLED)
    const { unmount } = render(<ConnectionNotice />)
    expect(screen.getByText('A criação de personagem foi cancelada. Escolha uma aventura para começar de novo.')).toBeTruthy()
    unmount()

    useConnectionNotice.getState().show('Provider refused the key (401).')
    render(<ConnectionNotice />)
    expect(screen.getByText('Provider refused the key (401).')).toBeTruthy()
  })

  it('keeps the command bar in English by default', () => {
    render(<InputBar />)
    expect(screen.getByPlaceholderText('Enter your command...')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Send' })).toBeTruthy()
  })
})
