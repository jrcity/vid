import React, { useState, memo, useCallback } from 'react';
import useTranslation from '../hooks/useTranslation';

const LanguageSwitcher = memo(() => {  // ← ADD memo
  const { language, setLanguage, availableLanguages, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const handleLanguageChange = useCallback((langCode) => {
    setLanguage(langCode);
    setIsOpen(false);
  }, [setLanguage]);

  const toggleDropdown = useCallback(() => {
    setIsOpen(prev => !prev);
  }, []);

  const currentLanguage = availableLanguages.find(lang => lang.code === language);

  return (
    <div className="language-switcher" style={{ position: 'relative' }}>
      <button 
        onClick={toggleDropdown}
        aria-label={t('navbar.language')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          background: 'transparent',
          border: '1px solid #ddd',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        <span>{currentLanguage?.flag}</span>
        <span>{currentLanguage?.name}</span>
        <span>▼</span>
      </button>
      
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: '4px',
          background: 'white',
          border: '1px solid #ddd',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          zIndex: 1000,
          minWidth: '150px'
        }}>
          {availableLanguages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%',
                padding: '8px 12px',
                background: language === lang.code ? '#f0f0f0' : 'white',
                border: 'none',
                textAlign: 'left',
                cursor: 'pointer'
              }}
            >
              <span>{lang.flag}</span>
              <span>{lang.name}</span>
              <span style={{ fontSize: '12px', color: '#666' }}>{lang.nativeName}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
});

LanguageSwitcher.displayName = 'LanguageSwitcher';

export default LanguageSwitcher;
