interface Props {
  href?: string
  label?: string
  disabled?: boolean
}

export function DownloadButton({ href, label = 'Download CSV', disabled = false }: Props) {
  if (disabled || !href) {
    return (
      <button
        disabled
        className="px-4 py-2 bg-gray-100 text-gray-400 rounded-lg text-sm font-medium cursor-not-allowed"
        data-testid="download-button"
      >
        {label}
      </button>
    )
  }

  return (
    <a
      href={href}
      download
      className="inline-flex items-center px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800 transition-colors"
      data-testid="download-button"
    >
      {label}
    </a>
  )
}
