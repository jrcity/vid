import en from './en.json';
import sw from './sw.json';
import ha from './ha.json';
import tw from './tw.json';
import zu from './zu.json';
import st from './st.json';
import am from './am.json';

const translations = {
  en,
  sw,
  ha,
  tw,
  zu,
  st,
  am
};

export const getNestedValue = (obj, path) => {
  return path.split('.').reduce((current, key) => {
    return current?.[key] ?? null;
  }, obj);
};

export const translate = (language, key, fallbackLanguage = 'en') => {
  let value = getNestedValue(translations[language], key);
  
  if (value === null && language !== fallbackLanguage) {
    value = getNestedValue(translations[fallbackLanguage], key);
  }
  
  return value !== null ? value : key;
};

export default translations;
