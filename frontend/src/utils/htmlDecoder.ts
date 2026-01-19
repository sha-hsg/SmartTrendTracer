/**
 * Utility to decode HTML entities in text
 */

/**
 * Decodes HTML entities like &amp;, &lt;, &gt;, &quot;, &#39; etc.
 * @param text - The text containing HTML entities
 * @returns The decoded text
 */
export function decodeHtmlEntities(text: string): string {
  if (!text) return text
  
  // Create a temporary textarea element to decode HTML entities
  const textarea = document.createElement('textarea')
  textarea.innerHTML = text
  const decoded = textarea.value
  
  // Additional replacements for common entities that might not be handled
  return decoded
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x27;/g, "'")
    .replace(/&#x2F;/g, '/')
    .replace(/&nbsp;/g, ' ')
}

/**
 * Decodes HTML entities recursively in an object
 * @param obj - The object containing strings with HTML entities
 * @returns The object with decoded strings
 */
export function decodeHtmlEntitiesInObject<T>(obj: T): T {
  if (typeof obj === 'string') {
    return decodeHtmlEntities(obj) as T
  }
  
  if (Array.isArray(obj)) {
    return obj.map(item => decodeHtmlEntitiesInObject(item)) as T
  }
  
  if (obj !== null && typeof obj === 'object') {
    const decoded: any = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        decoded[key] = decodeHtmlEntitiesInObject(obj[key])
      }
    }
    return decoded as T
  }
  
  return obj
}