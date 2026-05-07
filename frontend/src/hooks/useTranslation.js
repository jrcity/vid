import { useLanguage } from '../context/LanguageContext';

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
