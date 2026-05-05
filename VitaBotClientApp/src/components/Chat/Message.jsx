import styles from './Message.module.css'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useState } from 'react'

function CodeRenderer({ inline, className, children, ...props }) {
  const [copied, setCopied] = useState(false)

  if (inline) {
    return (
      <code className={styles.inlineCode} {...props}>
        {children}
      </code>
    )
  }

  const copyToClipboard = async () => {
    try {
      const text = String(children).replace(/\n$/, '')
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        textArea.remove()
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Error al copiar:', err)
    }
  }

  return (
    <div className={styles.codeWrapper}>
      <button
        className={styles.copyButton}
        onClick={copyToClipboard}
        title={copied ? 'Copiado!' : 'Copiar código'}
      >
        {copied ? '✓' : 'Copiar'}
      </button>
      <pre className={styles.codeBlock}>
        <code className={className || ''} {...props}>
          {children}
        </code>
      </pre>
    </div>
  )
}

export default function Message({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`${styles.message} ${isUser ? styles.user : styles.ai}`}>
      {/*
      <div className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarAi}`}
           aria-hidden>
        {isUser ? 'Tú' : 'AI'}
      </div>
      */}
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${message.isError ? styles.error : ''}`}>
        {isUser ? (
          message.content
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: CodeRenderer }}>
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  )
}