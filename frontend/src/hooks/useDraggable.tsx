import { useState, useEffect, useRef } from 'react'

interface Position {
  x: number
  y: number
}

export function useDraggable(initialPosition?: Position) {
  const [position, setPosition] = useState<Position>(
    initialPosition || { x: window.innerWidth / 2 - 300, y: 100 }
  )
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState<Position>({ x: 0, y: 0 })
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return

      const deltaX = e.clientX - dragStart.x
      const deltaY = e.clientY - dragStart.y

      setPosition(prev => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY
      }))

      setDragStart({ x: e.clientX, y: e.clientY })
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      
      // Prevent text selection while dragging
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.userSelect = ''
    }
  }, [isDragging, dragStart])

  const handleMouseDown = (e: React.MouseEvent) => {
    // Only drag from the header - check for either class
    const target = e.target as HTMLElement
    if (target.closest('.modal-header') || target.closest('.draggable-handle')) {
      setIsDragging(true)
      setDragStart({ x: e.clientX, y: e.clientY })
      e.preventDefault()
    }
  }

  return {
    position,
    handleMouseDown,
    isDragging,
    elementRef,
    resetPosition: () => setPosition(initialPosition || { x: window.innerWidth / 2 - 300, y: 100 })
  }
}