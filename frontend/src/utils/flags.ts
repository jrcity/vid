/**
 * Converts an ISO 3166-1 alpha-2 country code to an emoji flag.
 * 
 * @param isoCode The two-letter country code (e.g., "NG", "KE")
 * @returns The emoji flag character or a globe if unknown
 */
export const getEmojiFlag = (isoCode: string): string => {
  if (!isoCode || isoCode === 'UNKNOWN') return '🌍'
  
  const codePoints = isoCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0))
  
  return String.fromCodePoint(...codePoints)
}
