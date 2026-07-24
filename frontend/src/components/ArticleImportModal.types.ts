export interface AuthSite {
  key: string
  name: string
  login_url: string
  has_session: boolean
  session_info?: {
    created_at?: string
    last_used?: string
    cookie_count?: number
    is_valid?: boolean
  }
}

export interface ArticleImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess: () => void
}
