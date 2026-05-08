import { useLanguage } from '../context/LanguageContext';

/**
 * Hook to use translations in components
 */
const useTranslation = () => {
  const { t, language, setLanguage, autoDetectLanguage, availableLanguages } = useLanguage();
  
  return {
    t,
    language,
    setLanguage,
    autoDetectLanguage,
    availableLanguages
  };
};

export default useTranslation;
