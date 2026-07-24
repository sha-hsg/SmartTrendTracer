import { Sun, Moon, Monitor } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { Button } from '@/components/ui/button'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const cycle = () => {
    const next = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'
    setTheme(next)
  }

  const icon = theme === 'light' ? <Sun className="h-4 w-4" />
    : theme === 'dark' ? <Moon className="h-4 w-4" />
    : <Monitor className="h-4 w-4" />

  const label = theme === 'light' ? 'Light' : theme === 'dark' ? 'Dark' : 'System'

  return (
    <Button variant="ghost" size="icon" className="h-9 w-9" onClick={cycle} title={`Theme: ${label}`}>
      {icon}
      <span className="sr-only">Toggle theme ({label})</span>
    </Button>
  )
}
