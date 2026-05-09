import en from './en.json';
import sw from './sw.json';
import ha from './ha.json';
import tw from './tw.json';
import zu from './zu.json';
import am from './am.json';
import st from './st.json';
import rw from './rw.json';

const translations = {
  en,
  sw,
  ha,
  tw,
  zu,
  am,
  st,
  rw
};

// Helper function to get nested value
export const getNestedValue = (obj, path) => {
  return path.split('.').reduce((current, key) => {
    return current?.[key] ?? null;
  }, obj);
};

export const translate = (language, key, fallbackLanguage = 'en') => {
  // Try selected language first
  let value = getNestedValue(translations[language], key);
  
  // Fallback to English if not found
  if (value === null && language !== fallbackLanguage) {
    value = getNestedValue(translations[fallbackLanguage], key);
  }
  
  // Final fallback: return the key
  return value !== null ? value : key;
};

export default translations;
