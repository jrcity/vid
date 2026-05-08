import en from './en.json';
import sw from './sw.json';
import ha from './ha.json';
import tw from './tw.json';
import zu from './zu.json';
import am from './am.json';
import st from './st.json';

const translations: any = { en, sw, ha, tw, zu, am, st };

/**
 * Helper to get nested values from an object using a dot-notation key (e.g. "common.save")
 */
export const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((current, key) => {
    return current?.[key] ?? null;
  }, obj);
};

/**
 * Core translation function
 */
export const translate = (language: string, key: string, fallbackLanguage = 'en'): string => {
  // Try selected language
  let value = getNestedValue(translations[language], key);
  
  // Fallback to English
  if (value === null && language !== fallbackLanguage) {
    value = getNestedValue(translations[fallbackLanguage], key);
  }
  
  // Final fallback: return the key itself
  return value !== null ? value : key;
};

export default translations;