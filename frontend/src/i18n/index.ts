import en from './en.json';
import sw from './sw.json';
import ha from './ha.json';
import tw from './tw.json';
import zu from './zu.json';
import am from './am.json';
import st from './st.json';
import rw from './rw.json';
import fulani from './fulani.json';

const translations: any = { en, sw, ha, tw, zu, am, st, rw, ff: fulani };

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
const interpolate = (value: string, params?: Record<string, string | number>): string => {
  if (!params) return value;
  return Object.entries(params).reduce((result, [paramKey, paramValue]) => {
    return result.replace(new RegExp(`\{${paramKey}\}`, 'g'), String(paramValue));
  }, value);
};

export const translate = (
  language: string,
  key: string,
  params?: Record<string, string | number>,
  fallbackLanguage = 'en'
): string => {
  // Try selected language
  let value = getNestedValue(translations[language], key);
  
  // Fallback to English
  if (value === null && language !== fallbackLanguage) {
    value = getNestedValue(translations[fallbackLanguage], key);
  }
  
  if (typeof value === 'string') {
    return interpolate(value, params);
  }
  
  // Final fallback: return the key itself
  return value !== null ? String(value) : key;
};

export default translations;
