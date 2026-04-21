import { useRef, useCallback } from 'react'
import SendButton from '../Chat/SendButton'
import { useAutoResize } from '../../hooks/useAutoResize'
import styles from './InputArea.module.css'

export default function InputArea({ onSend, disabled }) {
  const textareaRef = useRef(null)
  const resize = useAutoResize(140)

  const handleSend = useCallback(() => {
    const value = textareaRef.current?.value.trim()
    if (!value || disabled) return
    onSend(value)
    textareaRef.current.value = ''
    resize(textareaRef.current)
    textareaRef.current.focus()
  }, [onSend, disabled, resize])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleInput = useCallback((e) => {
    resize(e.target)
  }, [resize])

  return (
    <div className={styles.area}>
      <div className={styles.wrapper}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Escribe un mensaje…"
          rows={1}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          aria-label="Mensaje"
        />
        <SendButton onClick={handleSend} disabled={disabled} />
      </div>
      <p className={styles.hint} aria-hidden>
        ↵ Enviar · shift+↵ Nueva línea
      </p>
    </div>
  )
}