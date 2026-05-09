import React, { createContext, useState, useEffect, useContext, useCallback, useMemo } from 'react';
import translations, { translate } from '../i18n';

const LanguageContext = createContext<any>(null);

const countryToLanguageMap: Record<string, string> = {
  'NG': 'ha', 'KE': 'sw', 'TZ': 'sw', 'GH': 'tw',
  'ZA': 'zu', 'LS': 'st', 'ET': 'am', 'RW': 'rw', 'US': 'en',
  'GB': 'en', 'DEFAULT': 'en'
};

export const LanguageProvider = ({ children }: { children: React.ReactNode }) => {
  const [language, setLanguage] = useState(() => {
    try {
      const saved = localStorage.getItem('app-language');
      return saved && (translations as any)[saved] ? saved : 'en';
    } catch (error) {
      console.error('Failed to read localStorage:', error);
      return 'en';
    }
  });

  // Memoized translation function
  const t = useCallback((key: string) => {
    return translate(language, key);
  }, [language]);

  // Memoized changeLanguage function
  const changeLanguage = useCallback((newLanguage: string) => {
    if ((translations as any)[newLanguage]) {
      setLanguage(newLanguage);
      try {
        localStorage.setItem('app-language', newLanguage);
      } catch (error) {
        console.error('Failed to save to localStorage:', error);
      }
    }
  }, []);

  const autoDetectLanguage = useCallback((countryCode: string) => {
    const detected = countryToLanguageMap[countryCode] || countryToLanguageMap.DEFAULT;
    if (detected !== language) {
      changeLanguage(detected);
      return true;
    }
    return false;
  }, [language, changeLanguage]);

  const availableLanguages = useMemo(() => [
    { code: 'en', name: 'English', flag: '🇬🇧', nativeName: 'English' },
    { code: 'sw', name: 'Kiswahili', flag: '🇰🇪', nativeName: 'Kiswahili' },
    { code: 'ha', name: 'Hausa', flag: '🇳🇬', nativeName: 'Hausa' },
    { code: 'ff', name: 'Fulani', flag: '🌍', nativeName: 'Fulfulde' },
    { code: 'tw', name: 'Twi', flag: '🇬🇭', nativeName: 'Twi' },
    { code: 'zu', name: 'isiZulu', flag: '🇿🇦', nativeName: 'isiZulu' },
    { code: 'st', name: 'Sesotho', flag: '🇱🇸', nativeName: 'Sesotho' },
    { code: 'rw', name: 'Kinyarwanda', flag: '🇷🇼', nativeName: 'Kinyarwanda' },
    { code: 'am', name: 'አማርኛ', flag: '🇪🇹', nativeName: 'አማርኛ' }
  ], []);

  const value = useMemo(() => ({
    language,
    t,
    setLanguage: changeLanguage,
    autoDetectLanguage,
    availableLanguages
  }), [language, t, changeLanguage, autoDetectLanguage, availableLanguages]);

  return (
    <LanguageContext.Provider value={value}>
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
