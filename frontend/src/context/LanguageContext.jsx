import React, { createContext, useState, useEffect, useContext } from 'react';
import translations from '../i18n';

const LanguageContext = createContext();

const countryToLanguageMap = {
  'NG': 'ha',  // Nigeria -> Hausa
  'KE': 'sw',  // Kenya -> Swahili
  'TZ': 'sw',  // Tanzania -> Swahili
  'GH': 'tw',  // Ghana -> Twi
  'ZA': 'zu',  // South Africa -> Zulu
  'LS': 'st',  // Lesotho -> Sesotho
  'ET': 'am',  // Ethiopia -> Amharic
  'US': 'en',  // USA -> English
  'GB': 'en',  // UK -> English
  'DEFAULT': 'en'
};

export const LanguageProvider = ({ children }) => {
  // Get saved language from localStorage or default to English
  const [language, setLanguage] = useState(() => {
    const saved = localStorage.getItem('app-language');
    return saved && translations[saved] ? saved : 'en';
  });

  // t() function to get translation by key
  const t = (key) => {
    try {
      // Split key by dots: "enroll.title" -> ['enroll', 'title']
      const keys = key.split('.');
      let value = translations[language];
      
      // Navigate through nested object
      for (const k of keys) {
        if (value && value[k]) {
          value = value[k];
        } else {
          // Fallback to English if translation missing
          let fallback = translations.en;
          for (const fk of keys) {
            fallback = fallback?.[fk];
          }
          return fallback || key;
        }
      }
      return value;
    } catch (error) {
      console.error(`Translation error for key: ${key}`, error);
      return key;
    }
  };

  const changeLanguage = (newLanguage) => {
    if (translations[newLanguage]) {
      setLanguage(newLanguage);
      localStorage.setItem('app-language', newLanguage);
    }
  };

  const autoDetectLanguage = (countryCode) => {
    const detected = countryToLanguageMap[countryCode] || countryToLanguageMap.DEFAULT;
    if (detected !== language) {
      changeLanguage(detected);
      return true;
    }
    return false;
  };

  const availableLanguages = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'sw', name: 'Kiswahili', flag: '🇰🇪' },
    { code: 'ha', name: 'Hausa', flag: '🇳🇬' },
    { code: 'tw', name: 'Twi', flag: '🇬🇭' },
    { code: 'zu', name: 'isiZulu', flag: '🇿🇦' },
    { code: 'st', name: 'Sesotho', flag: '🇱🇸' },
    { code: 'am', name: 'አማርኛ', flag: '🇪🇹' }
  ];

  return (
    <LanguageContext.Provider value={{
      language,
      t,
      setLanguage: changeLanguage,
      autoDetectLanguage,
      availableLanguages
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
